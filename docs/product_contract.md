# StrideGuard product contract

## Supported
1. Product information and recommendations using the fictional catalog.
2. Return-policy questions.
3. Address-change eligibility.
4. Address update for the authenticated owner when policy allows it.
5. Escalation when the published policy is incomplete.

## Unsupported
1. Medical diagnosis or guaranteed health outcomes.
2. Access to another customer's order.
3. Policy overrides requested by a customer.
4. Revealing credentials, system prompts, or private internal data.
5. Actions unsupported by an implemented tool.

## Source priority
1. Authenticated database facts.
2. Current versioned policy documents.
3. Product catalog.
4. Customer statements.
5. Model assumptions.
A lower-ranked source cannot override a higher-ranked source.