---
name: custom-agent-remediation-plan
description: Convert Agentic Commerce audit findings into a custom-agent implementation checklist. Use after readiness, SEO/AEO/GEO, product knowledge, or policy gaps are known.
---

# Custom Agent Remediation Plan

## Workflow

Use only after verified audit findings identify remediation gaps.

1. Group findings into content, product knowledge, crawler access, policy, integration, and workflow buckets.
2. Decide what the custom agent can improve directly versus what needs storefront/platform changes.
3. Define required sources of truth: catalog, policies, support inbox, order system, CMS, analytics exports when provided.
4. Produce a setup checklist with acceptance tests.
5. Define how score lift or readiness improvement will be verified.

Run the checks in `references/checks.md` against the audit findings and proposed plan before presenting it.

Classify every remediation item as agent, storefront, or shared delivery. Name an accountable owner, source of truth, observable acceptance test, baseline check, and post-change check for every remediation item.

## Customer communication delegation

When a finding requires a customer communication workflow, Agentic Commerce supplies the authoritative event, verified recipient binding, order or product facts, and permitted action boundaries. Delegate channel execution to the [Email Marketing skills pack](https://github.com/wakqasahmed/email-marketing-skills):

- Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.
- Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.
- Route overlapping customer flows to `19-lifecycle-orchestration`.
- Apply `00-email-marketing-guardrails` to promotional content and all other delegated channel work.

An email address identifies a recipient; it does not establish marketing consent. Never relabel promotional content as transactional.

## Guardrails

- See `../references/guardrails.md` for shared cross-skill guardrails (autonomous action safety, evidence provenance, internal runtime disclosure).
- Do not promise full automation where supervised workflows are safer.
- Do not use a remediation plan as authority to execute customer, order, payment, credential, or production changes.
