"""Unified data models for parsed API documentation.

All parsers (Swagger, Postman, Markdown) convert their input
into these standard models for downstream processing.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

SUPPORTED_HTTP_METHODS = {
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
    "TRACE",
}
VALID_PARAM_LOCATIONS = {"query", "path", "header", "cookie"}
VALID_PARAM_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}


class Param(BaseModel):
    """A single API parameter (query, path, header, or cookie)."""

    name: str
    location: str  # query / path / header / cookie
    required: bool = False
    param_type: str = "string"  # string / integer / boolean / array / object
    description: str = ""
    constraints: dict[str, Any] = Field(default_factory=dict)
    example: Any | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("parameter name must not be empty")
        return normalized

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_PARAM_LOCATIONS:
            raise ValueError(
                "parameter location must be one of: "
                f"{', '.join(sorted(VALID_PARAM_LOCATIONS))}"
            )
        return normalized

    @field_validator("param_type")
    @classmethod
    def normalize_param_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_PARAM_TYPES:
            raise ValueError(
                "parameter type must be one of: "
                f"{', '.join(sorted(VALID_PARAM_TYPES))}"
            )
        return normalized


class ApiEndpoint(BaseModel):
    """A single API endpoint with all its metadata."""

    method: str  # GET / POST / PUT / DELETE / PATCH
    path: str  # /api/users/{id}
    summary: str = ""
    description: str = ""
    operation_id: str = ""
    parameters: list[Param] = Field(default_factory=list)
    request_body: dict[str, Any] | None = None
    request_body_required: bool = False
    responses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    auth_required: bool = False
    tags: list[str] = Field(default_factory=list)
    content_type: str = "application/json"
    content_types: list[str] = Field(default_factory=list)

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_HTTP_METHODS:
            raise ValueError(
                "HTTP method must be one of: "
                f"{', '.join(sorted(SUPPORTED_HTTP_METHODS))}"
            )
        return normalized

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            return "/"
        if re.search(r"\s", normalized):
            raise ValueError("endpoint path must not contain whitespace")
        return normalized if normalized.startswith("/") else f"/{normalized}"

    @model_validator(mode="after")
    def synchronize_content_types(self):
        content_types = _normalize_content_types(
            [*self.content_types, self.content_type]
            if self.content_types
            else [self.content_type]
        )
        self.content_types = content_types
        self.content_type = content_types[0]
        return self


def _normalize_content_types(values: list[str]) -> list[str]:
    normalized = []
    seen = set()
    for value in values:
        content_type = value.split(";", 1)[0].strip().lower()
        if not content_type or content_type in seen:
            continue
        normalized.append(content_type)
        seen.add(content_type)
    return normalized or ["application/json"]
