import os

import pytest

from strideguard.llm_factory import build_chat_model
from strideguard.models import SupportAnswer
from strideguard.settings import Settings
from strideguard.support import answer_with_context


@pytest.mark.integration
def test_selected_live_model_returns_structured_output() -> None:
    provider = os.getenv("LLM_PROVIDER", "groq")
    key_name = "GROQ_API_KEY" if provider == "groq" else "GEMINI_API_KEY"
    if not os.getenv(key_name):
        pytest.skip(f"{key_name} is not set")

    answer = answer_with_context(
        question="Which shoe has maximum cushioning?",
        context="[products_v1#cloudpeak-max] CloudPeak Max has maximum cushioning.",
        model=build_chat_model(Settings()),
    )

    assert isinstance(answer, SupportAnswer)
    assert answer.answer.strip()
