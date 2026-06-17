from pathlib import Path

import json

import pytest

from _core.parser.postman import parse_postman
from _core.parser.detect import detect_format

FIXTURES = Path(__file__).parent / "fixtures"


class TestDetectPostman:
    def test_detect_postman_format(self):
        assert detect_format(FIXTURES / "sample.postman.json") == "postman"

    def test_detect_from_schema_without_postman_id(self):
        assert detect_format(FIXTURES / "nested.postman.json") == "postman"


class TestPostmanParser:
    def test_parse_endpoints_count(self):
        endpoints = parse_postman(FIXTURES / "sample.postman.json")
        assert len(endpoints) == 2

    def test_parse_get_request(self):
        endpoints = parse_postman(FIXTURES / "sample.postman.json")
        get_ep = [e for e in endpoints if e.method == "GET"][0]
        assert get_ep.path == "/api/users"
        assert len(get_ep.parameters) == 2
        assert get_ep.auth_required is False

    def test_keeps_relative_raw_url_path_without_dropping_first_segment(self, tmp_path):
        collection = {
            "info": {
                "name": "Relative URLs",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [
                {
                    "name": "Relative path",
                    "request": {"method": "GET", "url": "api/users"},
                },
                {
                    "name": "Host path",
                    "request": {
                        "method": "GET",
                        "url": "api.example.com/v1/users",
                    },
                },
                {
                    "name": "Host only",
                    "request": {"method": "GET", "url": "api.example.com"},
                },
            ],
        }
        fixture = tmp_path / "relative.postman.json"
        fixture.write_text(json.dumps(collection), encoding="utf-8")

        endpoints = parse_postman(fixture)

        assert [endpoint.path for endpoint in endpoints] == [
            "/api/users",
            "/v1/users",
            "/",
        ]

    def test_parses_string_request_as_get_url(self, tmp_path):
        collection = {
            "info": {
                "name": "String request",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [{"name": "List Users", "request": "https://api.example.com/users"}],
        }
        fixture = tmp_path / "string-request.postman.json"
        fixture.write_text(json.dumps(collection), encoding="utf-8")

        endpoint = parse_postman(fixture)[0]

        assert endpoint.method == "GET"
        assert endpoint.path == "/users"
        assert endpoint.summary == "List Users"

    def test_rejects_invalid_collection_shape(self, tmp_path):
        fixture = tmp_path / "invalid.postman.json"
        fixture.write_text("[]", encoding="utf-8")

        with pytest.raises(ValueError, match="must be a mapping"):
            parse_postman(fixture)

    def test_rejects_invalid_collection_item_entry(self, tmp_path):
        collection = {
            "info": {
                "name": "Invalid item",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": ["not an item object"],
        }
        fixture = tmp_path / "invalid-item.postman.json"
        fixture.write_text(json.dumps(collection), encoding="utf-8")

        with pytest.raises(ValueError, match="item entries must be mappings"):
            parse_postman(fixture)

    def test_parse_post_with_auth(self):
        endpoints = parse_postman(FIXTURES / "sample.postman.json")
        post_ep = [e for e in endpoints if e.method == "POST"][0]
        assert post_ep.path == "/api/users"
        assert post_ep.request_body is not None
        assert post_ep.auth_required is True

    def test_infers_json_schema_from_raw_body(self):
        endpoints = parse_postman(FIXTURES / "sample.postman.json")
        post_ep = next(endpoint for endpoint in endpoints if endpoint.method == "POST")

        assert post_ep.request_body["type"] == "object"
        assert post_ep.request_body["properties"]["name"] == {
            "type": "string",
            "example": "test",
        }


class TestNestedPostmanParser:
    def test_uses_folder_tags_path_variables_and_custom_headers(self):
        endpoints = parse_postman(FIXTURES / "nested.postman.json")
        get_user = next(
            endpoint for endpoint in endpoints if endpoint.summary == "Get User"
        )

        assert get_user.tags == ["Users"]
        assert get_user.path == "/api/users/{userId}"
        assert get_user.description == "Returns one user."
        assert get_user.auth_required is False
        assert [(p.name, p.location, p.param_type) for p in get_user.parameters] == [
            ("expand", "query", "boolean"),
            ("userId", "path", "integer"),
            ("X-Tenant-ID", "header", "string"),
        ]
        assert (
            get_user.responses["200"]["schema"]["properties"]["id"]["type"] == "integer"
        )

    def test_inherits_collection_auth_and_vendor_json_content_type(self):
        endpoints = parse_postman(FIXTURES / "nested.postman.json")
        create = next(
            endpoint for endpoint in endpoints if endpoint.summary == "Create User"
        )

        assert create.tags == ["Users"]
        assert create.auth_required is True
        assert create.content_type == "application/vnd.example+json"
        assert create.request_body_required is True
        assert create.request_body["properties"]["active"]["type"] == "boolean"

    def test_parses_form_data_file_upload(self):
        endpoints = parse_postman(FIXTURES / "nested.postman.json")
        upload = next(
            endpoint for endpoint in endpoints if endpoint.summary == "Upload Avatar"
        )

        assert upload.tags == ["Uploads"]
        assert upload.auth_required is True
        assert upload.content_type == "multipart/form-data"
        assert upload.request_body["properties"]["file"] == {
            "type": "string",
            "format": "binary",
        }

    def test_parses_urlencoded_and_graphql_bodies(self, tmp_path):
        collection = {
            "info": {
                "name": "Body modes",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [
                {
                    "name": "Login",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/login",
                        "body": {
                            "mode": "urlencoded",
                            "urlencoded": [
                                {"key": "username", "value": "kerwin"},
                                {"key": "remember", "value": "true"},
                            ],
                        },
                    },
                },
                {
                    "name": "GraphQL",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/graphql",
                        "body": {
                            "mode": "graphql",
                            "graphql": {
                                "query": "query User($id: ID!) { user(id: $id) { id } }",
                                "variables": '{"id": 42}',
                            },
                        },
                    },
                },
            ],
        }
        fixture = tmp_path / "body-modes.postman.json"
        fixture.write_text(json.dumps(collection), encoding="utf-8")

        endpoints = parse_postman(fixture)
        login = next(endpoint for endpoint in endpoints if endpoint.summary == "Login")
        graphql = next(
            endpoint for endpoint in endpoints if endpoint.summary == "GraphQL"
        )

        assert login.content_type == "application/x-www-form-urlencoded"
        assert login.request_body["properties"]["remember"]["type"] == "string"
        assert graphql.content_type == "application/json"
        assert (
            graphql.request_body["properties"]["variables"]["properties"]["id"]["type"]
            == "integer"
        )
