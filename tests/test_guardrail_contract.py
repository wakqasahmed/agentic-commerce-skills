import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("scripts/validate-plugin.py")
GUARDRAILS = Path("skills/agentic-commerce/references/guardrails.md")
SEO_AUDIT = Path("skills/agentic-commerce/seo-aeo-geo-audit/SKILL.md")
SEO_CHECKS = Path("skills/agentic-commerce/seo-aeo-geo-audit/references/checks.md")
SEO_CONTRACT = Path("skills/agentic-commerce/seo-aeo-geo-audit/eval/check-contract.py")
MUTATIONS = json.loads(
    (ROOT / "tests/fixtures/guardrail-mutations.json").read_text()
)


class RepositoryContractTest(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(root / VALIDATOR)],
            capture_output=True,
            check=False,
            text=True,
        )

    def run_seo_contract(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(root / SEO_CONTRACT)],
            capture_output=True,
            check=False,
            text=True,
        )

    def test_repository_satisfies_guardrail_contract(self) -> None:
        result = self.run_validator(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_plugin_rejects_new_protocol_specific_top_level_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mutated_root = Path(tmp) / "repository"
            shutil.copytree(ROOT, mutated_root, ignore=shutil.ignore_patterns(".git"))
            plugin_path = mutated_root / ".claude-plugin/plugin.json"
            plugin = json.loads(plugin_path.read_text())
            plugin["skills"].append("./skills/agentic-commerce/ap2-readiness")
            skill_path = mutated_root / "skills/agentic-commerce/ap2-readiness"
            skill_path.mkdir()
            (skill_path / "SKILL.md").write_text("---\nname: ap2-readiness\n---\n")
            plugin_path.write_text(json.dumps(plugin))

            result = self.run_validator(mutated_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plugin skill set must preserve public names", result.stdout + result.stderr)

    def test_guardrail_mutations_fail_validation(self) -> None:
        for mutation in MUTATIONS:
            with self.subTest(mutation=mutation["name"]):
                with tempfile.TemporaryDirectory() as tmp:
                    mutated_root = Path(tmp) / "repository"
                    shutil.copytree(ROOT, mutated_root, ignore=shutil.ignore_patterns(".git"))
                    guardrails_path = mutated_root / GUARDRAILS
                    guardrails = guardrails_path.read_text()
                    self.assertEqual(guardrails.count(mutation["old"]), 1)
                    guardrails_path.write_text(
                        guardrails.replace(mutation["old"], mutation["new"], 1)
                    )

                    result = self.run_validator(mutated_root)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        mutation["expected_error"],
                        result.stdout + result.stderr,
                    )

    def test_unknown_ai_visibility_delegation_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mutated_root = Path(tmp) / "repository"
            shutil.copytree(ROOT, mutated_root, ignore=shutil.ignore_patterns(".git"))
            skill_path = mutated_root / SEO_AUDIT
            skill = skill_path.read_text()
            skill_path.write_text(
                skill.replace(
                    "`robots-ai-crawler-audit`",
                    "`invented-crawler-audit`",
                    1,
                )
            )

            result = self.run_validator(mutated_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "unknown AI Visibility delegation: invented-crawler-audit",
                result.stdout + result.stderr,
            )

    def test_missing_seo_checks_reference_fails_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mutated_root = Path(tmp) / "repository"
            shutil.copytree(ROOT, mutated_root, ignore=shutil.ignore_patterns(".git"))
            (mutated_root / SEO_CHECKS).unlink()

            result = self.run_seo_contract(mutated_root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "missing SEO/AEO/GEO checks reference",
                result.stdout + result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
