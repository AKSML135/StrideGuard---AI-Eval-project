"""Run every golden case through the baseline or RAG pipeline and freeze results.

Usage:
    uv run python scripts/run_experiment.py \\
      --mode baseline \\
      --dataset evals/datasets/dev.jsonl \\
      --output artifacts/runs/baseline_v1.jsonl

    uv run python scripts/run_experiment.py \\
      --mode rag \\
      --dataset evals/datasets/dev.jsonl \\
      --output artifacts/runs/rag_v1.jsonl
"""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from strideguard.datasets import load_cases
from strideguard.experiment import run_case
from strideguard.knowledge import load_full_context
from strideguard.llm_factory import build_chat_model
from strideguard.models import RunRecord
from strideguard.rag import answer_with_rag
from strideguard.settings import get_settings
from strideguard.support import PROMPT_VERSION


def run_rag_case(case, model, settings, store=None) -> RunRecord:
    started_at = datetime.now(UTC)
    started = time.perf_counter()
    response = None
    retrieved_doc_ids: list[str] = []
    error: str | None = None

    try:
        answer, retrieved_doc_ids = answer_with_rag(
            question=case.user_input,
            model=model,
            store=store,
            authoritative_facts=json.dumps(case.initial_state, indent=2),
        )
        response = answer
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    return RunRecord(
        run_id=str(uuid4()),
        case_id=case.case_id,
        mode="rag",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "rag"], required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    model = build_chat_model(settings)
    cases = load_cases(args.dataset)
    if args.limit:
        cases = cases[: args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for index, case in enumerate(cases, start=1):
            if args.mode == "baseline":
                run = run_case(case=case, mode="baseline", model=model, settings=settings)
            else:
                run = run_rag_case(case, model, settings)

            handle.write(run.model_dump_json() + "\n")
            status = "error" if run.error else "ok"
            print(
                f"[{index}/{len(cases)}] {case.case_id}: {status} "
                f"({run.latency_ms:.0f} ms)"
            )

    print(f"Wrote {len(cases)} runs to {args.output}")


if __name__ == "__main__":
    main()
