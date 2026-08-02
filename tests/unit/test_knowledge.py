"""Unit tests for src/strideguard/knowledge.py.

NOTE: the guide references this test file by name only (Phase 9's
"uv run pytest tests/unit/test_knowledge.py ...") without printing its
contents. Reconstructed here to cover the behavior knowledge.py's own Phase 4
description promises: splitting markdown by heading, generating stable
doc_ids, and formatting sections for retrieval.
"""

from pathlib import Path

from strideguard.knowledge import load_policy_sections, slugify


def test_slugify_produces_url_safe_ids() -> None:
    assert slugify("Address change window") == "address-change-window"
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"


def test_load_policy_sections_splits_by_heading(tmp_path: Path) -> None:
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    (policy_dir / "shipping_v1.md").write_text(
        "# Shipping Policy\n\n"
        "## Address change window\n\n"
        "Eligible through 60 minutes.\n\n"
        "## Ownership\n\n"
        "Only the owner may modify an order.\n",
        encoding="utf-8",
    )

    sections = load_policy_sections(policy_dir)
    doc_ids = {section["doc_id"] for section in sections}

    assert "shipping_v1#address-change-window" in doc_ids
    assert "shipping_v1#ownership" in doc_ids
    assert all(section["version"] == "v1" for section in sections)


def test_load_policy_sections_is_stable_across_calls(tmp_path: Path) -> None:
    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    (policy_dir / "returns_v1.md").write_text(
        "# Return Policy\n\n## Return window\n\nEligible within 30 days.\n",
        encoding="utf-8",
    )

    first = load_policy_sections(policy_dir)
    second = load_policy_sections(policy_dir)

    assert [section["doc_id"] for section in first] == [
        section["doc_id"] for section in second
    ]
