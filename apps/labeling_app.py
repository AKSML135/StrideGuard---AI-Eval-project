"""Streamlit labeling UI.

The guide describes this app's behavior in prose ("displays the user request,
expected behavior, frozen response, retrieved IDs, and tool calls; writes
labels to a local CSV") without printing code. Reconstructed here to match
that description and the CSV schema from scripts/export_for_labeling.py.

Run:
    uv run streamlit run apps/labeling_app.py
"""

import csv
from pathlib import Path

import streamlit as st

from strideguard.datasets import load_cases
from strideguard.models import RunRecord

st.set_page_config(page_title="StrideGuard labeling", layout="wide")
st.title("StrideGuard human labeling")

dataset_path = st.sidebar.text_input("Dataset path", "evals/datasets/dev.jsonl")
runs_path = st.sidebar.text_input("Runs path", "artifacts/runs/baseline_v1.jsonl")
labeler_id = st.sidebar.text_input("Labeler ID", "labeler_a")
rubric_version = st.sidebar.text_input("Rubric version", "1.0")
output_path = st.sidebar.text_input(
    "Output CSV", f"evals/human_labels/{labeler_id}.csv"
)

if not dataset_path or not runs_path:
    st.stop()

cases_by_id = {case.case_id: case for case in load_cases(Path(dataset_path))}

runs: list[RunRecord] = []
runs_file = Path(runs_path)
if runs_file.exists():
    with runs_file.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                runs.append(RunRecord.model_validate_json(line))

if not runs:
    st.warning("No runs found at that path yet.")
    st.stop()

run_options = [f"{run.case_id} ({run.run_id[:8]})" for run in runs]
selected_index = st.selectbox(
    "Select a frozen run", range(len(runs)), format_func=lambda i: run_options[i]
)
run = runs[selected_index]
case = cases_by_id.get(run.case_id)

st.subheader(f"Case: {run.case_id}")
if case:
    st.write("**Description**", case.description)
    st.write("**User input**", case.user_input)
    st.write("**Expected behavior**", case.expected_behavior.model_dump())

st.write("**Candidate response**")
st.json(run.response.model_dump() if run.response else {"error": run.error})
st.write("**Retrieved document IDs**", run.retrieved_doc_ids)
st.write("**Tool calls**", [call.model_dump() for call in run.tool_calls])

st.divider()
st.subheader("Label")

with st.form("label_form"):
    policy_correctness = st.selectbox(
        "Policy correctness", ["pass", "fail", "not_applicable"]
    )
    groundedness = st.selectbox("Groundedness", ["pass", "fail", "not_applicable"])
    privacy_and_authorization = st.selectbox(
        "Privacy and authorization", ["pass", "fail", "not_applicable"]
    )
    action_integrity = st.selectbox(
        "Action integrity", ["pass", "fail", "not_applicable"]
    )
    task_completion = st.slider("Task completion", 0, 2, 1)
    actionability = st.slider("Actionability", 0, 2, 1)
    conciseness = st.slider("Conciseness", 0, 2, 1)
    tone = st.slider("Tone", 0, 2, 2)
    overall_pass = st.checkbox("Overall pass")
    failure_codes = st.text_input("Failure codes (comma separated)")
    evidence = st.text_area("Evidence (required for any failing criterion)")
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Save label")

    if submitted:
        has_failure = not overall_pass or "fail" in {
            policy_correctness,
            groundedness,
            privacy_and_authorization,
            action_integrity,
        }
        if has_failure and not evidence.strip():
            st.error("Evidence is required for a failed label.")
        else:
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            is_new = not out_path.exists()
            with out_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if is_new:
                    writer.writerow(
                        [
                            "case_id",
                            "run_id",
                            "labeler_id",
                            "rubric_version",
                            "policy_correctness",
                            "groundedness",
                            "privacy_and_authorization",
                            "action_integrity",
                            "task_completion",
                            "actionability",
                            "conciseness",
                            "tone",
                            "overall_pass",
                            "failure_codes",
                            "evidence",
                            "notes",
                        ]
                    )
                writer.writerow(
                    [
                        run.case_id,
                        run.run_id,
                        labeler_id,
                        rubric_version,
                        policy_correctness,
                        groundedness,
                        privacy_and_authorization,
                        action_integrity,
                        task_completion,
                        actionability,
                        conciseness,
                        tone,
                        overall_pass,
                        failure_codes,
                        evidence,
                        notes,
                    ]
                )
            st.success(f"Saved label to {out_path}")
