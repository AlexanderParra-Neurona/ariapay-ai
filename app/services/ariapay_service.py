import httpx

from app.config import settings


class AriapayAuthError(Exception):
    pass


class AriapayAPIError(Exception):
    pass


async def get_me(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.ARIAPAY_API_URL}/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
    if resp.status_code == 401:
        raise AriapayAuthError("Missing or invalid access_token")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["result"]
