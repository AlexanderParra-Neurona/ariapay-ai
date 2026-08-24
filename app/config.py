from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "changeme"
    FAQ_CACHE_TTL_SECONDS: int = 3600

    API_URL: str = "changeme"
    ARIAPAY_API_URL: str = "changeme"

    LLM_PROVIDER: str = "ollama"

    OLLAMA_URL: str = "changeme"
    CHAT_MODEL: str = "changeme"
    EMBED_MODEL: str = "changeme"
    EMBED_DIM: int = 0

    QDRANT_URL: str = "changeme"
    QDRANT_COLLECTION: str = "changeme"

    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_CANDIDATE_POOL: int = 20

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"


settings = Settings()
