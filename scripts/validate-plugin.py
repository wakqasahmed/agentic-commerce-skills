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
    "readiness-audit",
)
guardrails_path = root / "skills/agentic-commerce/references/guardrails.md"
guardrails = guardrails_path.read_text()
shared_reference = "See `../references/guardrails.md`"

for skill_name in safety_relevant_skills:
    skill_path = root / "skills/agentic-commerce" / skill_name / "SKILL.md"
    skill = skill_path.read_text()
    if shared_reference not in skill:
        raise SystemExit(f"Safety-relevant skill does not reference shared guardrails: {skill_name}")
    if f"`{skill_name}`" not in guardrails:
        raise SystemExit(f"Shared guardrails do not define safety-relevant skill: {skill_name}")

normalized_guardrails = " ".join(guardrails.split())
autonomous_section = normalized_guardrails.partition("## Autonomous action safety")[2]
autonomous_section = autonomous_section.partition("## ")[0]
sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", autonomous_section)]
action_sentence = next(
    (sentence for sentence in sentences if "autonomous checkout" in sentence.lower()),
    "",
)
payment_sentence = next(
    (sentence for sentence in sentences if "autonomous payment execution" in sentence.lower()),
    "",
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
if " or " in action_preconditions:
    raise SystemExit("Shared hard gate safeguards must remain all required, not alternatives")

required_guardrails = (
    "public-signal evidence",
    "verified exports",
)
for guardrail in required_guardrails:
    if guardrail not in guardrails:
        raise SystemExit(f"Shared guardrails require {guardrail}")

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
permissive_payment_language = (
    " or ",
    "unless",
    "except",
    "optional",
    "instead",
    "alternative",
    "where practical",
    "if possible",
)
if (
    payment_requirement not in payment_sentence
    or not payment_preconditions
    or any(term in payment_preconditions for term in permissive_payment_language)
):
    raise SystemExit("Shared payment safeguards must remain all required, not alternatives")

print(f"validated {len(plugin.get('skills', []))} plugin skills")
