from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "changeme"
    FAQ_CACHE_TTL_SECONDS: int = 3600

    API_URL: str = "changeme"
    ARIAPAY_API_URL: str = "changeme"

    OLLAMA_URL: str = "changeme"
    CHAT_MODEL: str = "changeme"
    EMBED_MODEL: str = "changeme"
    EMBED_DIM: int = 0
    FAQ_MATCH_THRESHOLD: float = 0.85

    QDRANT_URL: str = "changeme"
    QDRANT_COLLECTION: str = "changeme"

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"


settings = Settings()
