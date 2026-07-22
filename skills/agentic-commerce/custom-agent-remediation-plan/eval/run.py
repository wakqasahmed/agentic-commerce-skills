#!/usr/bin/env python3
"""Offline contract and held-out manifest checks for remediation planning."""
import json
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
SKILL = EVAL_DIR.parent / "SKILL.md"
CASES = EVAL_DIR / "held-out-cases.json"
RULES = (
    "Use only after verified audit findings identify remediation gaps.",
    "Classify every remediation item as agent, storefront, or shared delivery.",
    "Name an accountable owner, source of truth, observable acceptance test, baseline check, and post-change check for every remediation item.",
    "Do not use a remediation plan as authority to execute customer, order, payment, credential, or production changes.",
    "When a finding requires a customer communication workflow",
    "Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.",
    "Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.",
    "Route overlapping customer flows to `19-lifecycle-orchestration`.",
    "Apply `00-email-marketing-guardrails` to promotional content",
    "An email address identifies a recipient; it does not establish marketing consent.",
    "Never relabel promotional content as transactional.",
)
FIELDS = {"id", "split", "fixture_type", "prompt", "expected_skill_usage"}
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


def validate_contract() -> list[str]:
    failures = []
    try:
        skill = SKILL.read_text()
        cases = json.loads(CASES.read_text())["cases"]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        return [f"failed to load deterministic inputs: {error}"]

    for rule in RULES:
        if rule not in skill:
            failures.append(f"missing remediation guardrail: {rule}")

    counts = {"use": 0, "do_not_use": 0}
    identifiers = set()
    for case in cases:
        missing = FIELDS - case.keys()
        if missing:
            failures.append(f"{case.get('id', '<unknown>')} missing {sorted(missing)}")
            continue
        if case["id"] in identifiers:
            failures.append(f"duplicate case id: {case['id']}")
        identifiers.add(case["id"])
        if case["split"] != "held_out":
            failures.append(f"{case['id']} is not held out")
        if case["fixture_type"] not in {"synthetic", "sanitized_trace"}:
            failures.append(f"{case['id']} has invalid fixture type")
        if case["expected_skill_usage"] not in counts:
            failures.append(f"{case['id']} has invalid skill usage")
        else:
            counts[case["expected_skill_usage"]] += 1
        if case["expected_skill_usage"] == "use":
            findings = case.get("audit_fixture", {}).get("findings")
            if not isinstance(findings, list) or not findings:
                failures.append(f"{case['id']} lacks audit findings")
            elif not all(isinstance(finding, dict) and {"id", "bucket", "evidence_source"} <= finding.keys() for finding in findings):
                failures.append(f"{case['id']} has invalid audit findings")
        elif not isinstance(case.get("expected_route"), str) or not case["expected_route"]:
            failures.append(f"{case['id']} lacks an authorized route")
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
    if len(cases) < 10 or any(count < 5 for count in counts.values()):
        failures.append("held-out manifest needs at least five use and five do-not-use cases")
    return failures


def main() -> int:
    failures = validate_contract()
    if failures:
        print("FAIL: deterministic custom-agent remediation contract checks")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("PASS: deterministic custom-agent remediation contract checks")
    print("Harness gate: run the isolated enabled/disabled evaluator documented in eval/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
