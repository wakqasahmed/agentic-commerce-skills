import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate-sources.py"


class SourceValidatorTest(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(VALIDATOR), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_repository(self, ledger: str, guidance: str = "") -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)
        (root / "SOURCES.md").write_text(ledger)
        (root / "guidance.md").write_text(guidance)
        return root

    def test_checked_in_sources_and_citations_are_valid(self) -> None:
        result = self.run_validator(REPOSITORY_ROOT)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unregistered_citation_fails(self) -> None:
        root = self.write_repository(
            valid_ledger(), "Use the current endpoint. [SRC-MISSING]\n"
        )

        result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unregistered citation SRC-MISSING", result.stdout)

    def test_unused_source_fails(self) -> None:
        root = self.write_repository(valid_ledger())

        result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unused source SRC-TEST", result.stdout)

    def test_malformed_entry_and_missing_review_date_fail(self) -> None:
        root = self.write_repository(
            """# Sources

Freshness window: 180 days.

## SRC-TEST

- Publisher: Example Standards Body
- Official URL: not-a-url
- Supported claim: Example claim.
- Specification version: 1.0
""",
            "Example guidance. [SRC-TEST]\n",
        )

        result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed Official URL", result.stdout)
        self.assertIn("missing Last verified", result.stdout)

    def test_future_last_verified_date_fails(self) -> None:
        root = self.write_repository(
            valid_ledger(last_verified="2099-01-01"),
            "Example guidance. [SRC-TEST]\n",
        )

        result = self.run_validator(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SRC-TEST: Last verified date is in the future", result.stdout)

    def test_malformed_source_headings_fail(self) -> None:
        for source_id in ("src-test", "SRC--TEST"):
            with self.subTest(source_id=source_id):
                root = self.write_repository(
                    valid_ledger().replace("## SRC-TEST", f"## {source_id}"),
                    "Example guidance. [SRC-TEST]\n",
                )

                result = self.run_validator(root)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"malformed source heading {source_id}", result.stdout)

    def test_malformed_citations_fail(self) -> None:
        for source_id in ("src-test", "SRC--TEST"):
            with self.subTest(source_id=source_id):
                root = self.write_repository(
                    valid_ledger(), f"Example guidance. [{source_id}]\n"
                )

                result = self.run_validator(root)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"malformed citation {source_id}", result.stdout)

    def test_stale_source_warns_without_failing(self) -> None:
        root = self.write_repository(
            valid_ledger(last_verified="2020-01-01"),
            "Example guidance. [SRC-TEST]\n",
        )

        result = self.run_validator(root)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("warning: SRC-TEST was last verified", result.stdout)


def valid_ledger(last_verified: str = "2026-07-22") -> str:
    return f"""# Sources

Freshness window: 180 days.

## SRC-TEST

- Publisher: Example Standards Body
- Official URL: https://example.com/specification
- Supported claim: Example claim.
- Specification version: 1.0
- Last verified: {last_verified}
"""


if __name__ == "__main__":
    unittest.main()
