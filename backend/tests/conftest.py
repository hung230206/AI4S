import os
from pathlib import Path
from urllib.parse import urlparse

# Set environment before importing the application. Never use the demo DB for tests.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://fintech_demo:fintech_demo_local_only@127.0.0.1:5434/insurance_payment_test")
if not urlparse(os.environ["DATABASE_URL"]).path.endswith("_test"):
    raise RuntimeError("Destructive tests require a database name ending _test")
os.environ["PROVIDER_WORKER_ENABLED"] = "false"
# Tests never consume a developer's real Gemini quota. Provider calls are mocked.
os.environ["GEMINI_ENABLED"] = "false"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.db import engine, SessionLocal
from app.main import app
from app.models import Base
from app.seed import seed


@pytest.fixture(scope="session", autouse=True)
def migrate():
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "migrations"))
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def clean_database(migrate):
    names = ",".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {names} CASCADE"))
    with SessionLocal.begin() as db:
        seed(db)


class ConsentingTestClient(TestClient):
    def request(self, method, url, **kwargs):
        if kwargs.get("files"):
            purpose = "documents" if str(url).endswith("/documents") else "invoice-ocr" if str(url).endswith("/invoice-imports") else "claim-attachments"
            kwargs["headers"] = {"X-Processing-Consent": f"{purpose}:files-2026-10-19-v1", **(kwargs.get("headers") or {})}
        return super().request(method, url, **kwargs)


@pytest.fixture
def client():
    with ConsentingTestClient(app) as value:
        yield value


@pytest.fixture
def student_headers(client):
    result = client.post("/api/v1/demo/session", json={"role": "STUDENT"})
    assert result.status_code == 200, result.text
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


@pytest.fixture
def operator_headers(client):
    from app.config import settings
    result = client.post("/api/v1/demo/session", json={"role": "OPERATOR", "operator_code": settings.demo_operator_code})
    return {"Authorization": f"Bearer {result.json()['access_token']}"}
