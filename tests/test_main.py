import pytest
from httpx import AsyncClient, ASGITransport

try:
    from main import app
except ImportError:
    import sys
    import os
    sys.path.insert(
        0, os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), '..')))
    from main import app

transport = ASGITransport(app=app, raise_app_exceptions=True)


@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(
            transport=transport,
            base_url="http://testserver") as client:
        response = await client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.asyncio
async def test_read_item():
    async with AsyncClient(
            transport=transport,
            base_url="http://testserver") as client:
        response = await client.get("/item/10?query_param=testquery")
    assert response.status_code == 200
    assert response.json() == {
        "item_id": 10,
        "query_param": "testquery"
    }


@pytest.mark.asyncio
async def test_read_item_no_query():
    async with AsyncClient(
            transport=transport,
            base_url="http://testserver") as client:
        response = await client.get("/item/25")
    assert response.status_code == 200
    assert response.json() == {"item_id": 25, "query_param": None}
