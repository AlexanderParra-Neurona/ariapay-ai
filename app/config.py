from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "changeme"
    FAQ_CACHE_TTL_SECONDS: int = 3600

    API_URL: str = "changeme"
    ARIAPAY_API_URL: str = "changeme"

    LLM_PROVIDER: str = "ollama"

    OLLAMA_URL: str = "changeme"
    OLLAMA_CHAT_MODEL: str = "changeme"
    OLLAMA_EMBED_MODEL: str = "changeme"
    OLLAMA_EMBED_DIM: int = 0

    DEEPINFRA_API_TOKEN: str = "changeme"
    DEEPINFRA_CHAT_MODEL: str = "changeme"
    DEEPINFRA_EMBED_MODEL: str = "changeme"
    DEEPINFRA_EMBED_DIM: int = 0

    QDRANT_URL: str = "changeme"
    QDRANT_COLLECTION: str = "changeme"

    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_CANDIDATE_POOL: int = 20

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

    @property
    def CHAT_MODEL(self) -> str:
        return self.OLLAMA_CHAT_MODEL if self.LLM_PROVIDER == "ollama" else self.DEEPINFRA_CHAT_MODEL

    @property
    def EMBED_MODEL(self) -> str:
        return self.OLLAMA_EMBED_MODEL if self.LLM_PROVIDER == "ollama" else self.DEEPINFRA_EMBED_MODEL

    @property
    def EMBED_DIM(self) -> int:
        return self.OLLAMA_EMBED_DIM if self.LLM_PROVIDER == "ollama" else self.DEEPINFRA_EMBED_DIM


settings = Settings()
