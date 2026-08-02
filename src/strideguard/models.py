from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class OrderStatus(str, Enum):
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    order_id: str
    owner_user_id: str
    created_at: datetime
    status: OrderStatus
    address: str
    product_id: str
    delivered_at: datetime | None = None


class SupportAnswer(BaseModel):
    decision: str = Field(description="Short machine-readable decision code")
    answer: str = Field(description="Customer-facing answer")
    cited_doc_ids: list[str] = Field(default_factory=list)
    next_action: str | None = None
    needs_escalation: bool = False

    @field_validator("cited_doc_ids")
    @classmethod
    def unique_citations(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None
    error: str | None = None


class RunRecord(BaseModel):
    run_id: str
    case_id: str
    mode: Literal["baseline", "rag", "agent"]
    provider: str
    model: str
    prompt_version: str
    knowledge_version: str
    started_at: datetime
    latency_ms: float
    response: SupportAnswer | None = None
    raw_response: str | None = None
    retrieved_doc_ids: list[str] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    final_state: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ExpectedBehavior(BaseModel):
    decision: str | None = None
    must_include_any: list[list[str]] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)
    expected_document_ids: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    expected_final_state: dict[str, Any] = Field(default_factory=dict)
    should_escalate: bool | None = None


class GoldenCase(BaseModel):
    case_id: str = Field(pattern=r"^[A-Z0-9_]+$")
    description: str
    user_input: str
    authenticated_user_id: str = "U-001"
    initial_state: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: ExpectedBehavior
    tags: dict[str, str | bool | int] = Field(default_factory=dict)


# GoldenCase = stable test specification
# RunRecord = one stochastic execution of one system version
#
# Never store a generated model response directly inside the golden case as if
# it were permanent ground truth. A single case can have many baseline, RAG,
# agent, prompt-version, and model-version runs.


PolicyLabel = Literal["pass", "fail", "not_applicable"]


class HumanLabel(BaseModel):
    case_id: str
    run_id: str
    labeler_id: str
    rubric_version: str
    policy_correctness: PolicyLabel
    groundedness: PolicyLabel
    privacy_and_authorization: PolicyLabel
    action_integrity: PolicyLabel
    task_completion: int = Field(ge=0, le=2)
    actionability: int = Field(ge=0, le=2)
    conciseness: int = Field(ge=0, le=2)
    tone: int = Field(ge=0, le=2)
    overall_pass: bool
    failure_codes: list[str] = Field(default_factory=list)
    evidence: str = ""
    notes: str = ""

    @model_validator(mode="after")
    def evidence_for_failure(self) -> "HumanLabel":
        has_failure = (
            not self.overall_pass
            or "fail"
            in {
                self.policy_correctness,
                self.groundedness,
                self.privacy_and_authorization,
                self.action_integrity,
            }
        )
        if has_failure and not self.evidence.strip():
            raise ValueError("Evidence is required for a failed label.")
        return self


# NOTE: `Decision` and `ProductCondition` are used by src/strideguard/policy_engine.py
# (Phase 3) but their field-by-field definitions were not printed verbatim in the
# guide's text -- only their call sites were. The fields below were inferred from
# every keyword argument the guide's policy_engine.py code passes to them
# (allowed, reason_code, explanation, requires_escalation) and from the
# conditions described in the returns policy (unopened, tried-on, lightly used,
# heavily used). Double check these against your own judgment when you implement
# this phase yourself.
class ProductCondition(str, Enum):
    UNOPENED = "unopened"
    TRIED_ON = "tried_on"
    LIGHTLY_USED = "lightly_used"
    HEAVILY_USED = "heavily_used"


class Decision(BaseModel):
    allowed: bool
    reason_code: str
    explanation: str
    requires_escalation: bool = False


class CriterionJudgement(BaseModel):
    label: Literal["pass", "fail", "not_applicable"]
    evidence: str


class JudgeVerdict(BaseModel):
    policy_correctness: CriterionJudgement
    groundedness: CriterionJudgement
    privacy_and_authorization: CriterionJudgement
    action_integrity: CriterionJudgement
    task_completion: int = Field(ge=0, le=2)
    actionability: int = Field(ge=0, le=2)
    conciseness: int = Field(ge=0, le=2)
    tone: int = Field(ge=0, le=2)
    overall_pass: bool
    failure_codes: list[str] = Field(default_factory=list)
