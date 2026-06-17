"""Endpoint-list validation helpers shared by CLI scripts."""

from _core.parser.base import ApiEndpoint


class EndpointListError(ValueError):
    """Raised when an endpoint list is structurally valid but unusable."""


def validate_endpoint_list(endpoints: list[ApiEndpoint]) -> None:
    """Ensure endpoint lists are non-empty and have unique METHOD + path keys."""
    if not endpoints:
        raise EndpointListError("endpoints JSON must contain at least one endpoint")

    seen: set[tuple[str, str]] = set()
    for endpoint in endpoints:
        key = (endpoint.method, endpoint.path)
        if key in seen:
            raise EndpointListError(
                f"duplicate endpoint: {endpoint.method} {endpoint.path}"
            )
        seen.add(key)
