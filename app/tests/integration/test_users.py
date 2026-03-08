import pytest


@pytest.mark.asyncio
async def test_users_requires_auth(client):
    response = await client.get("/api/v1/users/me")
    assert response.status_code in {401, 403}
