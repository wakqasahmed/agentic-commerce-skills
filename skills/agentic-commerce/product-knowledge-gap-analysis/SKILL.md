---
name: product-knowledge-gap-analysis
description: Find ecommerce product data gaps that block AI answers, recommendations, support automation, and agentic commerce workflows.
---

# Product Knowledge Gap Analysis

## Workflow

1. Select representative products and variant families. Inspect attributes, specs, ingredients/materials, sizing, compatibility, use cases, and contraindications.
2. Capture product facts from raw HTML, rendered product content when available, JSON-LD, and an operator-supplied public feed. Label each observation with its surface, provenance, and timestamp.
3. Compare product and variant identifiers, price, currency, availability, sale timing, fulfillment-relevant state, and observable freshness indicators across those surfaces.
4. When checkout evidence is safely available, compare it separately using only a supervised non-purchasing check or verified operator-provided evidence. Never place an order to complete the audit.
5. Check whether product pages answer buyer questions without support escalation and identify missing schema or feed fields.
6. Group gaps by template-level fixes vs product-specific enrichment. Recommend the smallest product knowledge load needed for a custom agent.

Run the checks in `references/checks.md` and cite the observed output for each finding.

Report every cross-surface mismatch with:

- the fact and blocking status;
- every conflicting surface and its observed value;
- the evidence timestamp;
- the buyer or agent failure mode;
- the proposed source of truth; and
- the accountable remediation owner.

## Guardrails

See `../references/guardrails.md` for shared evidence-provenance and autonomous-action rules.

- Treat facts without a visible source as unknown; never infer ingredients, compatibility, contraindications, or safety claims.
- Separate template-level fixes from product-specific enrichment.
- Do not alter catalog data or make product claims; identify the source of truth and route remediation to its owner.
- Treat raw HTML, rendered content, JSON-LD, and public feeds as public-signal evidence. Never present them as proof that checkout values match.
- Report checkout consistency only when supported by a supervised non-purchasing check or verified operator-provided evidence. Do not add to cart when that can reserve inventory, submit checkout, authorize payment, or place an order.

## Output

- Missing attribute, answer, or conflicting fact
- Affected product, variant, template, and surfaces
- Evidence provenance and timestamp
- Customer or AI-agent failure mode
- Proposed source of truth and remediation owner
- Blocking status
