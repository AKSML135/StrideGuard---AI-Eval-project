# evals/human_labels

This directory holds labeling artifacts produced while working through
Phase 7 and Phase 11 of the project guide. It starts empty except for this
file; the guide's scripts write into it, they don't ship pre-filled data:

- `<name>_labeling_template.csv` -- produced by
  `scripts/export_for_labeling.py`, one row per frozen run, ready to be
  labeled (by hand or via `apps/labeling_app.py`).
- `labeler_a.csv`, `labeler_b.csv` -- independent-round labels from two
  labelers, consumed by `scripts/agreement_report.py`.
- `adjudicated_gold.csv` -- the joined, adjudicated result of the two files
  above, consumed by `scripts/calibrate_judge.py`. Must include at least
  `case_id`, `run_id`, and `overall_pass` columns.

See `evals/rubrics/labeling_guide_v1.md` for scoring definitions and
`evals/rubrics/rubric_v1.yaml` for the machine-readable rubric.
