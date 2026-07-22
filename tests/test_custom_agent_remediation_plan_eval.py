import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skills/agentic-commerce/custom-agent-remediation-plan/eval/run.py"


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


if __name__ == "__main__":
    unittest.main()
