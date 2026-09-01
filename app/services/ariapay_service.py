import httpx

from app.config import settings
from app.constants import (
    ARIAPAY_LOGIN_PATH,
    ARIAPAY_ME_PATH,
    ARIAPAY_PASSCODE_VERIFY_PATH,
    ARIAPAY_PLATFORM_HEADERS,
    BEARER_PREFIX,
    HTTP_STATUS_OK,
    HTTP_STATUS_UNAUTHORIZED,
    HTTP_TIMEOUT_DEFAULT_SECONDS,
)


class AriapayAuthError(Exception):
    pass


class AriapayAPIError(Exception):
    pass


async def get_me(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.ARIAPAY_API_URL}{ARIAPAY_ME_PATH}",
            headers={
                **ARIAPAY_PLATFORM_HEADERS,
                "Authorization": f"{BEARER_PREFIX} {access_token}",
            },
            timeout=HTTP_TIMEOUT_DEFAULT_SECONDS,
        )
    if resp.status_code == HTTP_STATUS_UNAUTHORIZED:
        raise AriapayAuthError("Missing or invalid access_token")
    if resp.status_code != HTTP_STATUS_OK:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]


async def login(phone_number: str, country_code: str, password: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}{ARIAPAY_LOGIN_PATH}",
            json={
                "phone_number": phone_number,
                "country_code": country_code,
                "password": password,
            },
            headers=ARIAPAY_PLATFORM_HEADERS,
            timeout=HTTP_TIMEOUT_DEFAULT_SECONDS,
        )
    if resp.status_code == HTTP_STATUS_UNAUTHORIZED:
        raise AriapayAuthError("Wrong phone number or password")
    if resp.status_code != HTTP_STATUS_OK:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]["passcode_token"]


async def verify_passcode(token: str, passcode: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}{ARIAPAY_PASSCODE_VERIFY_PATH}",
            json={"passcode": passcode},
            headers={
                **ARIAPAY_PLATFORM_HEADERS,
                "Authorization": f"{BEARER_PREFIX} {token}",
            },
            timeout=HTTP_TIMEOUT_DEFAULT_SECONDS,
        )
    if resp.status_code == HTTP_STATUS_UNAUTHORIZED:
        raise AriapayAuthError("Wrong passcode or invalid token")
    if resp.status_code != HTTP_STATUS_OK:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["token"]
