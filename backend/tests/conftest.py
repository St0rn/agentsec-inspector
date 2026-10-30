from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Any

import httpx
import pytest

TEST_DATA_DIR = tempfile.mkdtemp(prefix="agentsec-tests-")
os.environ["AGENTSEC_DATA_DIR"] = TEST_DATA_DIR
os.environ["AGENTSEC_API_TOKEN"] = "test-token"  # noqa: S105 - isolated test credential

from agentsec.database import init_db  # noqa: E402
from agentsec.main import (  # noqa: E402
    app,  # noqa: E402
    seed_scenarios,  # noqa: E402
)

init_db()
seed_scenarios()


class APIClient:
    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 12345))
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as session:
                return await session.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("OPTIONS", path, **kwargs)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def project(client: APIClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "client_name": "Test Client",
            "engagement_name": "Authorised Test",
            "description": "Automated fixture",
            "authorized_scope": "Loopback laboratory only",
            "start_date": "2026-01-01",
            "end_date": "2026-01-02",
        },
    )
    assert response.status_code == 201
    return response.json()
