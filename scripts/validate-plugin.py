#!/usr/bin/env python3
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
missing = [skill for skill in plugin.get("skills", []) if not (root / skill / "SKILL.md").is_file()]
if missing:
    raise SystemExit("Missing plugin skill paths: " + ", ".join(missing))

safety_relevant_skills = (
    "agent-readiness",
    "commerce-protocol-readiness",
    "custom-agent-remediation-plan",
    "ecommerce-policy-readiness",
    "fde-opportunity-map",
    "product-knowledge-gap-analysis",
    "readiness-audit",
)
guardrails_path = root / "skills/agentic-commerce/references/guardrails.md"
guardrails = guardrails_path.read_text()
shared_reference = "See `../references/guardrails.md`"
email_delegation_skills = (
    "custom-agent-remediation-plan",
    "ecommerce-policy-readiness",
)
delegated_email_skills = (
    "00-email-marketing-guardrails",
    "09-post-purchase-customer-success",
    "14-transactional-service",
    "16-inventory-price-alert",
    "19-lifecycle-orchestration",
)
agentic_email_skills = (*delegated_email_skills, "email-writing")
email_delegation_rules = (
    "When a finding requires a customer communication workflow, Agentic Commerce supplies the authoritative event, verified recipient binding, order or product facts, and permitted action boundaries. Delegate channel execution to the [Email Marketing skills pack](https://github.com/wakqasahmed/email-marketing-skills):",
    "Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.",
    "Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.",
    "Route overlapping customer flows to `19-lifecycle-orchestration`.",
    "Apply `00-email-marketing-guardrails` to promotional content and all other delegated channel work.",
    "An email address identifies a recipient; it does not establish marketing consent.",
    "Never relabel promotional content as transactional.",
)

for skill_name in safety_relevant_skills:
    skill_path = root / "skills/agentic-commerce" / skill_name / "SKILL.md"
    skill = skill_path.read_text()
    if shared_reference not in skill:
        raise SystemExit(f"Safety-relevant skill does not reference shared guardrails: {skill_name}")
    if f"`{skill_name}`" not in guardrails:
        raise SystemExit(f"Shared guardrails do not define safety-relevant skill: {skill_name}")

for skill_name in email_delegation_skills:
    skill_path = root / "skills/agentic-commerce" / skill_name / "SKILL.md"
    skill = skill_path.read_text()
    for rule in email_delegation_rules:
        if skill.count(rule) != 1:
            raise SystemExit(
                f"Customer communication delegation contract missing from {skill_name}: {rule}"
            )

for skill_path in (root / "skills/agentic-commerce").glob("*/SKILL.md"):
    frontmatter = skill_path.read_text().partition("---")[2].partition("---")[0]
    name_match = re.search(r"^name:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    if name_match and name_match.group(1) in agentic_email_skills:
        raise SystemExit(
            "Delegated Email Marketing skills must not be copied into Agentic Commerce: "
            f"{name_match.group(1)}"
        )

normalized_guardrails = " ".join(guardrails.split())
autonomous_section = normalized_guardrails.partition("## Autonomous action safety")[2]
autonomous_section = autonomous_section.partition("## ")[0]
evidence_section = normalized_guardrails.partition("## Evidence provenance")[2]
evidence_section = evidence_section.partition("## ")[0]
sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", autonomous_section)]
action_sentence = next(
    (sentence for sentence in sentences if "autonomous checkout" in sentence.lower()),
    "",
)
payment_sentence = next(
    (sentence for sentence in sentences if "autonomous payment execution" in sentence.lower()),
    "",
)
evidence_sentence = next(
    (
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", evidence_section)
        if "public-signal evidence" in sentence.lower()
    ),
    "",
)
permissive_safeguard_language = (
    " or ",
    "unless",
    "except",
    "optional",
    "instead",
    "alternative",
    "where practical",
    "if possible",
)

if not action_sentence.startswith("Do not recommend ") or " without " not in action_sentence:
    raise SystemExit("Shared guardrails must preserve the autonomous action hard gate")

required_actions = (
    "checkout",
    "payment",
    "support",
    "order",
    "other operational commerce actions",
)
for action in required_actions:
    if action not in action_sentence.lower():
        raise SystemExit(f"Shared hard gate must cover {action}")

action_preconditions = action_sentence.partition(" without ")[2].lower()
required_action_safeguards = (
    "approval workflows",
    "policy grounding",
    "audit logging",
    "human escalation path",
)
for safeguard in required_action_safeguards:
    if safeguard not in action_preconditions:
        raise SystemExit(f"Shared hard gate requires {safeguard}")
if any(term in action_preconditions for term in permissive_safeguard_language):
    raise SystemExit("Shared hard gate safeguards must remain all required, not alternatives")

evidence_requirement = (
    "Label findings as public-signal evidence unless the user has explicitly provided "
    "verified exports"
)
if not evidence_sentence.startswith(evidence_requirement):
    raise SystemExit("Evidence provenance must distinguish public signals from verified exports")

payment_safeguards = (
    "identity verification",
    "consent capture",
    "fraud controls",
    "audit logging",
    "human escalation path",
)
for safeguard in payment_safeguards:
    if safeguard not in payment_sentence.lower():
        raise SystemExit(f"Shared payment guardrails require {safeguard}")

payment_requirement = "requires all of the following before it is recommended:"
payment_preconditions = payment_sentence.partition(payment_requirement)[2].lower()
if (
    payment_requirement not in payment_sentence
    or not payment_preconditions
    or any(term in payment_preconditions for term in permissive_safeguard_language)
):
    raise SystemExit("Shared payment safeguards must remain all required, not alternatives")

print(f"validated {len(plugin.get('skills', []))} plugin skills")
