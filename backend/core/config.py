"""Centralized, environment-driven application configuration."""

from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration shared by the API, workers, and infrastructure clients."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Adaptive AI Learning Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-change-in-production-32bytes-min"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 120

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "learning_platform"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/learning_platform"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "study_chunks"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOAD_DIR: str = "backend/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 52_428_800
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".pptx", ".txt", ".md", ".html"]

    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-large"

    DEFAULT_LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "qwen2.5:3b-instruct"
    VLLM_BASE_URL: str = "http://localhost:8000/v1"
    LLM_REQUEST_TIMEOUT_SECONDS: float = 120.0

    CONFIDENCE_THRESHOLD: float = 0.35
    MAX_CONTEXT_TOKENS: int = 4096
    MAX_OUTPUT_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.2
    LLM_TOP_P: float = 0.9
    LLM_TOP_K: int = 40
    RERANK_WEIGHT_RERANKER: float = 0.5
    RERANK_WEIGHT_DENSE: float = 0.3
    RERANK_WEIGHT_SPARSE: float = 0.2

    WEAK_TOPIC_MASTERY_THRESHOLD: float = 0.40
    STRONG_TOPIC_MASTERY_THRESHOLD: float = 0.80
    REVISION_ATTEMPT_THRESHOLD: int = 3
    MAX_STUDENT_MEMORY_ITEMS: int = 50
    IRT_DEFAULT_ITEM_DIFFICULTY: float = 0.0
    IRT_DEFAULT_ITEM_DISCRIMINATION: float = 1.0
    IRT_LEARNING_RATE: float = 0.25
    BKT_PRIOR_P_L0: float = 0.10
    BKT_PROB_TRANSITION: float = 0.20
    BKT_PROB_GUESS: float = 0.25
    BKT_PROB_SLIP: float = 0.10
    SM2_MIN_EASE_FACTOR: float = 1.30
    SM2_INITIAL_EASE_FACTOR: float = 2.50
    PEDAGOGY_SOCRATIC_THETA_MIN: float = 0.50
    PEDAGOGY_SOCRATIC_MASTERY_MIN: float = 0.60
    PEDAGOGY_ANALOGY_THETA_MAX: float = -0.50
    PEDAGOGY_FEYNMAN_MASTERY_MAX: float = 0.30
    QUIZ_DEFAULT_QUESTION_COUNT: int = 5
    QUIZ_DIFFICULTY_MARGIN: float = 0.30
    QUIZ_MAX_GENERATION_RETRIES: int = 3

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "production"}:
            return False
        return value

    @model_validator(mode="after")
    def validate_production_secret(self):
        if self.APP_ENV.lower() == "production" and self.SECRET_KEY == "dev-secret-key-change-in-production-32bytes-min":
            raise ValueError("SECRET_KEY must be set to a unique value in production.")
        return self

    @property
    def MAX_UPLOAD_SIZE_MB(self) -> int:
        return self.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)


settings = Settings()
