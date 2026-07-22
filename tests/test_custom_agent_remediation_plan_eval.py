import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skills/agentic-commerce/custom-agent-remediation-plan/eval/run.py"
GRADER = ROOT / "skills/agentic-commerce/custom-agent-remediation-plan/eval/validate-harness-results.py"
COMPLETE_FIXTURE = (
    ROOT
    / "skills/agentic-commerce/custom-agent-remediation-plan/eval/fixtures/complete-action-plan.json"
)


def load_grader():
    spec = importlib.util.spec_from_file_location("remediation_grader", GRADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_complete_item() -> dict:
    return json.loads(COMPLETE_FIXTURE.read_text())["plan"][0]


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


if __name__ == "__main__":
    unittest.main()
