import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = (
    Path("scripts/validate-plugin.py"),
    Path("skills/agentic-commerce/custom-agent-remediation-plan/eval/run.py"),
    Path("skills/agentic-commerce/ecommerce-policy-readiness/eval/run.py"),
)
SKILLS = (
    Path("skills/agentic-commerce/custom-agent-remediation-plan/SKILL.md"),
    Path("skills/agentic-commerce/ecommerce-policy-readiness/SKILL.md"),
)
SCENARIOS = (
    (
        Path("skills/agentic-commerce/custom-agent-remediation-plan/eval/run.py"),
        Path(
            "skills/agentic-commerce/custom-agent-remediation-plan/eval/held-out-cases.json"
        ),
    ),
    (
        Path("skills/agentic-commerce/ecommerce-policy-readiness/eval/run.py"),
        Path(
            "skills/agentic-commerce/ecommerce-policy-readiness/eval/held-out-cases.json"
        ),
    ),
)
REQUIRED_CONTRACT = (
    "When a finding requires a customer communication workflow, Agentic Commerce supplies the authoritative event, verified recipient binding, order or product facts, and permitted action boundaries. Delegate channel execution to the [Email Marketing skills pack](https://github.com/wakqasahmed/email-marketing-skills):",
    "Route verified events for receipts, shipping, cancellations, refunds, accounts, and service status to `14-transactional-service`.",
    "Route optional post-purchase education to `09-post-purchase-customer-success` and verified inventory or price events to `16-inventory-price-alert`.",
    "Route overlapping customer flows to `19-lifecycle-orchestration`.",
    "Apply `00-email-marketing-guardrails` to promotional content and all other delegated channel work.",
    "An email address identifies a recipient; it does not establish marketing consent.",
    "Never relabel promotional content as transactional.",
)


class EmailDelegationContractTest(unittest.TestCase):
    def run_validator(
        self, root: Path, validator: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(root / validator)],
            capture_output=True,
            check=False,
            text=True,
        )

    def copy_repository(self, destination: Path) -> Path:
        mutated_root = destination / "repository"
        shutil.copytree(ROOT, mutated_root, ignore=shutil.ignore_patterns(".git"))
        return mutated_root

    def test_repository_satisfies_email_delegation_contract(self) -> None:
        for validator in VALIDATORS:
            with self.subTest(validator=validator):
                result = self.run_validator(ROOT, validator)

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_each_delegating_skill_preserves_required_contract(self) -> None:
        for skill_path in SKILLS:
            for clause in REQUIRED_CONTRACT:
                with self.subTest(skill=skill_path, clause=clause):
                    with tempfile.TemporaryDirectory() as tmp:
                        mutated_root = self.copy_repository(Path(tmp))
                        mutated_skill_path = mutated_root / skill_path
                        skill = mutated_skill_path.read_text()
                        self.assertEqual(skill.count(clause), 1)
                        replacement = clause.replace("Route", "Consider", 1)
                        if replacement == clause:
                            replacement = clause.replace("authoritative", "unverified", 1)
                        if replacement == clause:
                            replacement = "removed"
                        mutated_skill_path.write_text(
                            skill.replace(clause, replacement, 1)
                        )

                        result = self.run_validator(
                            mutated_root, Path("scripts/validate-plugin.py")
                        )

                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(
                            "Customer communication delegation contract",
                            result.stdout + result.stderr,
                        )

    def test_agentic_pack_cannot_copy_a_delegated_email_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mutated_root = self.copy_repository(Path(tmp))
            copied_skill = (
                mutated_root
                / "skills/agentic-commerce/email-writing/SKILL.md"
            )
            copied_skill.parent.mkdir()
            copied_skill.write_text(
                "---\nname: email-writing\n"
                "description: Agentic Commerce email execution.\n---\n"
            )

            result = self.run_validator(
                mutated_root, Path("scripts/validate-plugin.py")
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Delegated Email Marketing skills must not be copied",
                result.stdout + result.stderr,
            )

    def test_eval_runners_require_authoritative_communication_inputs(self) -> None:
        mutations = {
            "event": "unverified_order_receipt",
            "recipient_binding": "marketing list email address",
            "order_facts": "inferred order facts",
        }
        for runner, manifest_path in SCENARIOS:
            for field, replacement in mutations.items():
                with self.subTest(runner=runner, field=field):
                    with tempfile.TemporaryDirectory() as tmp:
                        mutated_root = self.copy_repository(Path(tmp))
                        mutated_manifest_path = mutated_root / manifest_path
                        manifest = json.loads(mutated_manifest_path.read_text())
                        scenario = next(
                            case
                            for case in manifest["cases"]
                            if case["id"] == "verified-receipt-with-promotion"
                        )
                        scenario["communication_fixture"][field] = replacement
                        mutated_manifest_path.write_text(json.dumps(manifest))

                        result = self.run_validator(mutated_root, runner)

                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(
                            "delegation scenario lacks authoritative Agentic Commerce inputs",
                            result.stdout + result.stderr,
                        )

    def test_eval_runners_enforce_receipt_routing(self) -> None:
        for runner, manifest_path in SCENARIOS:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as tmp:
                    mutated_root = self.copy_repository(Path(tmp))
                    mutated_manifest_path = mutated_root / manifest_path
                    manifest = json.loads(mutated_manifest_path.read_text())
                    scenario = next(
                        case
                        for case in manifest["cases"]
                        if case["id"] == "verified-receipt-with-promotion"
                    )
                    scenario["expected_communication_routes"][
                        "verified_order_receipt"
                    ] = "00-email-marketing-guardrails"
                    mutated_manifest_path.write_text(json.dumps(manifest))

                    result = self.run_validator(mutated_root, runner)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "verified order receipt must route to 14-transactional-service",
                        result.stdout + result.stderr,
                    )

    def test_eval_runners_route_promotion_through_marketing_guardrails(self) -> None:
        for runner, manifest_path in SCENARIOS:
            with self.subTest(runner=runner):
                with tempfile.TemporaryDirectory() as tmp:
                    mutated_root = self.copy_repository(Path(tmp))
                    mutated_manifest_path = mutated_root / manifest_path
                    manifest = json.loads(mutated_manifest_path.read_text())
                    scenario = next(
                        case
                        for case in manifest["cases"]
                        if case["id"] == "verified-receipt-with-promotion"
                    )
                    scenario["expected_communication_routes"][
                        "promotional_content"
                    ] = "14-transactional-service"
                    mutated_manifest_path.write_text(json.dumps(manifest))

                    result = self.run_validator(mutated_root, runner)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "promotional content must route through Email Marketing guardrails",
                        result.stdout + result.stderr,
                    )


if __name__ == "__main__":
    unittest.main()
