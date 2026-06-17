"""Knowledge loader — selects and loads test knowledge modules based on endpoint characteristics."""

from pathlib import Path

from _core.parser.base import ApiEndpoint

# knowledge/ lives at the project root, two levels above scripts/_core/.
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"

PAGINATION_PARAM_NAMES = {"page", "size", "limit", "offset", "page_size", "per_page", "pagesize"}


def select_skills(endpoint: ApiEndpoint, depth: str) -> list[str]:
    """Select which skill files to load based on endpoint features and depth."""
    skills = ["base.md"]

    if endpoint.parameters:
        skills.append("param-validation.md")

    if _has_pagination_params(endpoint):
        skills.append("pagination.md")

    if _has_file_upload_content_type(endpoint):
        skills.append("file-upload.md")

    if endpoint.auth_required:
        skills.append("auth-testing.md")

    if depth == "full":
        for s in ("auth-testing.md", "idempotency.md"):
            if s not in skills:
                skills.append(s)

    return skills


def load_skill_content(skill_names: list[str]) -> str:
    """Load and concatenate the content of the given knowledge files."""
    parts = []
    for name in skill_names:
        path = _resolve_knowledge_path(name)
        parts.append(path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def _resolve_knowledge_path(name: str) -> Path:
    path = (KNOWLEDGE_DIR / name).resolve()
    if not path.is_relative_to(KNOWLEDGE_DIR.resolve()) or not path.is_file():
        raise ValueError(f"Unknown knowledge module: {name}")
    return path


def _has_pagination_params(endpoint: ApiEndpoint) -> bool:
    param_names = {p.name.lower() for p in endpoint.parameters}
    return bool(param_names & PAGINATION_PARAM_NAMES)


def _has_file_upload_content_type(endpoint: ApiEndpoint) -> bool:
    return "multipart/form-data" in {
        endpoint.content_type,
        *endpoint.content_types,
    }
