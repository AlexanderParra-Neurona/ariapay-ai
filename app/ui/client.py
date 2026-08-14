import requests

from app.config import settings


def respond(message: str, history: list[dict]) -> str:
    resp = requests.post(f"{settings.API_URL}/chat", json={"question": message}, timeout=30)
    resp.raise_for_status()
    return resp.json()["answer"]
