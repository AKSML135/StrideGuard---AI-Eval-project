"""
Centralized, typed configuration for StrideGuard.

Every other module (llm_factory.py, knowledge.py, rag.py, experiment.py,
observability.py, ...) reads configuration through a `Settings` instance
rather than calling `os.getenv` directly. This keeps provider branching,
paths, and feature flags in one place.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Provider selection -------------------------------------------------
    llm_provider: str = Field(default="groq")
    groq_api_key: str | None = Field(default=None)
    gemini_api_key: str | None = Field(default=None)
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    gemini_model: str = Field(default="gemini-2.5-flash")
    llm_temperature: float = Field(default=0.0)

    # --- Paths ---------------------------------------------------------------
    project_root: Path = Field(default=Path("."))
    qdrant_path: Path = Field(default=Path(".local/qdrant"))
    qdrant_collection: str = Field(default="strideguard_policies")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2"
    )

    # --- Observability (Phoenix / OpenInference) ------------------------------
    enable_phoenix: bool = Field(default=False)
    phoenix_collector_endpoint: str = Field(
        default="http://localhost:6006"
    )
    phoenix_project: str = Field(default="strideguard-evals")

    @model_validator(mode="after")
    def _resolve_paths(self) -> "Settings":
        # Normalize relative paths against project_root so callers can treat
        # qdrant_path / project_root as ready-to-use, absolute-ish paths
        # regardless of the current working directory.
        object.__setattr__(self, "project_root", self.project_root.resolve())
        if not self.qdrant_path.is_absolute():
            object.__setattr__(
                self, "qdrant_path", (self.project_root / self.qdrant_path).resolve()
            )
        return self

    @property
    def selected_model(self) -> str:
        """The model name for whichever provider is currently selected."""
        if self.llm_provider == "groq":
            return self.groq_model
        if self.llm_provider == "gemini":
            return self.gemini_model
        raise ValueError(f"Unsupported provider: {self.llm_provider}")

    def require_selected_api_key(self) -> str:
        """
        Return the API key for the selected provider, or raise a clear
        error early rather than letting the provider SDK fail with an
        opaque auth error later.
        """
        if self.llm_provider == "groq":
            key = self.groq_api_key
            key_name = "GROQ_API_KEY"
        elif self.llm_provider == "gemini":
            key = self.gemini_api_key
            key_name = "GEMINI_API_KEY"
        else:
            raise ValueError(f"Unsupported provider: {self.llm_provider}")

        if not key:
            raise ValueError(
                f"{key_name} is not set. Put it in your .env file for "
                f"LLM_PROVIDER={self.llm_provider}."
            )
        return key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached singleton accessor. Application code should call this instead
    of constructing Settings() repeatedly, so a single process shares one
    resolved configuration. Tests that need a fresh instance (e.g. after
    monkeypatching env vars) should construct Settings() directly, or call
    get_settings.cache_clear() first.
    """
    return Settings()