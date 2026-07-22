import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "skills/agentic-commerce/product-knowledge-gap-analysis/eval/run.py"
FIXTURES = EVALUATOR.parent / "fixtures"
PLUGIN_VALIDATOR = Path("scripts/validate-plugin.py")
SKILL = Path("skills/agentic-commerce/product-knowledge-gap-analysis/SKILL.md")


class ProductCatalogConsistencyTest(unittest.TestCase):
    def run_evaluator(self, fixture: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(EVALUATOR), "--fixture", str(fixture)],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_mutation(self, fixture_name: str, mutate) -> Path:
        fixture = json.loads((FIXTURES / fixture_name).read_text())
        mutate(fixture)
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        fixture_path = Path(temporary_directory.name) / fixture_name
        fixture_path.write_text(json.dumps(fixture))
        return fixture_path

    def test_variant_mismatch_is_blocking(self) -> None:
        result = self.run_evaluator(FIXTURES / "variant-mismatch.json")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        validation = json.loads(result.stdout)
        self.assertEqual(validation["status"], "BLOCKED")
        self.assertEqual(validation["blocking_facts"], ["variant_identifier"])

    def test_stale_price_and_availability_are_blocking(self) -> None:
        result = self.run_evaluator(FIXTURES / "stale-price-availability.json")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        validation = json.loads(result.stdout)
        self.assertEqual(validation["status"], "BLOCKED")
        self.assertEqual(
            validation["blocking_facts"],
            ["availability", "freshness_indicator", "price"],
        )

    def test_incomplete_mismatch_record_fails(self) -> None:
        fixture = self.write_mutation(
            "variant-mismatch.json",
            lambda data: data["reported_mismatches"][0].pop("remediation_owner"),
        )

        result = self.run_evaluator(fixture)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing remediation_owner", result.stderr)

    def test_checkout_evidence_must_be_non_purchasing_and_verified(self) -> None:
        def make_checkout_unsafe(data: dict) -> None:
            checkout = next(
                evidence
                for evidence in data["evidence"]
                if evidence["surface"] == "checkout"
            )
            checkout["provenance"] = "public"
            checkout["non_purchasing"] = False

        fixture = self.write_mutation("variant-mismatch.json", make_checkout_unsafe)

        result = self.run_evaluator(fixture)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout evidence must be supervised or operator-verified", result.stderr)
        self.assertIn("checkout evidence must be non-purchasing", result.stderr)

    def test_checkout_like_unknown_surface_cannot_bypass_checkout_safety(self) -> None:
        def disguise_checkout_as_public(data: dict) -> None:
            checkout = next(
                evidence
                for evidence in data["evidence"]
                if evidence["surface"] == "checkout"
            )
            checkout["surface"] = "checkout_api"
            checkout["provenance"] = "public"
            checkout["non_purchasing"] = False
            checkout["order_placed"] = True
            data["reported_mismatches"][0]["conflicting_surfaces"][-1]["surface"] = (
                "checkout_api"
            )

        fixture = self.write_mutation("variant-mismatch.json", disguise_checkout_as_public)

        result = self.run_evaluator(fixture)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported evidence surface checkout_api", result.stderr)

    def test_action_changing_mismatches_must_be_blocking(self) -> None:
        action_changing_facts = (
            "product_identifier",
            "variant_identifier",
            "price",
            "currency",
            "availability",
        )

        for fact in action_changing_facts:
            with self.subTest(fact=fact):
                def make_non_blocking(data: dict, mismatch_fact: str = fact) -> None:
                    report = data["reported_mismatches"][0]
                    report["fact"] = mismatch_fact
                    report["severity"] = "NON_BLOCKING"
                    for index, evidence in enumerate(data["evidence"]):
                        evidence["facts"]["variant_identifier"] = "TS-100-BLU-M"
                        evidence["facts"][mismatch_fact] = (
                            "conflicting-value" if index == 3 else "canonical-value"
                        )
                    report["conflicting_surfaces"] = [
                        {
                            "surface": evidence["surface"],
                            "observed_value": evidence["facts"][mismatch_fact],
                        }
                        for evidence in data["evidence"]
                    ]

                fixture = self.write_mutation("variant-mismatch.json", make_non_blocking)

                result = self.run_evaluator(fixture)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"action-changing mismatch {fact} must be BLOCKING",
                    result.stderr,
                )

    def test_plugin_validator_requires_shared_guardrails_for_product_audits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repository"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git"))
            skill_path = root / SKILL
            skill_path.write_text(
                skill_path.read_text().replace(
                    "See `../references/guardrails.md` for shared evidence-provenance and autonomous-action rules.\n",
                    "",
                    1,
                )
            )

            result = subprocess.run(
                ["python3", str(root / PLUGIN_VALIDATOR)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Safety-relevant skill does not reference shared guardrails: product-knowledge-gap-analysis",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
