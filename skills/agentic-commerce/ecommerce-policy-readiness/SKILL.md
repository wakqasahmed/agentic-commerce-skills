---
name: ecommerce-policy-readiness
description: Assess whether ecommerce policies are clear enough for AI answers, support drafts, and supervised order workflows.
---

# Ecommerce Policy Readiness

## Workflow

1. Check shipping, delivery, returns, refunds, warranty, payment, cancellations, substitutions, and support escalation.
2. Identify ambiguity that would cause wrong AI answers or unsafe support drafts.
3. Check whether policies are linked from product, cart, checkout, and support surfaces.
4. Convert policy gaps into answer-ready snippets and escalation rules.

Run the checks in `references/checks.md` and cite the observed output for each finding.

## Output

- Policy gap
- Risk to buyer or operator
- Suggested wording/fix
- Whether a custom agent needs a rule, memory item, or integration

## Customer communication delegation

When a finding requires a customer communication workflow, Agentic Commerce supplies the authoritative event, verified recipient binding, order or product facts, and permitted action boundaries. Delegate channel execution to the [Email Marketing skills pack](https://github.com/wakqasahmed/email-marketing-skills):

- Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.
- Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.
- Route overlapping customer flows to `19-lifecycle-orchestration`.
- Apply `00-email-marketing-guardrails` to promotional content and all other delegated channel work.

An email address identifies a recipient; it does not establish marketing consent. Never relabel promotional content as transactional.

## Guardrails

- See `../references/guardrails.md` for shared cross-skill guardrails (autonomous action safety, evidence provenance, internal runtime disclosure).
- Ground every policy answer or draft in a verified, current policy source; never infer a return, refund, delivery, warranty, or cancellation term from a product page or common practice.
- Return `HOLD` with the missing policy fact while it can be collected. Return `BLOCK` when a material policy, exception, or authority cannot be verified.
- Keep refunds, cancellations, substitutions, and order changes supervised by the merchant's authorized workflow; policy readability is not authority to execute an action.
- State the evidence source, the buyer or operator risk, and the escalation path for every unresolved material policy gap.
