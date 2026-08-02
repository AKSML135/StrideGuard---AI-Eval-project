import json
import re
from pathlib import Path

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_policy_sections(policy_dir: Path) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    for path in sorted(policy_dir.glob("*.md")):
        current_heading = "document"
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_lines
            text = "\n".join(current_lines).strip()
            if text:
                sections.append(
                    {
                        "doc_id": f"{path.stem}#{slugify(current_heading)}",
                        "title": current_heading,
                        "text": text,
                        "source": str(path),
                        # NOTE: "version" wasn't in the guide's printed dict
                        # (only referenced later via metadata["version"] when
                        # building RAG documents in Phase 9). Inferred here
                        # from the "_v1" / "_v2" suffix convention used by
                        # every policy filename (e.g. shipping_v1.md).
                        "version": (
                            path.stem.rsplit("_", maxsplit=1)[-1]
                            if "_" in path.stem
                            else "v1"
                        ),
                    }
                )
            current_lines = []

        for line in path.read_text(encoding="utf-8").splitlines():
            match = HEADING_PATTERN.match(line)
            if match:
                flush()
                current_heading = match.group(2)
            else:
                current_lines.append(line)
        flush()
    return sections


def _format_section(section: dict[str, object]) -> str:
    return f"[{section['doc_id']}]\n{section['text']}"


# NOTE: `load_full_context` is imported directly by src/strideguard/experiment.py
# in Phase 6, but the guide only ever describes what knowledge.py "should do"
# in prose (read markdown, split at headings, generate IDs, format sections,
# append the product catalog) -- it never prints this function's body.
# Reconstructed here to match that description exactly.
def load_full_context(project_root: Path) -> str:
    project_root = Path(project_root)
    sections = load_policy_sections(project_root / "knowledge" / "policies")
    parts = [_format_section(section) for section in sections]

    products_path = project_root / "data" / "products.json"
    if products_path.exists():
        products = json.loads(products_path.read_text(encoding="utf-8"))
        for product in products:
            doc_id = f"products_v1#{slugify(product['name'])}"
            parts.append(f"[{doc_id}]\n{json.dumps(product, indent=2)}")

    return "\n\n".join(parts)
