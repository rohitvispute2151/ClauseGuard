from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ClauseGuard application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "clauseguard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # "development" | "production"

    # Security
    # When set, every /api/v1 route except /health requires a matching `X-API-Key` header.
    # Leave empty to disable (local development).
    API_KEY: str = ""
    # Comma-separated list of browser origins allowed by CORS, e.g. "https://clauseguard.vercel.app".
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    # Number of trusted reverse proxies in front of the API. When > 0 the client IP is read from
    # `X-Forwarded-For` (counting from the right). Keep 0 when the API is reachable directly,
    # otherwise clients can spoof their IP and dodge rate limits.
    TRUSTED_PROXY_HOPS: int = 0

    # Per-IP quotas on the endpoints that spend LLM tokens (fixed window).
    QUOTA_ENABLED: bool = True
    QUOTA_WINDOW_S: int = 3600
    QUOTA_UPLOADS: int = 5
    QUOTA_EXTRACTIONS: int = 10
    QUOTA_QUESTIONS: int = 40

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://clauseguard:clauseguard_secret@localhost:5434/clauseguard"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://clauseguard:clauseguard_secret@localhost:5434/clauseguard"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Primary LLM Provider: Google Gemini via Google AI Studio (FreeLLM.net)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_ID: str = "gemini-flash-lite-latest"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai"

    # Fallback LLM Provider: Groq (FreeLLM.net)
    GROQ_API_KEY: str = ""
    GROQ_MODEL_ID: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Embeddings
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # Resilience & Limits
    LLM_MAX_RETRIES: int = 3
    LLM_BASE_DELAY_S: float = 1.0
    LLM_MAX_DELAY_S: float = 15.0
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_S: float = 30.0
    RATE_LIMIT_TOKENS: int = 100
    RATE_LIMIT_REFILL_RATE: float = 10.0

    # Pipeline
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    CONTEXT_TOKEN_BUDGET: int = 6000
    RETRIEVAL_TOP_K: int = 5
    EXTRACTION_CONCURRENCY_CAP: int = 4
    MAX_REPAIR_ATTEMPTS: int = 2
    CITATION_SIMILARITY_THRESHOLD: float = 0.80

    # Observability
    ENABLE_METRICS: bool = True
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        if self.is_production and (not self.cors_origins_list or "*" in self.cors_origins_list):
            raise ValueError("CORS_ORIGINS must list explicit origins (no '*') when ENVIRONMENT=production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
