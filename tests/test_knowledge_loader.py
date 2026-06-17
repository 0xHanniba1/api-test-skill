import pytest

from _core.knowledge_loader import load_skill_content, select_skills
from _core.parser.base import ApiEndpoint, Param


def _make_endpoint(**overrides) -> ApiEndpoint:
    defaults = dict(
        method="GET",
        path="/api/test",
        summary="Test",
        parameters=[],
        request_body=None,
        responses={"200": {"description": "OK"}},
        auth_required=False,
        tags=[],
        content_type="application/json",
    )
    defaults.update(overrides)
    return ApiEndpoint(**defaults)


class TestSelectSkills:
    def test_always_includes_base(self):
        ep = _make_endpoint()
        skills = select_skills(ep, depth="quick")
        assert "base.md" in skills

    def test_quick_with_params_includes_param_validation(self):
        ep = _make_endpoint(
            parameters=[Param(name="q", location="query", required=False, param_type="string")]
        )
        skills = select_skills(ep, depth="quick")
        assert "param-validation.md" in skills

    def test_full_includes_auth_and_idempotency(self):
        ep = _make_endpoint()
        skills = select_skills(ep, depth="full")
        assert "auth-testing.md" in skills
        assert "idempotency.md" in skills

    def test_quick_auth_required_includes_auth_testing(self):
        ep = _make_endpoint(auth_required=True)
        skills = select_skills(ep, depth="quick")
        assert "auth-testing.md" in skills

    def test_pagination_detected(self):
        ep = _make_endpoint(
            parameters=[
                Param(name="page", location="query", required=False, param_type="integer"),
                Param(name="size", location="query", required=False, param_type="integer"),
            ]
        )
        skills = select_skills(ep, depth="quick")
        assert "pagination.md" in skills

    def test_file_upload_detected(self):
        ep = _make_endpoint(content_type="multipart/form-data")
        skills = select_skills(ep, depth="quick")
        assert "file-upload.md" in skills

    def test_file_upload_detected_from_secondary_content_type(self):
        ep = _make_endpoint(content_types=["application/json", "multipart/form-data"])
        skills = select_skills(ep, depth="quick")
        assert "file-upload.md" in skills


class TestLoadSkillContent:
    def test_load_base_skill(self):
        content = load_skill_content(["base.md"])
        assert len(content) > 0
        assert "测试" in content or "test" in content.lower()

    def test_missing_skill_fails_explicitly(self):
        with pytest.raises(ValueError, match="Unknown knowledge module"):
            load_skill_content(["missing.md"])

    def test_rejects_path_escape(self):
        with pytest.raises(ValueError, match="Unknown knowledge module"):
            load_skill_content(["../README.md"])
