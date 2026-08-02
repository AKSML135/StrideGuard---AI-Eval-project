from typing import Any

from strideguard.settings import Settings, get_settings


def build_chat_model(
    settings: Settings | None = None,
    *,
    temperature: float | None = None,
) -> Any:
    settings = settings or get_settings()
    api_key = settings.require_selected_api_key()
    chosen_temperature = (
        settings.llm_temperature if temperature is None else temperature
    )

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_model,
            api_key=api_key,
            temperature=chosen_temperature,
            max_retries=2,
            timeout=60,
        )

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=api_key,
            temperature=chosen_temperature,
            max_retries=2,
            timeout=60,
        )

    raise ValueError(f"Unsupported provider: {settings.llm_provider}")
