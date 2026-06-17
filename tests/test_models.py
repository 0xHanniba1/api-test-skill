import pytest

from _core.parser.base import ApiEndpoint, Param


class TestParam:
    def test_create_required_param(self):
        p = Param(name="id", location="path", required=True, param_type="integer")
        assert p.name == "id"
        assert p.required is True
        assert p.description == ""
        assert p.constraints == {}

    def test_create_param_with_constraints(self):
        p = Param(
            name="age",
            location="query",
            required=False,
            param_type="integer",
            description="User age",
            constraints={"min": 0, "max": 150},
        )
        assert p.constraints["min"] == 0

    def test_mutable_defaults_are_isolated(self):
        first = Param(name="a", location="query")
        second = Param(name="b", location="query")

        first.constraints["minimum"] = 1

        assert second.constraints == {}

    def test_normalizes_name_and_type(self):
        param = Param(name=" page ", location="query", param_type=" Integer ")

        assert param.name == "page"
        assert param.param_type == "integer"

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="parameter name"):
            Param(name=" ", location="query")

    def test_normalizes_location(self):
        param = Param(name="tenant", location=" Header ")

        assert param.location == "header"

    def test_rejects_invalid_location(self):
        with pytest.raises(ValueError, match="parameter location"):
            Param(name="bad", location="body")

    def test_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="parameter type"):
            Param(name="bad", location="query", param_type="uuid")


class TestApiEndpoint:
    def test_create_minimal_endpoint(self):
        ep = ApiEndpoint(
            method="GET",
            path="/api/users",
            summary="List users",
            parameters=[],
            request_body=None,
            responses={"200": {"description": "Success"}},
            auth_required=False,
            tags=["users"],
        )
        assert ep.method == "GET"
        assert ep.content_type == "application/json"

    def test_create_post_endpoint_with_body(self):
        ep = ApiEndpoint(
            method="POST",
            path="/api/users",
            summary="Create user",
            parameters=[],
            request_body={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["name", "email"],
            },
            responses={"201": {"description": "Created"}},
            auth_required=True,
            tags=["users"],
        )
        assert ep.request_body is not None
        assert ep.auth_required is True

    def test_endpoint_serialization_roundtrip(self):
        ep = ApiEndpoint(
            method="DELETE",
            path="/api/users/{id}",
            summary="Delete user",
            parameters=[
                Param(name="id", location="path", required=True, param_type="integer")
            ],
            request_body=None,
            responses={"204": {"description": "Deleted"}},
            auth_required=True,
            tags=["users"],
        )
        data = ep.model_dump()
        ep2 = ApiEndpoint(**data)
        assert ep2.path == "/api/users/{id}"
        assert len(ep2.parameters) == 1

    def test_normalizes_method_path_and_content_types(self):
        endpoint = ApiEndpoint(
            method=" post ",
            path=" users ",
            content_types=[
                " Multipart/Form-Data ",
                "application/json; charset=utf-8",
                "multipart/form-data",
            ],
        )

        assert endpoint.method == "POST"
        assert endpoint.path == "/users"
        assert endpoint.content_type == "multipart/form-data"
        assert endpoint.content_types == ["multipart/form-data", "application/json"]

    def test_rejects_invalid_method(self):
        with pytest.raises(ValueError, match="HTTP method"):
            ApiEndpoint(method="FETCH", path="/users")

    def test_rejects_whitespace_inside_path(self):
        with pytest.raises(ValueError, match="path must not contain whitespace"):
            ApiEndpoint(method="GET", path="/bad path")

    def test_defaults_are_isolated(self):
        first = ApiEndpoint(method="GET", path="/first")
        second = ApiEndpoint(method="GET", path="/second")

        first.tags.append("first")
        first.responses["200"] = {"description": "ok"}

        assert second.tags == []
        assert second.responses == {}
