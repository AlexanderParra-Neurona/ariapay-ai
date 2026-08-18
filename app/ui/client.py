import requests

from app.config import settings


def respond(message: str, history: list[dict], access_token: str) -> str:
    payload = {"question": message, "access_token": access_token or None}
    resp = requests.post(f"{settings.API_URL}/chat", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["answer"]
