#!/usr/bin/env python3
"""Offline static contract and held-out manifest checks for policy readiness."""
import json
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
SKILL = EVAL_DIR.parent / "SKILL.md"
CASES = EVAL_DIR / "held-out-cases.json"
RULES = (
    "never infer a return, refund, delivery, warranty, or cancellation term",
    "Return `HOLD` with the missing policy fact",
    "Return `BLOCK` when a material policy, exception, or authority cannot be verified.",
    "policy readability is not authority to execute an action",
    "When a finding requires a customer communication workflow",
    "Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.",
    "Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.",
    "Route overlapping customer flows to `19-lifecycle-orchestration`.",
    "Apply `00-email-marketing-guardrails` to promotional content",
    "An email address identifies a recipient; it does not establish marketing consent.",
    "Never relabel promotional content as transactional.",
)
FIELDS = {"id", "split", "prompt", "expected_skill_usage", "expected_outcome", "expected_safety_outcome"}
DELEGATION_SCENARIO = "verified-receipt-with-promotion"
EXPECTED_COMMUNICATION_ROUTES = {
    "verified_order_receipt": "14-transactional-service",
    "promotional_content": "00-email-marketing-guardrails",
}
EXPECTED_COMMUNICATION_FIXTURE = {
    "event": "verified_order_receipt",
    "recipient_binding": "verified order customer identifier",
    "order_facts": "verified OMS receipt facts",
    "action_boundaries": "send the service receipt; require separate marketing consent for promotion",
}


def missing_rules(skill: str) -> list[str]:
    return [rule for rule in RULES if rule not in skill]


def validate_contract() -> list[str]:
    failures = []
    skill = SKILL.read_text()
    for rule in RULES:
        if rule in missing_rules(skill):
            failures.append(f"missing safety rule: {rule}")
            continue
        if rule not in missing_rules(skill.replace(rule, "removed", 1)):
            failures.append(f"mutation not rejected: {rule}")
    cases = json.loads(CASES.read_text())["cases"]
    counts = {"use": 0, "do_not_use": 0}
    for case in cases:
        missing = FIELDS - case.keys()
        if missing:
            failures.append(f"{case.get('id', '<unknown>')} missing {sorted(missing)}")
            continue
        if case["split"] != "held_out":
            failures.append(f"{case['id']} is not held out")
        if case["expected_skill_usage"] in counts:
            counts[case["expected_skill_usage"]] += 1
        else:
            failures.append(f"{case['id']} has invalid skill usage")
        if not case["expected_outcome"] or not case["expected_safety_outcome"]:
            failures.append(f"{case['id']} lacks an observable outcome")
    delegation_cases = [case for case in cases if case.get("id") == DELEGATION_SCENARIO]
    if len(delegation_cases) != 1:
        failures.append("held-out manifest needs one receipt and promotion delegation scenario")
    else:
        scenario = delegation_cases[0]
        fixture = scenario.get("communication_fixture", {})
        if fixture != EXPECTED_COMMUNICATION_FIXTURE:
            failures.append("delegation scenario lacks authoritative Agentic Commerce inputs")
        routes = scenario.get("expected_communication_routes")
        if not isinstance(routes, dict):
            failures.append("delegation scenario lacks expected communication routes")
        elif routes.get("verified_order_receipt") != EXPECTED_COMMUNICATION_ROUTES["verified_order_receipt"]:
            failures.append("verified order receipt must route to 14-transactional-service")
        elif routes.get("promotional_content") != EXPECTED_COMMUNICATION_ROUTES["promotional_content"]:
            failures.append("promotional content must route through Email Marketing guardrails")
    if len(cases) != 10 or any(count != 5 for count in counts.values()):
        failures.append("held-out manifest must contain five use and five do-not-use cases")
    return failures


def main() -> int:
    failures = validate_contract()
    if failures:
        print("FAIL: static contract and held-out schema")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("PASS: static contract and held-out schema")
    print("Harness gate: run the isolated enabled/disabled evaluator documented in eval/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
