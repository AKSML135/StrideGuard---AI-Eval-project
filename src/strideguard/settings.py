"""Application settings.

NOTE: Unlike almost every other file in this repository, the guide never
prints `settings.py`'s contents anywhere in its 103 pages -- it only says
"Create src/strideguard/settings.py and src/strideguard/llm_factory.py" and
then shows llm_factory.py. Every field and method below was reconstructed
from how `Settings`/`get_settings` are actually used across the rest of the
guide (llm_factory.build_chat_model, retrieval.py, experiment.py, the CLI,
etc.) and from the keys listed in `.env.example`. Treat this file as a
best-effort implementation, not a verbatim transcription.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "groq"
    groq_api_key: str | None = None
    gemini_api_key: str | None = None

    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.5-flash"

    llm_temperature: float = 0

    project_root: Path = Path(".")

    qdrant_path: Path = Path(".local/qdrant")
    qdrant_collection: str = "strideguard_policies"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    enable_phoenix: bool = False
    phoenix_collector_endpoint: str = "http://localhost:6006"
    phoenix_project: str = "strideguard-evals"

    @property
    def selected_model(self) -> str:
        if self.llm_provider == "groq":
            return self.groq_model
        if self.llm_provider == "gemini":
            return self.gemini_model
        raise ValueError(f"Unsupported provider: {self.llm_provider}")

    def require_selected_api_key(self) -> str:
        if self.llm_provider == "groq":
            key = self.groq_api_key
        elif self.llm_provider == "gemini":
            key = self.gemini_api_key
        else:
            raise ValueError(f"Unsupported provider: {self.llm_provider}")

        if not key:
            raise ValueError(
                f"No API key set for provider {self.llm_provider!r}. "
                "Set it in your .env file."
            )
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()
