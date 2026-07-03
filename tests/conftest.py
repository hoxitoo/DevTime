import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import DB  # noqa: E402


@pytest.fixture
def db():
    tmp = tempfile.mkdtemp()
    d = DB(os.path.join(tmp, "test.db"))
    yield d
    d.close()


@pytest.fixture
def client():
    """FastAPI TestClient на чистой временной БД."""
    from fastapi.testclient import TestClient
    from api.server import create_app
    tmp = tempfile.mkdtemp()
    app = create_app(os.path.join(tmp, "api.db"))
    with TestClient(app) as c:
        yield c
