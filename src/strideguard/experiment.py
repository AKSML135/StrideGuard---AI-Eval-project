import json
import time
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from strideguard.knowledge import load_full_context
from strideguard.models import GoldenCase, RunRecord
from strideguard.support import PROMPT_VERSION, answer_with_context


def run_case(
    *,
    case: GoldenCase,
    mode: Literal["baseline", "rag"],
    model: Any,
    settings: Any,
    store: Any | None = None,
) -> RunRecord:
    started_at = datetime.now(UTC)
    started = time.perf_counter()
    response = None
    retrieved_doc_ids: list[str] = []
    error: str | None = None

    try:
        context = load_full_context(settings.project_root)
        context += "\n\n[authoritative_case_facts]\n" + json.dumps(
            case.initial_state,
            indent=2,
        )
        response = answer_with_context(
            question=case.user_input,
            context=context,
            model=model,
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    return RunRecord(
        run_id=str(uuid4()),
        case_id=case.case_id,
        mode="baseline",
        provider=settings.llm_provider,
        model=settings.selected_model,
        prompt_version=PROMPT_VERSION,
        knowledge_version="kb-v1",
        started_at=started_at,
        latency_ms=(time.perf_counter() - started) * 1000,
        response=response,
        retrieved_doc_ids=retrieved_doc_ids,
        error=error,
    )
