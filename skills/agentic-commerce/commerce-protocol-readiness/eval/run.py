#!/usr/bin/env python3
"""Static behavioral eval for commerce-protocol-readiness's payment-safety guardrail.

Unlike readiness-audit/eval/run.py, this eval makes no LLM calls and needs no
API key: the guardrail under test ("do not recommend autonomous payments
without identity, consent, audit logs, fraud controls, and human escalation")
is checkable without running the model, so it runs on every push/PR via
scripts/ci.yml instead of being gated behind a manual, API-cost workflow.

Two checks:

1. Guardrail-text assertion -- SKILL.md's Guardrails section must still
   require identity, consent, audit logs, fraud controls, and human
   escalation before recommending autonomous payments. Catches a prose edit
   that quietly drops or waters down the guardrail.
2. Decision-logic fixtures -- eval/fixtures/*.scenario.json describes a
   storefront's protocol readiness and safeguard state; decide_recommendation()
   codifies the guardrail as a rule and is asserted against each fixture's
   *.expected.json. Includes a fixture that looks superficially "ready" (every
   payment protocol scored ready/verified) but is missing identity, consent,
   and audit logging -- exactly the case the guardrail exists to catch -- plus
   a genuinely-ready positive control and a discovery-only negative control.
"""
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SKILL_DIR = EVAL_DIR.parent
FIXTURES_DIR = EVAL_DIR / "fixtures"

REQUIRED_SAFEGUARDS = [
    "identity_verification",
    "consent_capture",
    "audit_logs",
    "fraud_controls",
    "human_escalation",
]

READY_LEVELS = {"ready", "verified"}

GUARDRAIL_HEADING = "## Guardrails"
REQUIRED_GUARDRAIL_TERMS = [
    "identity",
    "consent",
    "audit log",
    "fraud control",
    "human escalation",
]


def check_guardrail_text() -> list[str]:
    skill_md = (SKILL_DIR / "SKILL.md").read_text()
    if GUARDRAIL_HEADING not in skill_md:
        return ["SKILL.md has no '## Guardrails' section"]

    guardrails_section = skill_md.split(GUARDRAIL_HEADING, 1)[1].lower()
    failures = []
    if "autonomous payment" not in guardrails_section:
        failures.append("Guardrails section no longer mentions autonomous payments")
    for term in REQUIRED_GUARDRAIL_TERMS:
        if term not in guardrails_section:
            failures.append(
                f"Guardrails section no longer requires '{term}' before recommending "
                "autonomous payments"
            )
    return failures


def decide_recommendation(scenario: dict) -> dict:
    """Codifies the guardrail: a protocol ready for autonomous payment must not
    be recommended unless every required safeguard is present."""
    protocol_readiness = scenario["protocol_readiness"]
    safeguards = scenario["safeguards"]

    ready_protocols = [p for p, level in protocol_readiness.items() if level in READY_LEVELS]
    missing_safeguards = [s for s in REQUIRED_SAFEGUARDS if not safeguards.get(s, False)]

    if not ready_protocols:
        return {"decision": "not_applicable", "missing_safeguards": []}
    if missing_safeguards:
        return {"decision": "do_not_recommend", "missing_safeguards": missing_safeguards}
    return {"decision": "recommend", "missing_safeguards": []}


def run_fixture(scenario_path: Path) -> bool:
    expected_path = scenario_path.with_name(
        scenario_path.name.replace(".scenario.json", ".expected.json")
    )
    scenario = json.loads(scenario_path.read_text())
    expected = json.loads(expected_path.read_text())

    print(f"--- {scenario_path.name} ---")
    result = decide_recommendation(scenario)

    failures = []
    if result["decision"] != expected["expected_decision"]:
        failures.append(
            f"expected decision '{expected['expected_decision']}', got '{result['decision']}'"
        )
    expected_missing = set(expected["expected_missing_safeguards"])
    actual_missing = set(result["missing_safeguards"])
    if actual_missing != expected_missing:
        failures.append(
            f"expected missing safeguards {sorted(expected_missing)}, "
            f"got {sorted(actual_missing)}"
        )

    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print(f"PASS: decision '{result['decision']}' as expected")
    return True


def main() -> int:
    all_passed = True

    print("--- SKILL.md guardrail text ---")
    text_failures = check_guardrail_text()
    if text_failures:
        print("FAIL:")
        for failure in text_failures:
            print(f"  - {failure}")
        all_passed = False
    else:
        print("PASS: Guardrails section still requires identity, consent, audit logs, "
              "fraud controls, and human escalation before autonomous payments")

    fixtures = sorted(FIXTURES_DIR.glob("*.scenario.json"))
    if not fixtures:
        print("No fixtures found under eval/fixtures/", file=sys.stderr)
        return 1

    for scenario_path in fixtures:
        if not run_fixture(scenario_path):
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
