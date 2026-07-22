#!/usr/bin/env python3
"""Offline contract and held-out manifest checks for remediation planning."""
import json
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
SKILL = EVAL_DIR.parent / "SKILL.md"
CASES = EVAL_DIR / "held-out-cases.json"
FIXTURES = EVAL_DIR / "fixtures"
RULES = (
    "Use only after verified audit findings identify remediation gaps.",
    "Classify every remediation item as agent, storefront, or shared delivery.",
    "Name an accountable owner, source of truth, observable acceptance test, baseline check, and post-change check for every remediation item.",
    "Return a plan status of `HOLD` with the specific missing controls when required monitoring, ownership, reconciliation, or recovery evidence is absent.",
    "Do not require these operational controls for low- or moderate-risk read-only content and discovery work.",
    "Do not use a remediation plan as authority to execute customer, order, payment, credential, or production changes.",
)
FIELDS = {"id", "split", "fixture_type", "prompt", "expected_skill_usage"}
PLAN_FIELDS = (
    "id",
    "bucket",
    "delivery",
    "owner",
    "evidence_source",
    "baseline_check",
    "acceptance_test",
    "post_change_check",
    "operation_mode",
    "risk_level",
)
OPERATIONAL_CONTROLS = (
    "trace_or_correlation_ids",
    "authorization_evidence",
    "audit_events",
    "idempotency_or_deduplication",
    "reconciliation_checks",
    "retained_failure_evidence",
    "health_signals",
    "alert_thresholds",
    "accountable_operator",
    "human_escalation_path",
    "disable_or_kill_switch",
    "rollback_or_recovery_procedure",
    "safe_dependency_fallback",
    "approval_workflow",
    "policy_grounding",
)


def has_value(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_plan(plan: object) -> dict:
    missing_controls = []
    if not isinstance(plan, list) or not plan:
        return {"status": "HOLD", "missing_controls": ["plan"]}

    for index, item in enumerate(plan):
        item_id = item.get("id", f"item-{index + 1}") if isinstance(item, dict) else f"item-{index + 1}"
        if not isinstance(item, dict):
            missing_controls.append(f"{item_id}.item")
            continue
        for field in PLAN_FIELDS:
            if not has_value(item.get(field)):
                missing_controls.append(f"{item_id}.{field}")
        if has_value(item.get("operation_mode")) and item["operation_mode"] not in {"action_capable", "read_only"}:
            missing_controls.append(f"{item_id}.operation_mode")
        if has_value(item.get("risk_level")) and item["risk_level"] not in {"low", "moderate", "high"}:
            missing_controls.append(f"{item_id}.risk_level")

        controls_required = item.get("operation_mode") == "action_capable" or item.get("risk_level") == "high"
        if not controls_required:
            continue
        controls = item.get("operational_controls")
        if not isinstance(controls, dict):
            missing_controls.extend(f"{item_id}.{field}" for field in OPERATIONAL_CONTROLS)
            continue
        for field in OPERATIONAL_CONTROLS:
            if not has_value(controls.get(field)):
                missing_controls.append(f"{item_id}.{field}")

    return {
        "status": "HOLD" if missing_controls else "READY",
        "missing_controls": missing_controls,
    }


def load_fixture_plan(fixture: dict) -> object:
    if "plan" in fixture:
        return fixture["plan"]
    base_name = fixture.get("base_fixture")
    if not isinstance(base_name, str) or Path(base_name).name != base_name:
        return None
    base = json.loads((FIXTURES / base_name).read_text())
    plan = base.get("plan")
    if not isinstance(plan, list):
        return None
    for item in plan:
        controls = item.get("operational_controls") if isinstance(item, dict) else None
        if isinstance(controls, dict):
            for field in fixture.get("remove_controls", []):
                controls.pop(field, None)
    return plan


def validate_fixtures() -> tuple[list[str], list[str]]:
    failures = []
    reports = []
    for fixture_path in sorted(FIXTURES.glob("*.json")):
        fixture = json.loads(fixture_path.read_text())
        actual = validate_plan(load_fixture_plan(fixture))
        expected = fixture.get("expected_validation")
        missing = ", ".join(actual["missing_controls"])
        detail = f" (missing: {missing})" if missing else ""
        reports.append(f"{fixture_path.stem}: {actual['status']}{detail}")
        if actual != expected:
            failures.append(f"{fixture_path.name} expected {expected}, got {actual}")
    if not reports:
        failures.append("no deterministic remediation-plan fixtures found")
    return failures, reports


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
            elif not all(isinstance(finding, dict) and {"id", "bucket", "evidence_source", "operation_mode", "risk_level"} <= finding.keys() for finding in findings):
                failures.append(f"{case['id']} has invalid audit findings")
        elif not isinstance(case.get("expected_route"), str) or not case["expected_route"]:
            failures.append(f"{case['id']} lacks an authorized route")
    if len(cases) < 10 or any(count < 5 for count in counts.values()):
        failures.append("held-out manifest needs at least five use and five do-not-use cases")
    return failures


def main() -> int:
    failures = validate_contract()
    fixture_failures, reports = validate_fixtures()
    failures.extend(fixture_failures)
    print("\n".join(reports))
    if failures:
        print("FAIL: deterministic custom-agent remediation contract checks")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("PASS: deterministic custom-agent remediation contract checks")
    print("Harness gate: run the isolated enabled/disabled evaluator documented in eval/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
