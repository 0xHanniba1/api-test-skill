"""Auto-detect API documentation format."""

from pathlib import Path

import yaml

STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}


class FormatDetectionError(ValueError):
    """Raised when a structured-looking API document cannot be parsed."""


def detect_format(file_path: Path) -> str:
    """Detect the format of an API documentation file.

    Returns: 'swagger', 'postman', or 'markdown'.
    """
    text = file_path.read_text(encoding="utf-8")

    # Try YAML/JSON parsing
    is_structured_file = file_path.suffix.lower() in STRUCTURED_SUFFIXES
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            if "openapi" in data or "swagger" in data:
                return "swagger"
            if _is_postman_collection(data):
                return "postman"
    except yaml.YAMLError as error:
        if is_structured_file:
            raise FormatDetectionError(
                f"invalid YAML/JSON in structured API document: {error}"
            ) from error

    if is_structured_file:
        raise FormatDetectionError(
            "unsupported structured API document: expected OpenAPI/Swagger "
            "or Postman Collection"
        )

    return "markdown"


def _is_postman_collection(data: dict) -> bool:
    info = data.get("info", {})
    schema = info.get("schema", "") if isinstance(info, dict) else ""
    return bool(
        isinstance(info, dict)
        and ("_postman_id" in info or "schema.getpostman.com" in str(schema))
        and isinstance(data.get("item"), list)
    )
