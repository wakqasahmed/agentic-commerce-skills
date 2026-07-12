# Security Policy

## What this repository is

This repository is a pack of `SKILL.md` files and reference markdown for AI agent clients (Claude Code, Claude Desktop, and other Agent Skills / MCP-compatible tools). Skills are **prompt and instruction content, not executable code**. Installing a skill adds markdown to an agent's context; it does not add a binary, script, or dependency that runs on its own.

That said, skill instructions can direct an agent to run shell commands or fetch URLs, and an agent that follows those instructions is doing so with whatever permissions the user has granted it. Review a skill's instructions before installing it, the same way you would review any prompt you give an agent broad permissions to act on.

## Known instructions that run commands or fetch URLs

- `skills/agentic-commerce/agent-readiness/references/checks.md` — instructs the agent to run `curl` commands (with a `python3 -m json.tool` pipe) against the storefront URL under review: fetching `robots.txt`, response headers, raw page HTML, and JSON-LD payloads, and probing for `llms.txt`/`sitemap.xml`/`.well-known/ai-plugin.json`. Several of these commands spoof the `User-Agent` header as `GPTBot`, `ClaudeBot`, or `PerplexityBot` to test bot-specific blocking — this is the one behavior in this repo that could resemble scraping-evasion to a site owner or WAF if run against a site you don't control or have permission to audit.
- `skills/agentic-commerce/skills-marketplace-readiness/SKILL.md` — references the `npx skills@latest add owner/repo` install command as an example of a marketplace-compatible README install line; it does not itself instruct the agent to run it.

No skill in this repository instructs an agent to download and execute remote scripts, transmit credentials, or fetch content from anywhere other than the storefront URL supplied by the user for that specific audit.

## Reporting a security concern

This repository has no automated build, dependency install, or deploy pipeline, so most "security" concerns will be about skill instructions themselves: a skill that tells an agent to do something unsafe, exfiltrate data, or misrepresent its own scope.

To report a concern:

1. Open a GitHub issue in this repository: https://github.com/wakqasahmed/agentic-commerce-skills/issues/new
2. Include the skill name (or file path), the instruction you're concerned about, and the risk you see.
3. If the concern is sensitive, do not paste details into a public issue — a GitHub issue title cannot make an issue private. Instead use GitHub's private vulnerability reporting for this repository (Security tab → "Report a vulnerability"), which opens a private draft advisory visible only to maintainers.

## Scope

- In scope: instructions in any `SKILL.md` or `references/*.md` file, `scripts/*.sh` and `scripts/*.py`, and `.claude-plugin/plugin.json`.
- Out of scope: the behavior of third-party AI agent clients that execute these skills, and the behavior of storefronts audited using these skills.
