from typing import Any

from strideguard.models import SupportAnswer
from strideguard.support import answer_with_context


class FakeStructuredModel:
    def __init__(self, response: Any):
        self.response = response
        self.messages: list[Any] | None = None

    def invoke(self, messages: list[Any]) -> Any:
        self.messages = messages
        return self.response


class FakeChatModel:
    def __init__(self, response: Any):
        self.structured = FakeStructuredModel(response)
        self.requested_schema: type[Any] | None = None

    def with_structured_output(self, schema: type[Any]) -> FakeStructuredModel:
        self.requested_schema = schema
        return self.structured


def test_support_pipeline_without_api_calls() -> None:
    expected = SupportAnswer(
        decision="ELIGIBLE",
        answer="The order is eligible.",
        cited_doc_ids=["shipping_v1#address-change-window"],
    )
    model = FakeChatModel(expected)

    actual = answer_with_context(
        question="Can I change it?",
        context=(
            "[shipping_v1#address-change-window] "
            "Eligible through 60 minutes."
        ),
        model=model,
    )

    assert actual == expected
    assert model.requested_schema is SupportAnswer
    assert "Can I change it?" in model.structured.messages[1][1]
