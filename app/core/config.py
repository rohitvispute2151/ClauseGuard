from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ClauseGuard application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "clauseguard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_KEY: str = "clauseguard-test-key"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://clauseguard:clauseguard_secret@localhost:5433/clauseguard"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://clauseguard:clauseguard_secret@localhost:5433/clauseguard"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
