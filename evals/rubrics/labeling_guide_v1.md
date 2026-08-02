# StrideGuard labeling guide (v1)

## Unit of annotation

The unit of annotation is one frozen `run_id`. Never label a live, re-runnable
chatbot response -- label the exact recorded `RunRecord` so that the label
stays attached to a specific, reproducible system output.

## Source-priority rules

When judging whether a response is correct, apply the same source-priority
order defined in `docs/product_contract.md`:

1. Authenticated database facts.
2. Current versioned policy documents.
3. Product catalog.
4. Customer statements.
5. Model assumptions.

A lower-ranked source can never justify contradicting a higher-ranked source.
If the customer's stated order age conflicts with the database record, the
database record wins.

## Exact boundary definitions

- The address-change window is **60 minutes, inclusive**. An order exactly 60
  minutes old is still eligible; 61 minutes is not.
- The return window is **30 calendar days, inclusive**. Day 30 is eligible;
  day 31 is not.
- When original packaging is not addressed by policy, the correct behavior is
  to say the policy is incomplete and escalate -- not to invent a rule in
  either direction.

## Examples of pass, fail, and not-applicable

- **Pass**: a correct refund denial, even when the customer is unhappy about
  it. A customer's dissatisfaction is a signal about the product, not proof
  that the system was wrong.
- **Fail**: the response claims an address was updated before a tool result
  confirms success (`FALSE_SUCCESS`).
- **Not applicable**: `action_integrity` is not applicable when no tool call
  was required by the case.

## The evidence requirement

Every failing critical criterion or a failing `overall_pass` requires a
non-empty `evidence` string that quotes or closely paraphrases the specific
part of the response that is wrong. "Bad" is not evidence; "the response says
the window expired at 45 minutes" is evidence.

## Handling missing policy

When the published policy does not cover the situation, the assistant must
say so explicitly and escalate rather than invent a rule. Do not fail a
response for saying "I'm not sure, let me create a ticket" when the policy is
genuinely silent -- that is the correct behavior for `POLICY_MISSING` cases.

## Distinguishing user dissatisfaction from system incorrectness

A correct refund denial may pass even when the customer dislikes the policy.
A thumbs-down is a user signal, not proof of policy error. A response that
says "contact support" is incomplete when an escalation action is available
but not provided or initiated -- that is an `actionability` failure, not
necessarily a `policy_correctness` failure.

---

*Update the rubric version and this guide together whenever a definition
materially changes as a result of adjudication (see the agreement workflow in
Phase 7 of the project guide).*
