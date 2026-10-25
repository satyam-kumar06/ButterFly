import asyncio

import httpx

from apps.api.main import app


def test_health_reports_foundation_not_a_live_engine():
    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request())
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "phase": "0", "mode": "foundation"}
