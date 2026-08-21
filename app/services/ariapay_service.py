import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger("ariabot.ariapay_api")

PLATFORM_HEADERS = {"X-Platform": "android", "X-App-Version": "1.0.0"}


class AriapayAuthError(Exception):
    pass


class AriapayAPIError(Exception):
    pass


def _log_call(method: str, path: str, status_code: int, elapsed_ms: float) -> None:
    logger.info(
        "ariapay_api_call method=%s path=%s status=%s elapsed_ms=%.1f",
        method,
        path,
        status_code,
        elapsed_ms,
    )


async def get_me(access_token: str) -> dict:
    path = "/api/v1/users/me"
    start = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.ARIAPAY_API_URL}{path}",
            headers={**PLATFORM_HEADERS, "Authorization": f"Bearer {access_token}"},
            timeout=30,
        )
    _log_call("GET", path, resp.status_code, (time.monotonic() - start) * 1000)
    if resp.status_code == 401:
        raise AriapayAuthError("Missing or invalid access_token")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]


async def login(phone_number: str, country_code: str, password: str) -> str:
    path = "/api/v1/login"
    start = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}{path}",
            json={
                "phone_number": phone_number,
                "country_code": country_code,
                "password": password,
            },
            headers=PLATFORM_HEADERS,
            timeout=30,
        )
    _log_call("POST", path, resp.status_code, (time.monotonic() - start) * 1000)
    if resp.status_code == 401:
        raise AriapayAuthError("Wrong phone number or password")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["user"]["passcode_token"]


async def verify_passcode(token: str, passcode: str) -> dict:
    path = "/api/v1/passcode/verify"
    start = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.ARIAPAY_API_URL}{path}",
            json={"passcode": passcode},
            headers={**PLATFORM_HEADERS, "Authorization": f"Bearer {token}"},
            timeout=30,
        )
    _log_call("POST", path, resp.status_code, (time.monotonic() - start) * 1000)
    if resp.status_code == 401:
        raise AriapayAuthError("Wrong passcode or invalid token")
    if resp.status_code != 200:
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()["token"]
