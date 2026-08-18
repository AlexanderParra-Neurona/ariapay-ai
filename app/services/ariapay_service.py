import httpx

from app.config import settings

PLATFORM_HEADERS = {"X-Platform": "android", "X-App-Version": "1.0.0"}


class AriapayAuthError(Exception):
    pass


class AriapayAPIError(Exception):
    pass


async def get_me(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.ARIAPAY_API_URL}/api/v1/users/me",
            headers={**PLATFORM_HEADERS, "Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
    if resp.status_code == 401:
        raise AriapayAuthError("Missing or invalid access_token")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]


async def login(phone_number: str, country_code: str, password: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}/api/v1/login",
            json={"phone_number": phone_number, "country_code": country_code, "password": password},
            headers=PLATFORM_HEADERS,
            timeout=30,
        )
    if resp.status_code == 401:
        raise AriapayAuthError("Wrong phone number or password")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]["passcode_token"]


async def verify_passcode(token: str, passcode: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}/api/v1/passcode/verify",
            json={"passcode": passcode},
            headers={**PLATFORM_HEADERS, "Authorization": f"Bearer {token}"},
            timeout=30,
        )
    if resp.status_code == 401:
        raise AriapayAuthError("Wrong passcode or invalid token")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["token"]
