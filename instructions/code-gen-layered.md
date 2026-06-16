# Layered code generation

Generate a five-layer API automation project. Endpoints are grouped by tag
(from `plan_files.py --arch layered`); each tag gets one file per layer.

```
out/
├── base/            # HttpClient + env config (fixed templates below)
│   ├── config.py
│   └── client.py
├── data/{tag}.yaml  # test data, separated from code
├── api/{tag}_api.py # one class per tag, one method per endpoint
├── services/{tag}_flow.py  # CRUD orchestration across endpoints
├── tests/
│   ├── conftest.py  # fixtures: client + per-tag api instances
│   └── test_{tag}.py
├── Jenkinsfile
└── requirements.txt
```

Use the filenames from the plan exactly.

## base/config.py (verbatim)
```python
import os


def base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8080")


def auth_token() -> str:
    return os.getenv("API_TOKEN", "")
```

## base/client.py (verbatim)
```python
import requests

from base.config import auth_token, base_url


class HttpClient:
    def __init__(self):
        self.base = base_url()
        self.session = requests.Session()
        token = auth_token()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _url(self, path: str) -> str:
        return f"{self.base}{path}"

    def get(self, path, **kw):
        return self.session.get(self._url(path), **kw)

    def post(self, path, **kw):
        return self.session.post(self._url(path), **kw)

    def put(self, path, **kw):
        return self.session.put(self._url(path), **kw)

    def patch(self, path, **kw):
        return self.session.patch(self._url(path), **kw)

    def delete(self, path, **kw):
        return self.session.delete(self._url(path), **kw)
```

## data/{tag}.yaml
Group by operation, then by scenario. Each scenario carries `body` (POST/PUT/PATCH),
`params` (GET query), `path_params`, and `expected_status`.
```yaml
create_pet:
  valid:
    body: {name: "doggie"}
    expected_status: 201
  missing_name:
    body: {}
    expected_status: 400
get_pet:
  valid:
    path_params: {pet_id: 1}
    expected_status: 200
  not_found:
    path_params: {pet_id: 99999}
    expected_status: 404
```

## api/{tag}_api.py
One class `{Tag}Api`, one method per endpoint (`snake_case`). Path params are
method args; body is `body: dict`; query is `params: dict`. The constructor takes
an `HttpClient`. Methods only send the request and return the response — no
assertions, no data processing.
```python
from base.client import HttpClient


class PetsApi:
    def __init__(self, client: HttpClient):
        self.client = client

    def create_pet(self, body: dict):
        return self.client.post("/pets", json=body)

    def get_pet(self, pet_id: int):
        return self.client.get(f"/pets/{pet_id}")
```

## services/{tag}_flow.py
One class `{Tag}Flow` taking the Api instance. Infer realistic CRUD flows from
the available endpoints (e.g. `create_and_get`, `full_lifecycle`). Chain steps
via response data. Never call endpoints that do not exist.

## tests/conftest.py (template)
```python
import pytest

from base.client import HttpClient
from api.pets_api import PetsApi  # one import + fixture per tag


@pytest.fixture
def client():
    return HttpClient()


@pytest.fixture
def pets_api(client):
    return PetsApi(client)
```

## tests/test_{tag}.py
One class per operation; load data from YAML, do not hardcode it; docstrings carry
the TC-XXX ids; assert `resp.status_code == d["expected_status"]`.
```python
import yaml
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_data(resource: str) -> dict:
    with open(DATA_DIR / f"{resource}.yaml") as f:
        return yaml.safe_load(f)


class TestCreatePet:
    """POST /pets"""
    data = load_data("pets")["create_pet"]

    def test_success(self, pets_api):
        """TC-002: 创建成功"""
        d = self.data["valid"]
        resp = pets_api.create_pet(d["body"])
        assert resp.status_code == d["expected_status"]
```

## requirements.txt (verbatim)
```
pytest
requests
pyyaml
```

## Jenkinsfile (template)
```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: 'Target environment')
    }
    environment {
        API_TOKEN = credentials('api-token')
    }
    stages {
        stage('Install') {
            steps { sh 'pip install -r requirements.txt' }
        }
        stage('Test') {
            steps {
                sh 'API_BASE_URL=$API_BASE_URL pytest -v --junitxml=reports/result.xml'
            }
        }
    }
    post {
        always { junit 'reports/*.xml' }
    }
}
```

After writing everything, run `python scripts/validate.py <out>` (syntax + YAML)
and fix errors. The default check is dependency-free and safe to trust.

`--collect` is opt-in and has two caveats for layered output: it imports the
test modules, so it needs `requests`/`pyyaml` installed **and** must run from the
output dir so cross-layer imports (`from base.client import ...`) resolve. A
collect error about a missing `base`/`api`/`requests` module means env/run
location, not broken code — don't "fix" correct code to chase it.
