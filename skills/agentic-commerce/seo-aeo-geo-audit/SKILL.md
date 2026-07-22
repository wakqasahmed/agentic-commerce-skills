---
name: seo-aeo-geo-audit
description: Audit ecommerce SEO, AEO, and GEO readiness for AI-mediated discovery and citation. Use for product/category pages, policy pages, content hubs, and agent-readable storefronts.
---

# SEO AEO GEO Audit

## Workflow

1. Check indexability, metadata, canonical posture, internal links, and sitemap coverage.
2. Check answerability: concise answers, FAQs, policies, comparisons, and evidence-backed claims.
3. Check generative-engine usefulness: entity clarity, product attributes, structured data, citations, and crawlable text.
4. Identify gaps by impact on buyer discovery, AI citation, and product recommendation.
5. Convert gaps into prioritized fixes.

This workflow is complete when this pack is installed by itself. Delegation adds specialist depth but
is not required to finish a lightweight ecommerce audit.

Run the checks in `references/checks.md` and cite the observed output for each finding.
Do not present an unverified crawl, schema, or content inference as an observed finding.
Keep recommendations separate from evidence and do not make production changes during an audit.

## Delegation

When the canonical AI Visibility pack is available, route deeper analysis to its specialist skills
instead of duplicating their instructions:

- Robots directives, meta robots, response headers, and AI crawler behavior → `robots-ai-crawler-audit`.
- Sitemap coverage, canonical URLs, indexability, redirects, and discovery paths → `sitemap-discovery-audit`.
- Schema.org and JSON-LD validity, coverage, and page alignment → `schema-markup-audit`.
- Page stability, specificity, trust signals, and claim citation support → `citation-readiness-audit`.
- Content gaps affecting explanations, comparisons, recommendations, and answers → `answer-engine-content-audit`.

Treat each delegation as a specialist handoff recommendation, not as an observed finding. After
findings are verified, route implementation planning to `ai-search-remediation-plan` when available.

## Guardrails

See `../references/guardrails.md` for the shared evidence provenance and autonomous action safety
boundaries. This audit does not authorize production changes or operational commerce actions.

## Output

### Observed storefront evidence

- Top blocking gaps, with the affected page or template
- Why each gap matters for SEO/AEO/GEO
- Cited observed output and proof/check command where possible

### Specialist handoff recommendations

- Deeper analysis needed and the canonical specialist skill to use

### Remediation work

- Prioritized recommended fixes derived from verified findings
- Implementation work kept separate from the audit evidence and specialist handoffs
