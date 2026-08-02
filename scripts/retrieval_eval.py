"""Evaluate retrieval quality independently of generation.

Usage:
    uv run python scripts/retrieval_eval.py \\
      --dataset evals/datasets/dev.jsonl \\
      --k 5
"""

import argparse
import time
from pathlib import Path

from strideguard.datasets import load_cases
from strideguard.retrieval import open_store, recall_at_k, reciprocal_rank, retrieve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    cases = [case for case in load_cases(args.dataset) if case.expected_behavior.expected_document_ids]
    store = open_store()

    recalls = {1: [], 3: [], min(5, args.k): []}
    reciprocal_ranks = []
    empty_retrieval_cases = []
    failed_cases = []

    for case in cases:
        expected = set(case.expected_behavior.expected_document_ids)
        started = time.perf_counter()
        documents = retrieve(case.user_input, k=args.k, store=store)
        latency_ms = (time.perf_counter() - started) * 1000
        retrieved_ids = [str(document.metadata["doc_id"]) for document in documents]

        if not retrieved_ids:
            empty_retrieval_cases.append(case.case_id)

        for k in recalls:
            recalls[k].append(recall_at_k(expected, retrieved_ids, k))
        rr = reciprocal_rank(expected, retrieved_ids)
        reciprocal_ranks.append(rr)
        if rr == 0.0:
            failed_cases.append(case.case_id)

        print(
            f"{case.case_id}: retrieved={retrieved_ids} expected={sorted(expected)} "
            f"rr={rr:.2f} latency={latency_ms:.0f}ms"
        )

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    print("\n--- Retrieval summary ---")
    for k, values in recalls.items():
        print(f"recall@{k}: {mean(values):.3f}")
    print(f"mean reciprocal rank: {mean(reciprocal_ranks):.3f}")
    print(f"cases with empty retrieval: {empty_retrieval_cases}")
    print(f"cases with zero reciprocal rank: {failed_cases}")


if __name__ == "__main__":
    main()
