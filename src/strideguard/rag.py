from typing import Any

from strideguard.retrieval import retrieve
from strideguard.support import SupportAnswer, answer_with_context


# NOTE: `format_retrieved_context` is called by `answer_with_rag` below but its
# body was not printed in the guide. It is reconstructed to match the same
# "[doc_id]\ntext" format used everywhere else in the project (see
# knowledge.py's `_format_section` and the SYSTEM_PROMPT instruction to "cite
# source IDs exactly as they appear in square brackets in the context").
def format_retrieved_context(documents: list[Any]) -> str:
    parts = []
    for document in documents:
        doc_id = document.metadata["doc_id"]
        parts.append(f"[{doc_id}]\n{document.page_content}")
    return "\n\n".join(parts)


def answer_with_rag(
    *,
    question: str,
    model: Any,
    store: Any | None = None,
    k: int = 4,
    authoritative_facts: str = "",
) -> tuple[SupportAnswer, list[str]]:
    documents = retrieve(question, k=k, store=store)
    doc_ids = [str(document.metadata["doc_id"]) for document in documents]
    context = format_retrieved_context(documents)
    if authoritative_facts:
        context += f"\n\n[authoritative_case_facts]\n{authoritative_facts}"
    answer = answer_with_context(
        question=question,
        context=context,
        model=model,
    )
    return answer, doc_ids


# Authoritative order facts are passed separately from retrieved policy so
# that a user claim does not replace database truth.
