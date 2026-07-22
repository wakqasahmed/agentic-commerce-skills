#!/usr/bin/env python3
import json
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

hard_gate = "Do not recommend autonomous checkout, payment, or support actions without"
if hard_gate not in guardrails:
    raise SystemExit("Shared guardrails must preserve the autonomous action hard gate")

required_guardrails = (
    "approval workflows",
    "policy grounding",
    "audit logging",
    "human escalation path",
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
    if safeguard not in guardrails:
        raise SystemExit(f"Shared payment guardrails require {safeguard}")

all_required_payment_safeguards = (
    "requires all of the following before it is recommended: identity verification, "
    "consent capture, and fraud controls, together with audit logging and a human "
    "escalation path"
)
if all_required_payment_safeguards not in " ".join(guardrails.split()):
    raise SystemExit("Shared payment safeguards must remain all required, not alternatives")

print(f"validated {len(plugin.get('skills', []))} plugin skills")
