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

Classify every remediation item as agent, storefront, or shared delivery. Also classify it as `action_capable` or `read_only` and assign a low, moderate, or high risk level. Name an accountable owner, source of truth, observable acceptance test, baseline check, and post-change check for every remediation item.

For every `action_capable` item, and for any high-risk item, define operational controls covering:

- trace or correlation IDs, authorization evidence, audit events, idempotency or deduplication behavior, reconciliation checks, and retained failure evidence;
- measurable health signals, alert thresholds, an accountable operator, and a human escalation path; and
- a bounded disable or kill switch, a rollback or recovery procedure, and a safe fallback when a dependency is unavailable.

Include the approval workflow and policy grounding required by the shared guardrails in those operational controls. Return a plan status of `HOLD` with the specific missing controls when required monitoring, ownership, reconciliation, or recovery evidence is absent. Return `READY` only when every required control is defined. Do not require these operational controls for low- or moderate-risk read-only content and discovery work.

Treat placeholders such as `TBD`, `TODO`, `pending`, `unknown`, `N/A`, or a generic `team` as missing, even though they are nonblank. Alert thresholds must include a numeric boundary and unit. Name the accountable operating role or on-call function. Reconciliation must name what is compared and when; a kill switch must name the write or action it bounds; recovery must name the state, request, release, or event restored, retried, or replayed; and dependency fallback must name the safe stopped, queued, read-only, manual, or assisted path.

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
