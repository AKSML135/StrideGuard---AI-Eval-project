"""Run every golden case through the sandboxed action agent.

For every case, this script:
  1. creates a fresh SQLite file;
  2. resets it;
  3. seeds the case's initial order;
  4. enables fault injection when requested;
  5. fixes now to the case timestamp;
  6. runs the agent;
  7. extracts retrieved IDs from the policy-search tool;
  8. saves tool calls and final database snapshot;
  9. records any exception without losing the batch.

Usage:
    uv run python scripts/run_agent_experiment.py \\
      --dataset evals/datasets/dev.jsonl \\
      --output artifacts/runs/agent_v1.jsonl
"""

import argparse
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from strideguard.agent import run_agent
from strideguard.datasets import load_cases
from strideguard.db import OrderRepository
from strideguard.llm_factory import build_chat_model
from strideguard.models import Order, RunRecord
from strideguard.settings import get_settings
from strideguard.support import PROMPT_VERSION


def main() -> None:
    parser = argparse.ArgumentParser()
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
            started_at = datetime.now(UTC)
            started = time.perf_counter()
            response = None
            tool_calls = []
            final_state: dict = {}
            error: str | None = None

            with tempfile.TemporaryDirectory() as tmp_dir:
                db_path = Path(tmp_dir) / f"{case.case_id}.sqlite"
                fail_updates = bool(
                    case.initial_state.get("simulate_tool_failure") == "update_address"
                )
                repository = OrderRepository(db_path, fail_updates=fail_updates)
                repository.reset()

                order_data = case.initial_state.get("order")
                if order_data:
                    repository.seed_order(Order.model_validate(order_data))

                case_now = case.initial_state.get("now")
                now_value = (
                    datetime.fromisoformat(case_now) if case_now else datetime.now(UTC)
                )

                try:
                    answer, tool_calls = run_agent(
                        question=case.user_input,
                        model=model,
                        repository=repository,
                        authenticated_user_id=case.authenticated_user_id,
                        now_provider=lambda: now_value,
                    )
                    response = answer
                except Exception as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"

                final_state = repository.snapshot()

            run = RunRecord(
                run_id=str(uuid4()),
                case_id=case.case_id,
                mode="agent",
                provider=settings.llm_provider,
                model=settings.selected_model,
                prompt_version=PROMPT_VERSION,
                knowledge_version="kb-v1",
                started_at=started_at,
                latency_ms=(time.perf_counter() - started) * 1000,
                response=response,
                tool_calls=tool_calls,
                final_state=final_state,
                error=error,
            )
            handle.write(run.model_dump_json() + "\n")
            status = "error" if run.error else "ok"
            print(f"[{index}/{len(cases)}] {case.case_id}: {status}")

    print(f"Wrote {len(cases)} agent runs to {args.output}")


if __name__ == "__main__":
    main()
