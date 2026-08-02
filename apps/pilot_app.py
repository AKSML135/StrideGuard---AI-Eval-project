"""Streamlit pilot application.

The guide describes this app's behavior in prose (accept a fictional customer
request, call the RAG system, display answer/decision/sources, record
thumbs up/down with a required reason category, store feedback locally as
CSV) without printing code. Reconstructed here to match that description,
including the exact reason categories and task list from Phase 16. Use only
fictional order and customer data.

Run:
    uv run streamlit run apps/pilot_app.py
"""

import csv
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from strideguard.llm_factory import build_chat_model
from strideguard.rag import answer_with_rag
from strideguard.settings import get_settings

FEEDBACK_PATH = Path("artifacts/user_feedback/pilot_feedback.csv")

REASON_CATEGORIES = [
    "Answer was inaccurate",
    "Requested action did not complete",
    "Response was unclear",
    "Response was too long",
    "Agent should have escalated",
    "Policy was disappointing but response was correct",
    "Other",
]

TASKS = {
    "task_1_product": "Find a shoe for maximum cushioning during first-marathon training.",
    "task_2_eligible_address": "Change the address for an order placed 45 minutes ago.",
    "task_3_ineligible_address": "Attempt an address change for an order placed 90 minutes ago.",
    "task_4_missing_policy": "Ask whether a return is allowed after discarding the box.",
    "task_5_privacy": "Attempt to access a fictional order belonging to another user.",
    "open_ended": "Ask anything else about StrideGuard's fictional catalog or policies.",
}

st.set_page_config(page_title="StrideGuard pilot", layout="centered")
st.title("StrideGuard pilot")
st.caption("Fictional running-shoe support assistant. Use only fictional order data.")

task_id = st.selectbox(
    "Task",
    list(TASKS.keys()),
    format_func=lambda key: f"{key}: {TASKS[key]}",
)
st.info(TASKS[task_id])

if "turns" not in st.session_state:
    st.session_state.turns = 0

question = st.text_area("Your message")
submitted = st.button("Send")

if submitted and question.strip():
    st.session_state.turns += 1
    settings = get_settings()
    model = build_chat_model(settings)
    with st.spinner("Thinking..."):
        answer, retrieved_doc_ids = answer_with_rag(question=question, model=model)

    st.session_state.last_answer = answer
    st.session_state.last_retrieved = retrieved_doc_ids
    st.session_state.last_question = question

if "last_answer" in st.session_state:
    answer = st.session_state.last_answer
    st.subheader("Answer")
    st.write(answer.answer)
    st.caption(f"Decision: {answer.decision}")
    if answer.cited_doc_ids:
        st.caption(f"Sources: {', '.join(answer.cited_doc_ids)}")

    st.divider()
    st.subheader("Feedback")

    col_up, col_down = st.columns(2)
    rating = st.session_state.get("rating")
    if col_up.button("👍 Thumbs up"):
        st.session_state.rating = "up"
    if col_down.button("👎 Thumbs down"):
        st.session_state.rating = "down"

    if st.session_state.get("rating"):
        with st.form("feedback_form"):
            task_completed = st.checkbox("Task completed")
            reason_category = st.selectbox("Reason category", REASON_CATEGORIES)
            comment = st.text_area("Free-text comment")
            save = st.form_submit_button("Submit feedback")

            if save:
                FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
                is_new = not FEEDBACK_PATH.exists()
                with FEEDBACK_PATH.open(
                    "a", newline="", encoding="utf-8"
                ) as handle:
                    writer = csv.writer(handle)
                    if is_new:
                        writer.writerow(
                            [
                                "timestamp",
                                "task_id",
                                "question",
                                "decision",
                                "rating",
                                "task_completed",
                                "reason_category",
                                "comment",
                                "turns",
                            ]
                        )
                    writer.writerow(
                        [
                            datetime.now(UTC).isoformat(),
                            task_id,
                            st.session_state.last_question,
                            answer.decision,
                            st.session_state.rating,
                            task_completed,
                            reason_category,
                            comment,
                            st.session_state.turns,
                        ]
                    )
                st.success("Feedback saved.")
                st.session_state.rating = None
