from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://localhost:6379/0"
    FAQ_CACHE_TTL_SECONDS: int = 3600

    API_URL: str = "http://localhost:8000"
    ARIAPAY_API_URL: str = "https://api.ariapay.id"

    OLLAMA_URL: str = "http://localhost:11434"
    EMBED_MODEL: str = "nomic-embed-text"
    EMBED_DIM: int = 768
    FAQ_MATCH_THRESHOLD: float = 0.85


settings = Settings()
