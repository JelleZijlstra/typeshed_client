from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import check_pycroscope


class TestCheckPycroscope(unittest.TestCase):
    def fake_build(
        self, command: list[str], *, cwd: Path, env: dict[str, str] | None = None
    ) -> None:
        if command[:2] == ["uv", "build"]:
            directory = Path(command[command.index("--out-dir") + 1])
            directory.mkdir()
            (directory / "typeshed_client-2.15.0-py3-none-any.whl").touch()

    def test_default_checks_latest_main_on_all_supported_pythons(self) -> None:
        with patch.object(check_pycroscope, "run", side_effect=self.fake_build) as run:
            self.assertEqual(check_pycroscope.main([]), 0)
        clone = run.call_args_list[0].args[0]
        self.assertIn("--branch=main", clone)
        self.assertIn(check_pycroscope.PYCROSCOPE_REPOSITORY, clone)
        checks = [
            call for call in run.call_args_list if call.args[0][:2] == ["uv", "run"]
        ]
        self.assertEqual(
            [call.args[0][call.args[0].index("--python") + 1] for call in checks],
            list(check_pycroscope.PYTHON_VERSIONS),
        )
        self.assertEqual(
            len({call.kwargs["env"]["UV_PROJECT_ENVIRONMENT"] for call in checks}), 5
        )
        for call in checks:
            command = call.args[0]
            self.assertIn("--locked", command)
            self.assertTrue(command[command.index("--with") + 1].endswith(".whl"))
            self.assertEqual(command[-4:], ["python", "-m", "pytest", "pycroscope"])

    def test_failure_continues_matrix_and_returns_nonzero(self) -> None:
        def fail_one(
            command: list[str], *, cwd: Path, env: dict[str, str] | None = None
        ) -> None:
            self.fake_build(command, cwd=cwd, env=env)
            if command[:2] == ["uv", "run"] and "3.10" in command:
                raise subprocess.CalledProcessError(1, command)

        with patch.object(check_pycroscope, "run", side_effect=fail_one) as run:
            self.assertEqual(
                check_pycroscope.main(["--python", "3.10", "--python", "3.11"]), 1
            )
        self.assertIn("3.11", run.call_args.args[0])

    def test_local_checkout_and_pytest_args_use_isolated_environment(self) -> None:
        with (
            patch.object(check_pycroscope, "run", side_effect=self.fake_build) as run,
            patch.dict(
                os.environ,
                {
                    "PYTHONPATH": "/unrelated/checkout",
                    "UV_PROJECT_ENVIRONMENT": "/existing/venv",
                },
            ),
        ):
            self.assertEqual(
                check_pycroscope.main(
                    [
                        "--pycroscope",
                        ".",
                        "--python",
                        "3.11",
                        "--",
                        "-q",
                        "pycroscope/test_type_object.py",
                    ]
                ),
                0,
            )
        self.assertFalse(
            any(call.args[0][:2] == ["git", "clone"] for call in run.call_args_list)
        )
        check = run.call_args
        self.assertEqual(check.kwargs["cwd"], Path.cwd())
        self.assertNotIn("PYTHONPATH", check.kwargs["env"])
        self.assertNotEqual(
            check.kwargs["env"]["UV_PROJECT_ENVIRONMENT"], "/existing/venv"
        )
        self.assertEqual(check.args[0][-2:], ["-q", "pycroscope/test_type_object.py"])


if __name__ == "__main__":
    unittest.main()
