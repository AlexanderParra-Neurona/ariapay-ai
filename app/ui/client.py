import requests

from app.config import settings


def respond(message: str, history: list[dict], access_token: str) -> str:
    payload = {"question": message, "access_token": access_token or None}
    resp = requests.post(f"{settings.API_URL}/chat", json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    return f"`{data['category']}`\n\n{data['answer']}"


def login() -> tuple[str, str]:
    payload = {
        "phone_number": settings.LOGIN_PHONE_NUMBER,
        "country_code": settings.LOGIN_COUNTRY_CODE,
        "password": settings.LOGIN_PASSWORD,
        "passcode": settings.LOGIN_PASSCODE,
    }
    resp = requests.post(f"{settings.API_URL}/auth/login", json=payload, timeout=30)
    if not resp.ok:
        try:
            detail = resp.json().get("detail", "Login failed")
        except ValueError:
            detail = "Login failed"
        return "", detail
    return resp.json()["access_token"], "Login successful"
