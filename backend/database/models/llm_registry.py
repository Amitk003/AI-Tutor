"""
LLM Registry SQLAlchemy Model.
Tracks configured open-source LLM models (Qwen 2.5 3B, Llama 3.2 3B), providers, context windows, and parameters.
"""

from typing import Any, Dict, Optional
from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class LLMRegistry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered open-source LLM configuration entity."""

    __tablename__ = "llm_registry"

    model_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Model identifier (e.g. qwen2.5:3b-instruct)",
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        default="ollama",
        nullable=False,
        doc="Inference provider (ollama, vllm, huggingface)",
    )
    context_window: Mapped[int] = mapped_column(
        Integer,
        default=32768,
        nullable=False,
        doc="Maximum supported context window token length",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Model active availability status",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is default system model",
    )
    parameters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Model parameters (temperature, top_p, repeat_penalty)",
    )

    def __repr__(self) -> str:
        return f"<LLMRegistry model='{self.model_name}' provider='{self.provider}' active={self.is_active}>"
