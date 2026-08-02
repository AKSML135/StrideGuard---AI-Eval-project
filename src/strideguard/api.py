from fastapi import FastAPI
from pydantic import BaseModel

from strideguard.llm_factory import build_chat_model
from strideguard.rag import answer_with_rag

app = FastAPI()


class PromptfooRequest(BaseModel):
    prompt: str


# NOTE: the /health endpoint is referenced by the guide's curl smoke-test
# command but its implementation was never printed. Added here as the
# obvious minimal liveness check.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/promptfoo")
def promptfoo(request: PromptfooRequest) -> dict[str, object]:
    answer, retrieved_doc_ids = answer_with_rag(
        question=request.prompt,
        model=build_chat_model(),
    )
    return {
        "output": answer.answer,
        "decision": answer.decision,
        "cited_doc_ids": answer.cited_doc_ids,
        "retrieved_doc_ids": retrieved_doc_ids,
    }
