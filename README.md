# Agentic Commerce Skills [![skills.sh](https://skills.sh/b/wakqasahmed/agentic-commerce-skills)](https://skills.sh/wakqasahmed/agentic-commerce-skills)

Practical agent skills for ecommerce teams preparing for AI-mediated discovery, answers, recommendations, checkout, support, and automation.

AI agents do not browse stores like humans. They fetch, parse, summarize, compare, cite, and increasingly act. This skill pack helps you check whether an ecommerce storefront is discoverable, readable, citable, and ready for agentic commerce workflows.

## Who This Is For

- Ecommerce founders checking whether their store is AI-ready.
- Developers improving crawler access, product data, schema, `llms.txt`, MCP, ACP, UCP, x402, or checkout readiness.
- Agencies and consultants producing AI search, AEO, GEO, and Agentic Commerce audits.

## Install

Install with skills.sh-compatible tooling:

```bash
npx skills@latest add wakqasahmed/agentic-commerce-skills
```

Local Claude CLI fallback:

```bash
scripts/list-skills.sh
scripts/link-skills.sh
```

## What This Helps You Find

- AI crawler or robots.txt blocks.
- Missing sitemap, llms.txt, link headers, or agent-facing discovery signals.
- Weak product titles, descriptions, variants, prices, availability, images, or attributes.
- Missing structured data for products, offers, FAQs, policies, and organization context.
- Product and policy gaps that stop agents from answering confidently.
- Unclear shipping, returns, refunds, warranty, support, or escalation paths.
- Checkout and order-flow gaps that block agent-assisted commerce.
- Protocol readiness gaps across ACP, UCP, x402, MCP, A2A, OAuth, payment, checkout, and order workflows.

## Skills

- `readiness-audit`: route a storefront into Custom Agent, Verified Audit, FDE, or Not Qualified.
- `seo-aeo-geo-audit`: check SEO, answer engine, and generative engine visibility.
- `agent-readiness`: check whether agents can crawl, read, cite, and safely act on a store.
- `commerce-protocol-readiness`: audit ACP, UCP, AP2, x402, MPP, MCP, A2A, OAuth, checkout, order, and payment readiness.
- `product-knowledge-gap-analysis`: find missing product data that blocks AI answers and support automation.
- `llms-txt-and-crawler-access`: review `robots.txt`, sitemap, `llms.txt`, AI bot rules, and crawl access.
- `ecommerce-policy-readiness`: assess shipping, returns, refunds, warranty, support, and escalation clarity.
- `custom-agent-remediation-plan`: convert audit gaps into a custom ecommerce agent implementation plan.
- `fde-opportunity-map`: identify when deeper Forward Deployed Engineering is warranted.
- `skills-marketplace-readiness`: prepare a skills repo for skills.sh, Agent Skills clients, Claude plugins, Codex, Cursor, Copilot, and related directories.

## Example Prompts

```text
Use the agentic commerce readiness audit skill on https://example-store.com and tell me the top 5 blockers for AI shoppers.
```

```text
Audit this Shopify store for ACP, UCP, x402, MCP, crawler access, llms.txt, schema, product data, and policy readiness.
```

```text
Find product knowledge gaps that would stop ChatGPT, Claude, Perplexity, or Gemini from recommending this store confidently.
```

```text
Review this store's shipping, returns, refunds, warranty, and support policies for AI shopper readiness.
```

```text
Turn these audit findings into a custom agent remediation plan for an ecommerce owner.
```

## What This Does Not Do

- It does not guarantee search rankings, AI citations, or sales.
- It does not certify that a store is officially accepted by any AI platform.
- It does not prove private analytics, revenue, conversion, or Search Console data unless you provide those exports.
- It does not recommend autonomous payments or checkout without consent, audit logs, fraud controls, and human escalation paths.

## Why This Exists

AI agents are becoming a new storefront interface.

The first wave of Agentic Commerce work is not “let agents buy everything automatically.” It is more basic:

1. Can agents discover your store?
2. Can they understand your products?
3. Can they cite your answers confidently?
4. Can they explain your policies accurately?
5. Can they identify safe next actions?
6. Can your checkout and support flows evolve toward agentic commerce protocols?

This skill pack turns those questions into practical audits and remediation plans.

## Marketplace And Discovery

- Public install command: npx skills@latest add wakqasahmed/agentic-commerce-skills
- skills.sh page: https://skills.sh/wakqasahmed/agentic-commerce-skills
- GitHub repo: https://github.com/wakqasahmed/agentic-commerce-skills

## For Developers

If you are adopting AI coding agents for real engineering work, also see my General Engineering Workflow Skills:

https://github.com/wakqasahmed/ai-engineering-workflow-skills

That repo covers clarification, issue decomposition, definition of done, review gates, release gates, HITL blockers, and handoffs.

## Author

I help ecommerce teams become ready for AI agents across discovery, answers, recommendations, checkout, support, and automation.

If you want your ecommerce store reviewed for Agentic Commerce, SEO, AEO, GEO, AI crawler readiness, product data quality, policy clarity, and checkout readiness, contact me.
