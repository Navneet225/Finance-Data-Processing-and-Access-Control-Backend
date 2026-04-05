import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_fd, _db_path = tempfile.mkstemp(suffix="_pytest_finance.db")
os.close(_fd)
TEST_DB_FILE = Path(_db_path)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE.as_posix()}"

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    try:
        TEST_DB_FILE.unlink(missing_ok=True)
    except OSError:
        pass
