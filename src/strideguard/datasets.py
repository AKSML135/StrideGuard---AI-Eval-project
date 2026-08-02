import json
from collections import Counter
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel

from strideguard.models import GoldenCase

ModelT = TypeVar("ModelT", bound=BaseModel)


def load_jsonl(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    records: list[ModelT] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(model_type.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(
                    f"Invalid record at {path}:{line_number}: {exc}"
                ) from exc
    return records


def write_jsonl(path: Path, records: Iterable[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")


def validate_case_ids(cases: list[GoldenCase]) -> None:
    counts = Counter(case.case_id for case in cases)
    duplicates = sorted(case_id for case_id, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate case IDs: {duplicates}")


# NOTE: `load_cases` is imported by tests/unit/test_dataset.py and
# scripts/validate_dataset.py (Phase 5) but the guide never prints its body --
# only its call sites. It is a thin, obvious convenience wrapper around
# load_jsonl, inferred to keep the phase runnable.
def load_cases(path: Path) -> list[GoldenCase]:
    return load_jsonl(path, GoldenCase)


def validate_dataset_coverage(cases: list[GoldenCase]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in cases:
        counts[f"intent:{case.tags.get('intent', 'missing')}"] += 1
        counts[f"risk:{case.tags.get('risk', 'missing')}"] += 1
        counts[f"critical:{bool(case.tags.get('critical', False))}"] += 1
        counts[
            f"requires_retrieval:{bool(case.tags.get('requires_retrieval', False))}"
        ] += 1
        counts[f"requires_tool:{bool(case.tags.get('requires_tool', False))}"] += 1
    return dict(sorted(counts.items()))
