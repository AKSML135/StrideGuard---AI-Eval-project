# Architecture and trust boundaries

## System modes

StrideGuard runs in three modes, evaluated separately:

1. **Baseline** (`src/strideguard/support.py` via `experiment.run_case`) --
   the full policy context is stuffed into the prompt. No retrieval, no tools.
2. **RAG** (`src/strideguard/rag.py`) -- policy sections are embedded into a
   local Qdrant collection (`src/strideguard/retrieval.py`) and retrieved per
   question.
3. **Agent** (`src/strideguard/agent.py`) -- a LangChain tool-calling agent
   backed by a sandboxed SQLite database (`src/strideguard/db.py`), wrapped
   through an authorization-and-policy action layer
   (`src/strideguard/actions.py`) and exposed as narrow tools
   (`src/strideguard/tools.py`).

## Trust boundaries

```
 user text / retrieved docs / tool output   (UNTRUSTED)
              |
              v
      LLM (prompt, judge, agent reasoning)   (fallible, no authority)
              |
              v
   deterministic policy engine               (authoritative business rules)
     src/strideguard/policy_engine.py
              |
              v
   action layer (authorization + policy)     (security boundary)
     src/strideguard/actions.py
              |
              v
   SQLite repository (state)                 (source of truth)
     src/strideguard/db.py
```

The language model never decides authorization or time-boundary eligibility
directly -- it calls a tool, the tool calls the action layer, and the action
layer calls the deterministic policy engine before touching state. This is
why `evaluate_address_change` and `evaluate_return`
(`src/strideguard/policy_engine.py`) are pure, boundary-tested functions with
no model dependency.

## Data flow for one address-change request

1. `src/strideguard/agent.py` builds an agent with `get_order` and
   `update_address` tools (`src/strideguard/tools.py`).
2. The agent calls `get_order`, which calls `get_order_action`
   (`src/strideguard/actions.py`), which calls
   `OrderRepository.get_order` (`src/strideguard/db.py`).
3. The agent calls `update_address`, which calls `update_address_action`,
   which calls `evaluate_address_change` *before* calling
   `OrderRepository.update_address`.
4. Every tool call is recorded as a `ToolCallRecord`
   (`src/strideguard/models.py`) so deterministic evaluators
   (`src/strideguard/evaluators.py`) can check tool selection, arguments, and
   final database state independently of the model's prose.

## Evaluation layers

| Layer | Module | What it checks |
|---|---|---|
| Deterministic policy | `policy_engine.py` | Time/authorization/condition boundaries |
| Deterministic evaluators | `evaluators.py` | Decision, retrieval, citations, tools, final state |
| Retrieval metrics | `retrieval.py` | recall@k, reciprocal rank |
| Human labels | `models.HumanLabel`, `evals/rubrics/` | Policy, groundedness, privacy, action integrity, quality |
| Calibrated LLM judge | `judge.py` | Scaled-up approximation of human labels, validated against them |
| Security | `promptfooconfig.yaml`, `api.py` | Injection, secret extraction, cross-user access |
| CI gates | `.github/workflows/evals.yml` | Deterministic, offline release gate |

See the project guide's Appendix D (root-cause decision tree) for how a
failure is traced backward through these layers to find the actual
engineering defect, rather than being labeled generically as "the LLM
hallucinated."
