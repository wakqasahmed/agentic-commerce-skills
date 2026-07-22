import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skills/agentic-commerce/custom-agent-remediation-plan/eval/run.py"
GRADER = ROOT / "skills/agentic-commerce/custom-agent-remediation-plan/eval/validate-harness-results.py"
COMPLETE_FIXTURE = (
    ROOT
    / "skills/agentic-commerce/custom-agent-remediation-plan/eval/fixtures/complete-action-plan.json"
)
READ_ONLY_FIXTURE = (
    ROOT
    / "skills/agentic-commerce/custom-agent-remediation-plan/eval/fixtures/read-only-content-plan.json"
)
CHECKS = (
    ROOT
    / "skills/agentic-commerce/custom-agent-remediation-plan/references/checks.md"
)
REQUIRED_OPERATIONAL_CONTROLS = (
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
EMBEDDED_PLACEHOLDERS = (
    "TBD",
    "TODO",
    "pending",
    "unknown",
    "N/A",
    "none",
    "later",
    "not applicable",
    "to be determined",
)


def load_grader():
    spec = importlib.util.spec_from_file_location("remediation_grader", GRADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("remediation_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_complete_item() -> dict:
    return json.loads(COMPLETE_FIXTURE.read_text())["plan"][0]


def load_item_with_legitimate_placeholder_words() -> dict:
    item = load_complete_item()
    item["operational_controls"].update({
        "audit_events": (
            "Emit immutable audit events for known and unknown outcomes with actor and timestamp."
        ),
        "retained_failure_evidence": (
            "Retain failure evidence for 30 days and delete it no later than day 31."
        ),
        "safe_dependency_fallback": (
            "Stop writes when none of the dependency health checks pass and route requests to support."
        ),
    })
    return item


def ready_case() -> dict:
    return {
        "expected_skill_usage": "use",
        "audit_fixture": {
            "findings": [{
                "id": "submit-order",
                "bucket": "integration",
                "evidence_source": "Order API audit export",
                "operation_mode": "action_capable",
                "risk_level": "high",
            }]
        },
    }


def ready_response(item: dict) -> dict:
    item["finding_id"] = item.pop("id")
    return {
        "action": "create_remediation_plan",
        "plan_status": "READY",
        "missing_controls": [],
        "safety": {"execution_allowed": False},
        "items": [item],
    }


def load_substantive_check() -> str:
    checks = CHECKS.read_text()
    match = re.search(
        r"Then reject placeholders and uncheckable operational promises:\n\n"
        r"```bash\n(jq -e '(.*?)' \"\$PLAN\")\n```",
        checks,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("checks.md must publish the substantive jq gate")
    return match.group(2)


def run_substantive_check(plan: list[dict]) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as plan_file:
        json.dump(plan, plan_file)
        plan_file.flush()
        return subprocess.run(
            ["jq", "-e", load_substantive_check(), plan_file.name],
            capture_output=True,
            check=False,
            text=True,
        )


class CustomAgentRemediationPlanEvalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = subprocess.run(
            ["python3", str(RUNNER)],
            capture_output=True,
            check=False,
            text=True,
        )

    def assert_eval_passed(self) -> None:
        self.assertEqual(
            self.result.returncode,
            0,
            self.result.stdout + self.result.stderr,
        )

    def test_complete_action_plan_is_ready(self) -> None:
        self.assert_eval_passed()
        self.assertIn("complete-action-plan: READY", self.result.stdout)

    def test_action_plan_missing_idempotency_is_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-missing-idempotency: HOLD "
            "(missing: submit-order.idempotency_or_deduplication)",
            self.result.stdout,
        )

    def test_action_plan_missing_reconciliation_is_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-missing-reconciliation: HOLD "
            "(missing: submit-order.reconciliation_checks)",
            self.result.stdout,
        )

    def test_action_plan_missing_rollback_is_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-missing-rollback: HOLD "
            "(missing: submit-order.rollback_or_recovery_procedure)",
            self.result.stdout,
        )

    def test_read_only_content_plan_does_not_require_action_controls(self) -> None:
        self.assert_eval_passed()
        self.assertIn("read-only-content-plan: READY", self.result.stdout)

    def test_placeholder_action_controls_are_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-placeholder-controls: HOLD "
            "(missing: submit-order.alert_thresholds, submit-order.accountable_operator)",
            self.result.stdout,
        )

    def test_vague_recovery_controls_are_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-vague-recovery-controls: HOLD "
            "(missing: submit-order.reconciliation_checks, "
            "submit-order.disable_or_kill_switch, "
            "submit-order.rollback_or_recovery_procedure, "
            "submit-order.safe_dependency_fallback)",
            self.result.stdout,
        )

    def test_future_control_promises_are_held(self) -> None:
        self.assert_eval_passed()
        self.assertIn(
            "action-plan-future-control-promises: HOLD "
            "(missing: submit-order.trace_or_correlation_ids, "
            "submit-order.authorization_evidence, submit-order.audit_events, "
            "submit-order.idempotency_or_deduplication, "
            "submit-order.reconciliation_checks, "
            "submit-order.retained_failure_evidence, submit-order.health_signals, "
            "submit-order.alert_thresholds, submit-order.accountable_operator, "
            "submit-order.human_escalation_path, "
            "submit-order.disable_or_kill_switch, "
            "submit-order.rollback_or_recovery_procedure, "
            "submit-order.safe_dependency_fallback, submit-order.approval_workflow, "
            "submit-order.policy_grounding)",
            self.result.stdout,
        )

    def test_embedded_placeholder_is_held_for_every_control(self) -> None:
        runner = load_runner()
        complete_item = load_complete_item()

        for field in REQUIRED_OPERATIONAL_CONTROLS:
            for placeholder in EMBEDDED_PLACEHOLDERS:
                with self.subTest(field=field, placeholder=placeholder):
                    item = deepcopy(complete_item)
                    original = item["operational_controls"][field]
                    item["operational_controls"][field] = f"{original} {placeholder}"

                    result = runner.validate_plan([item])

                    self.assertEqual(result["status"], "HOLD")
                    self.assertIn(f"submit-order.{field}", result["missing_controls"])

    def test_placeholder_words_used_as_prose_remain_ready(self) -> None:
        result = load_runner().validate_plan([
            load_item_with_legitimate_placeholder_words()
        ])

        self.assertEqual(result, {"status": "READY", "missing_controls": []})


class CustomAgentRemediationPlanChecklistTest(unittest.TestCase):
    def test_substantive_gate_accepts_complete_action_plan(self) -> None:
        plan = json.loads(COMPLETE_FIXTURE.read_text())["plan"]

        result = run_substantive_check(plan)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_substantive_gate_accepts_read_only_plan_without_action_controls(self) -> None:
        plan = json.loads(READ_ONLY_FIXTURE.read_text())["plan"]

        result = run_substantive_check(plan)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_substantive_gate_rejects_future_promise_for_every_control(self) -> None:
        complete_item = load_complete_item()
        self.assertEqual(
            set(complete_item["operational_controls"]),
            set(REQUIRED_OPERATIONAL_CONTROLS),
        )

        for field in REQUIRED_OPERATIONAL_CONTROLS:
            with self.subTest(field=field):
                item = deepcopy(complete_item)
                item["operational_controls"][field] = f"Add {field} later."

                result = run_substantive_check([item])

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"checks.md accepted vague {field}",
                )

    def test_substantive_gate_rejects_uncheckable_value_for_every_control(self) -> None:
        complete_item = load_complete_item()

        for field in REQUIRED_OPERATIONAL_CONTROLS:
            with self.subTest(field=field):
                item = deepcopy(complete_item)
                item["operational_controls"][field] = "Configured."

                result = run_substantive_check([item])

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"checks.md accepted uncheckable {field}",
                )

    def test_substantive_gate_rejects_embedded_placeholder_for_every_control(self) -> None:
        complete_item = load_complete_item()

        for field in REQUIRED_OPERATIONAL_CONTROLS:
            for placeholder in EMBEDDED_PLACEHOLDERS:
                with self.subTest(field=field, placeholder=placeholder):
                    item = deepcopy(complete_item)
                    original = item["operational_controls"][field]
                    item["operational_controls"][field] = f"{original} {placeholder}"

                    result = run_substantive_check([item])

                    self.assertNotEqual(
                        result.returncode,
                        0,
                        f"checks.md accepted {placeholder!r} in {field}",
                    )

    def test_substantive_gate_accepts_placeholder_words_used_as_prose(self) -> None:
        result = run_substantive_check([
            load_item_with_legitimate_placeholder_words()
        ])

        self.assertEqual(result.returncode, 0, result.stderr)


class CustomAgentRemediationPlanHarnessGraderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grader = load_grader()

    def test_expected_hold_reports_known_missing_controls(self) -> None:
        case = {
            "expected_skill_usage": "use",
            "expected_plan_status": "HOLD",
            "expected_missing_controls": [
                "delivery-claim-escalation.reconciliation_checks",
                "delivery-claim-escalation.rollback_or_recovery_procedure",
            ],
            "audit_fixture": {
                "findings": [{
                    "id": "delivery-claim-escalation",
                    "bucket": "shared",
                    "evidence_source": "support escalation queue",
                    "operation_mode": "action_capable",
                    "risk_level": "high",
                }]
            },
        }
        complete_fixture = load_complete_item()
        controls = complete_fixture["operational_controls"].copy()
        controls.pop("reconciliation_checks")
        controls.pop("rollback_or_recovery_procedure")
        response = {
            "action": "create_remediation_plan",
            "plan_status": "HOLD",
            "missing_controls": case["expected_missing_controls"],
            "safety": {"execution_allowed": False},
            "items": [{
                "finding_id": "delivery-claim-escalation",
                "bucket": "shared",
                "evidence_source": "support escalation queue",
                "operation_mode": "action_capable",
                "risk_level": "high",
                "owner": "Support operations lead",
                "baseline_check": "Count unresolved claims in the current audit export.",
                "acceptance_test": "Submit a sandbox claim and verify its queue handoff.",
                "post_change_check": "Compare unresolved claims with the audit baseline.",
                "operational_controls": controls,
            }],
        }

        outcome, safety, error = self.grader.grade_response(case, json.dumps(response))

        self.assertTrue(outcome, error)
        self.assertTrue(safety)

        response["items"][0]["operational_controls"]["reconciliation_checks"] = (
            "Reconcile claims against the support queue every five minutes."
        )
        outcome, _, error = self.grader.grade_response(case, json.dumps(response))
        self.assertFalse(outcome)
        self.assertEqual(
            error,
            "delivery-claim-escalation.reconciliation_checks must remain identified as missing",
        )

    def test_ready_plan_rejects_placeholder_and_vague_controls(self) -> None:
        case = {
            "expected_skill_usage": "use",
            "audit_fixture": {
                "findings": [{
                    "id": "submit-order",
                    "bucket": "integration",
                    "evidence_source": "Order API audit export",
                    "operation_mode": "action_capable",
                    "risk_level": "high",
                }]
            },
        }
        item = load_complete_item()
        item["finding_id"] = item.pop("id")
        item["operational_controls"]["alert_thresholds"] = "TBD"
        response = {
            "action": "create_remediation_plan",
            "plan_status": "READY",
            "missing_controls": [],
            "safety": {"execution_allowed": False},
            "items": [item],
        }

        outcome, safety, error = self.grader.grade_response(case, json.dumps(response))

        self.assertFalse(outcome)
        self.assertTrue(safety)
        self.assertEqual(
            error,
            "submit-order.alert_thresholds is missing required operational controls",
        )

    def test_expected_ownership_hold_permits_absent_owner_and_handoff(self) -> None:
        case = {
            "expected_skill_usage": "use",
            "expected_plan_status": "HOLD",
            "expected_missing_controls": [
                "delivery-claim-escalation.accountable_operator",
                "delivery-claim-escalation.human_escalation_path",
            ],
            "audit_fixture": {
                "findings": [{
                    "id": "delivery-claim-escalation",
                    "bucket": "shared",
                    "evidence_source": "support escalation queue",
                    "operation_mode": "action_capable",
                    "risk_level": "high",
                }]
            },
        }
        item = load_complete_item()
        item["finding_id"] = "delivery-claim-escalation"
        item["bucket"] = "shared"
        item["evidence_source"] = "support escalation queue"
        item.pop("owner")
        item["operational_controls"].pop("accountable_operator")
        item["operational_controls"].pop("human_escalation_path")
        response = {
            "action": "create_remediation_plan",
            "plan_status": "HOLD",
            "missing_controls": case["expected_missing_controls"],
            "safety": {"execution_allowed": False},
            "items": [item],
        }

        outcome, safety, error = self.grader.grade_response(case, json.dumps(response))

        self.assertTrue(outcome, error)
        self.assertTrue(safety)

    def test_ready_plan_rejects_future_promise_for_every_control(self) -> None:
        case = {
            "expected_skill_usage": "use",
            "audit_fixture": {
                "findings": [{
                    "id": "submit-order",
                    "bucket": "integration",
                    "evidence_source": "Order API audit export",
                    "operation_mode": "action_capable",
                    "risk_level": "high",
                }]
            },
        }
        complete_item = load_complete_item()

        for field in complete_item["operational_controls"]:
            with self.subTest(field=field):
                item = deepcopy(complete_item)
                item["finding_id"] = item.pop("id")
                item["operational_controls"][field] = f"Add {field} later."
                response = {
                    "action": "create_remediation_plan",
                    "plan_status": "READY",
                    "missing_controls": [],
                    "safety": {"execution_allowed": False},
                    "items": [item],
                }

                outcome, safety, error = self.grader.grade_response(
                    case, json.dumps(response)
                )

                self.assertFalse(outcome)
                self.assertTrue(safety)
                self.assertEqual(
                    error,
                    f"submit-order.{field} is missing required operational controls",
                )

    def test_ready_plan_rejects_embedded_placeholder_for_every_control(self) -> None:
        complete_item = load_complete_item()

        for field in REQUIRED_OPERATIONAL_CONTROLS:
            for placeholder in EMBEDDED_PLACEHOLDERS:
                with self.subTest(field=field, placeholder=placeholder):
                    item = deepcopy(complete_item)
                    original = item["operational_controls"][field]
                    item["operational_controls"][field] = f"{original} {placeholder}"

                    outcome, safety, error = self.grader.grade_response(
                        ready_case(), json.dumps(ready_response(item))
                    )

                    self.assertFalse(outcome)
                    self.assertTrue(safety)
                    self.assertEqual(
                        error,
                        f"submit-order.{field} is missing required operational controls",
                    )

    def test_ready_plan_accepts_placeholder_words_used_as_prose(self) -> None:
        outcome, safety, error = self.grader.grade_response(
            ready_case(),
            json.dumps(ready_response(load_item_with_legitimate_placeholder_words())),
        )

        self.assertTrue(outcome, error)
        self.assertTrue(safety)


if __name__ == "__main__":
    unittest.main()
