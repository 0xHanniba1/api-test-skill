"""Shared primitives reused by the deterministic core modules.

This is a trimmed-down version of the original generator/common.py: it keeps
only what the pure modules (testcase_document, naming) need, and drops the
LLM-driven validate-and-repair orchestration — self-healing now belongs to the
host agent, not to this library.
"""

import keyword
import re


class GenerationError(RuntimeError):
    """Base error for generated artifact failures."""


def extract_fenced_content(response: str, language: str = "python") -> str:
    """Extract a fenced block, falling back to the full response."""
    pattern = rf"```{re.escape(language)}\s*\n(.*?)```"
    match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else response.strip()


def normalize_identifier(value: str, default: str = "default") -> str:
    """Normalize free-form text for Python identifiers and file stems."""
    normalized = re.sub(r"\W+", "_", value.casefold(), flags=re.UNICODE).strip("_")
    if not normalized:
        normalized = default
    if normalized[0].isdigit() or keyword.iskeyword(normalized):
        normalized = f"tag_{normalized}"
    if not normalized.isidentifier():
        return default
    return normalized
