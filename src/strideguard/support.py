from typing import Any

from strideguard.models import SupportAnswer

PROMPT_VERSION = "support-v1"

SYSTEM_PROMPT = """You are StrideGuard, a support assistant for a fictional
running-shoe store.

Rules:
1. Use only the supplied product, policy, and order context.
2. Never invent policy. When policy is missing or ambiguous, say so and escalate.
3. Never expose or modify another user's order.
4. Do not claim an action succeeded unless a tool result confirms success.
5. Be concise: normally 2-5 sentences.
6. Cite source IDs exactly as they appear in square brackets in the context.

Return a structured response. The decision field must be a short code such as
ELIGIBLE, NOT_ELIGIBLE, NEEDS_ESCALATION, PRODUCT_RECOMMENDATION, or
INFORMATION_ONLY.
"""


def build_user_prompt(*, question: str, context: str) -> str:
    return f"""CONTEXT
{context}

CUSTOMER QUESTION
{question}

Answer using only the context. If the answer is not supported, choose
NEEDS_ESCALATION.
"""


def answer_with_context(
    *,
    question: str,
    context: str,
    model: Any,
) -> SupportAnswer:
    structured_model = model.with_structured_output(SupportAnswer)
    result = structured_model.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", build_user_prompt(question=question, context=context)),
        ]
    )
    if isinstance(result, SupportAnswer):
        return result
    return SupportAnswer.model_validate(result)
