# StrideGuard final evaluation report

*Template from Phase 17 of the project guide. Fill in every section with
measured results -- every percentage should include a denominator
(e.g. "27/30 critical cases passed (90%)", not just "90%").*

## 1. Product outcome

## 2. Architecture and trust boundaries

See `docs/architecture.md`.

## 3. Supported and unsupported behavior

See `docs/product_contract.md`.

## 4. Failure taxonomy

See `evals/failure_taxonomy.yaml`.

## 5. Dataset composition and limitations

## 6. Human-labeling and adjudication process

See `evals/rubrics/labeling_guide_v1.md`.

## 7. Inter-labeler agreement

## 8. Deterministic evaluators

## 9. Retrieval results

## 10. Agent action and state results

## 11. LLM-judge calibration

## 12. Security/red-team results

## 13. Experiment comparison

## 14. Slice analysis

## 15. Latency, usage, and errors

## 16. Pilot feedback

## 17. Remaining risks

## 18. Reproduction instructions

```bash
cp .env.example .env
uv sync --extra dev --extra evals
uv run pytest tests/unit -q
uv run python scripts/validate_dataset.py evals/datasets/dev.jsonl
```

See the project guide's Appendix A for the full command sequence.
