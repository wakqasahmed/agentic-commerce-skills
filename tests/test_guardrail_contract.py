import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("scripts/validate-plugin.py")
GUARDRAILS = Path("skills/agentic-commerce/references/guardrails.md")
MUTATIONS = json.loads(
    (ROOT / "tests/fixtures/guardrail-mutations.json").read_text()
)


class GuardrailContractTest(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(root / VALIDATOR)],
            capture_output=True,
            check=False,
            text=True,
        )

    def test_repository_satisfies_guardrail_contract(self) -> None:
        result = self.run_validator(ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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


if __name__ == "__main__":
    unittest.main()
