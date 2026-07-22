#!/usr/bin/env python3
"""Offline contract checks for the product-knowledge outcome eval."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
SKILL = EVAL_DIR.parent / "SKILL.md"
CASES = EVAL_DIR / "held-out-cases.json"
FIXTURES = EVAL_DIR / "fixtures"
RULES = (
    "Treat facts without a visible source as unknown; never infer ingredients, compatibility, contraindications, or safety claims.",
    "Separate template-level fixes from product-specific enrichment.",
    "Do not alter catalog data or make product claims; identify the source of truth and route remediation to its owner.",
    "Treat raw HTML, rendered content, JSON-LD, and public feeds as public-signal evidence. Never present them as proof that checkout values match.",
    "Report checkout consistency only when supported by a supervised non-purchasing check or verified operator-provided evidence.",
    "Never place an order to complete the audit.",
)
FIELDS = {"id", "split", "prompt", "expected_skill_usage", "catalog", "feed", "expected_artifact"}
PUBLIC_SURFACES = {
    "raw_html",
    "rendered_product_content",
    "json_ld",
    "operator_public_feed",
}
EVIDENCE_SURFACES = PUBLIC_SURFACES | {"checkout"}
FACTS = {
    "product_identifier",
    "variant_identifier",
    "price",
    "currency",
    "availability",
    "sale_timing",
    "fulfillment_state",
    "freshness_indicator",
}
ACTION_CHANGING_FACTS = {
    "product_identifier",
    "variant_identifier",
    "price",
    "currency",
    "availability",
}
MISMATCH_FIELDS = {
    "fact",
    "severity",
    "conflicting_surfaces",
    "evidence_timestamp",
    "failure_mode",
    "proposed_source_of_truth",
    "remediation_owner",
}
CHECKOUT_PROVENANCE = {"supervised_checkout", "verified_operator_evidence"}


def missing_rules(skill: str) -> list[str]:
    return [rule for rule in RULES if rule not in skill]


def has_value(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_timestamp(value: object) -> bool:
    if not has_value(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def observed_mismatches(evidence: list[dict]) -> dict[str, list[dict]]:
    observations = {fact: [] for fact in FACTS}
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("facts"), dict):
            continue
        for fact in FACTS:
            if fact in item["facts"]:
                observations[fact].append(
                    {"surface": item.get("surface"), "observed_value": item["facts"][fact]}
                )
    return {
        fact: values
        for fact, values in observations.items()
        if len({json.dumps(item["observed_value"], sort_keys=True) for item in values}) > 1
    }


def validate_catalog_fixture(fixture: object) -> tuple[dict, list[str]]:
    errors = []
    if not isinstance(fixture, dict):
        return {"status": "INVALID", "blocking_facts": []}, ["fixture must be an object"]

    evidence = fixture.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return {"status": "INVALID", "blocking_facts": []}, ["evidence must be a non-empty list"]

    seen_surfaces = set()
    for index, item in enumerate(evidence):
        label = (
            item.get("surface", f"evidence[{index}]")
            if isinstance(item, dict)
            else f"evidence[{index}]"
        )
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        surface = item.get("surface")
        if not has_value(surface):
            errors.append(f"{label} missing surface")
        elif surface not in EVIDENCE_SURFACES:
            errors.append(f"unsupported evidence surface {surface}")
        elif surface in seen_surfaces:
            errors.append(f"duplicate evidence surface {surface}")
        else:
            seen_surfaces.add(surface)
        if not is_timestamp(item.get("observed_at")):
            errors.append(f"{label} missing valid observed_at")
        facts = item.get("facts")
        if not isinstance(facts, dict):
            errors.append(f"{label} missing facts")
        else:
            for fact in sorted(FACTS - facts.keys()):
                errors.append(f"{label} missing fact {fact}")
        if surface == "checkout":
            if item.get("provenance") not in CHECKOUT_PROVENANCE:
                errors.append("checkout evidence must be supervised or operator-verified")
            if item.get("non_purchasing") is not True or item.get("order_placed") is not False:
                errors.append("checkout evidence must be non-purchasing and never place an order")
        elif item.get("provenance") != "public":
            errors.append(f"{label} evidence must be labeled public")

    for surface in sorted(PUBLIC_SURFACES - seen_surfaces):
        errors.append(f"missing representative surface {surface}")

    detected = observed_mismatches(evidence)
    reported = fixture.get("reported_mismatches")
    if not isinstance(reported, list):
        reported = []
        errors.append("reported_mismatches must be a list")

    reports_by_fact = {}
    blocking_facts = []
    for index, report in enumerate(reported):
        label = f"reported_mismatches[{index}]"
        if not isinstance(report, dict):
            errors.append(f"{label} must be an object")
            continue
        fact = report.get("fact")
        if not has_value(fact):
            errors.append(f"{label} missing fact")
        elif fact in reports_by_fact:
            errors.append(f"duplicate mismatch report for {fact}")
        else:
            reports_by_fact[fact] = report
        for field in sorted(MISMATCH_FIELDS - report.keys()):
            errors.append(f"{label} missing {field}")
        for field in ("failure_mode", "proposed_source_of_truth", "remediation_owner"):
            if field in report and not has_value(report[field]):
                errors.append(f"{label} has empty {field}")
        if not is_timestamp(report.get("evidence_timestamp")):
            errors.append(f"{label} missing valid evidence_timestamp")
        if report.get("severity") not in {"BLOCKING", "NON_BLOCKING"}:
            errors.append(f"{label} has invalid severity")
        elif report["severity"] == "BLOCKING" and isinstance(fact, str):
            blocking_facts.append(fact)
        elif fact in ACTION_CHANGING_FACTS:
            errors.append(f"action-changing mismatch {fact} must be BLOCKING")
        if not has_value(fact):
            continue
        if fact not in detected:
            errors.append(f"{label} does not describe an observed mismatch")
        elif report.get("conflicting_surfaces") != detected[fact]:
            errors.append(f"{label} must record every conflicting surface and observed value")

    for fact in sorted(detected.keys() - reports_by_fact.keys()):
        errors.append(f"unreported mismatch for {fact}")

    return {
        "status": "BLOCKED" if blocking_facts else "CLEAR",
        "blocking_facts": sorted(blocking_facts),
    }, errors


def validate_catalog_fixtures() -> tuple[list[str], list[str]]:
    failures = []
    reports = []
    fixture_paths = sorted(FIXTURES.glob("*.json"))
    if not fixture_paths:
        return ["no catalog consistency fixtures found"], reports
    for fixture_path in fixture_paths:
        fixture = json.loads(fixture_path.read_text())
        actual, errors = validate_catalog_fixture(fixture)
        reports.append(f"{fixture_path.stem}: {actual['status']}")
        failures.extend(f"{fixture_path.name}: {error}" for error in errors)
        if actual != fixture.get("expected_validation"):
            failures.append(
                f"{fixture_path.name}: expected {fixture.get('expected_validation')}, got {actual}"
            )
    return failures, reports


def validate_contract() -> list[str]:
    failures = []
    skill = SKILL.read_text()
    for rule in RULES:
        if rule in missing_rules(skill):
            failures.append(f"missing product-knowledge guardrail: {rule}")
        elif rule not in missing_rules(skill.replace(rule, "removed", 1)):
            failures.append(f"mutation not rejected: {rule}")
    cases = json.loads(CASES.read_text()).get("cases", [])
    counts, identifiers = {"use": 0, "do_not_use": 0}, set()
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
        if case["expected_skill_usage"] in counts:
            counts[case["expected_skill_usage"]] += 1
        else:
            failures.append(f"{case['id']} has invalid skill usage")
        artifact = case["expected_artifact"]
        if not isinstance(case["catalog"], list) or not isinstance(case["feed"], dict):
            failures.append(f"{case['id']} lacks realistic catalog/feed input")
        if not isinstance(artifact, dict) or not isinstance(artifact.get("decision"), str):
            failures.append(f"{case['id']} lacks a machine-checkable artifact")
        elif artifact["decision"] == "analyze":
            gaps = artifact.get("observed_gaps")
            if (not isinstance(gaps, list) or not gaps
                    or any(not isinstance(gap, dict) or set(gap) != {"sku", "field", "source", "remediation"} for gap in gaps)):
                failures.append(f"{case['id']} lacks observed product gap artifacts")
        elif artifact["decision"] == "route":
            if artifact.get("observed_gaps") != [] or not artifact.get("route") or not artifact.get("non_use_reason"):
                failures.append(f"{case['id']} lacks non-use routing artifact")
        else:
            failures.append(f"{case['id']} has invalid artifact decision")
    if len(cases) < 10 or any(count < 5 for count in counts.values()):
        failures.append("held-out manifest needs at least five use and five do-not-use cases")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    if args.fixture:
        fixture = json.loads(args.fixture.read_text())
        validation, errors = validate_catalog_fixture(fixture)
        if errors:
            print("\n".join(f"error: {error}" for error in errors), file=sys.stderr)
            return 1
        print(json.dumps(validation, sort_keys=True))
        return 0

    failures = validate_contract()
    fixture_failures, reports = validate_catalog_fixtures()
    failures.extend(fixture_failures)
    print("\n".join(reports))
    if failures:
        print("FAIL: deterministic product-knowledge contract checks")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("PASS: deterministic product-knowledge contract checks")
    print("Harness gate: run the isolated enabled/disabled evaluator documented in eval/README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
