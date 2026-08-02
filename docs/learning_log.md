# Learning log

## A note on how this repository was produced

This codebase was reconstructed from a 103-page phase-by-phase PDF project
guide ("StrideGuard - Phase-by-Phase AI Evaluation Project"). The guide is
explicitly written as a teaching document -- it tells the reader to
"implement the files yourself" after reading each phase, and it references an
external companion/starter repository that was not included in the PDF.

Most files in this repository (models, policy engine, evaluators, retrieval,
agent, judge, tracing, security config, CI workflow) were transcribed
directly from code blocks the guide prints in full. A smaller number of files
that the guide only describes in prose or shows only via CLI usage examples
(`settings.py`, the `scripts/*.py` CLIs, both Streamlit apps, `Makefile`,
and roughly 19 of the 20 seed dataset cases) were reconstructed to match the
guide's own specification. Every such file has a `NOTE:` comment at the top
explaining exactly what was inferred and why.

Use the entries below as a template: after you actually run each phase
against a live model, replace or extend them with your own real findings --
that is the entire point of this log.

---

## Phase 3 - deterministic policy engine

### What failed initially
The exact 60-minute case was rejected because I used `>= 60` rather than `> 60`.

### Root cause
The product policy said the boundary was inclusive, but the implementation
encoded an exclusive boundary.

### Fix
Changed the comparison and added 59, 60, and 61-minute tests.

### General lesson
Boundary language in product requirements must become explicit executable
tests.

---

## Phase N - (your entry here)

### What failed initially
### Root cause
### Fix
### General lesson
