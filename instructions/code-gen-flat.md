# Flat code generation

Generate pytest + requests code: one test file per endpoint, plus `conftest.py`.

## Rules
- Use the filenames from `plan_files.py` **exactly**.
- Organize with classes: `Test{Operation}`.
- One test method per case; the method docstring includes the case id (TC-XXX).
- Use the fixtures `base_url` and `auth_headers` from `conftest.py`.
- Read config from env: `API_BASE_URL`, `API_TOKEN`. Never hardcode URLs or tokens.
- Assert on `resp.status_code` and, where relevant, `resp.json()`.

## conftest.py (write verbatim)

```python
import os

import pytest


@pytest.fixture
def base_url():
    return os.getenv("API_BASE_URL", "http://localhost:8080")


@pytest.fixture
def auth_headers():
    token = os.getenv("API_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}
```

## Example test file (`test_post_pets.py`)

```python
import requests


class TestCreatePet:
    def test_create_success(self, base_url, auth_headers):
        """TC-002: 创建成功"""
        resp = requests.post(
            f"{base_url}/pets", json={"name": "doggie"}, headers=auth_headers
        )
        assert resp.status_code == 201

    def test_missing_name(self, base_url, auth_headers):
        """TC-003: 缺少 name"""
        resp = requests.post(f"{base_url}/pets", json={}, headers=auth_headers)
        assert resp.status_code == 400
```

After writing all files, run `python scripts/validate.py <out>` and fix any
reported errors before finishing. That covers syntax + YAML. To also verify the
tests import/collect, `pip install requests` first, then
`python scripts/validate.py <out> --collect`.
