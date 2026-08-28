from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_llm_provider(default: str = "ollama") -> str:
    path = _REPO_ROOT / ".llm-provider"
    if path.exists():
        value = path.read_text().strip()
        if value:
            return value
    return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "changeme"
    FAQ_CACHE_TTL_SECONDS: int = 3600

    API_URL: str = "changeme"
    ARIAPAY_API_URL: str = "changeme"

    LOGIN_PHONE_NUMBER: str = "changeme"
    LOGIN_COUNTRY_CODE: str = "+62"
    LOGIN_PASSWORD: str = "changeme"
    LOGIN_PASSCODE: str = "changeme"

    LLM_PROVIDER: str = Field(default_factory=_read_llm_provider)

    OLLAMA_URL: str = "changeme"
    OLLAMA_CHAT_MODEL: str = "changeme"
    OLLAMA_EMBED_MODEL: str = "changeme"
    OLLAMA_EMBED_DIM: int = 4096

    DEEPINFRA_API_TOKEN: str = "changeme"
    DEEPINFRA_CHAT_MODEL: str = "changeme"
    DEEPINFRA_EMBED_MODEL: str = "changeme"
    DEEPINFRA_EMBED_DIM: int = 4096

    QDRANT_URL: str = "changeme"
    QDRANT_COLLECTION: str = "changeme"

    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_CANDIDATE_POOL: int = 20
    TRANSACTIONS_MAX_ALL: int = 200

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

    @property
    def CHAT_MODEL(self) -> str:
        return (
            f"ollama/{self.OLLAMA_CHAT_MODEL}"
            if self.LLM_PROVIDER == "ollama"
            else f"deepinfra/{self.DEEPINFRA_CHAT_MODEL}"
        )

    @property
    def EMBED_MODEL(self) -> str:
        return (
            f"ollama/{self.OLLAMA_EMBED_MODEL}"
            if self.LLM_PROVIDER == "ollama"
            else f"deepinfra/{self.DEEPINFRA_EMBED_MODEL}"
        )

    @property
    def EMBED_DIM(self) -> int:
        return (
            self.OLLAMA_EMBED_DIM
            if self.LLM_PROVIDER == "ollama"
            else self.DEEPINFRA_EMBED_DIM
        )


settings = Settings()
