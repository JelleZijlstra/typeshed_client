#!/usr/bin/env python3
"""Test the current typeshed-client wheel against latest pycroscope."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path

PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")
PYCROSCOPE_REPOSITORY = "https://github.com/JelleZijlstra/pycroscope.git"


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print(f"+ {shlex.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        action="append",
        help="Python version or executable to test (repeatable; default: 3.10-3.14)",
    )
    parser.add_argument(
        "--pycroscope",
        type=Path,
        help="Use an existing pycroscope checkout instead of cloning latest main",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional pytest arguments after --",
    )
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parent
    pytest_args = args.pytest_args
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    if not pytest_args:
        pytest_args = ["pycroscope"]

    with tempfile.TemporaryDirectory(prefix="typeshed-client-pycroscope-") as directory:
        scratch = Path(directory)
        checkout = (
            args.pycroscope.resolve() if args.pycroscope else scratch / "pycroscope"
        )
        if args.pycroscope is None:
            run(
                [
                    "git",
                    "clone",
                    "--depth=1",
                    "--branch=main",
                    PYCROSCOPE_REPOSITORY,
                    str(checkout),
                ],
                cwd=scratch,
            )
        run(["git", "log", "-1", "--format=%H %s"], cwd=checkout)
        wheels = scratch / "wheels"
        run(
            ["uv", "build", "--wheel", "--out-dir", str(wheels), str(repo)], cwd=scratch
        )
        [wheel] = wheels.glob("*.whl")
        failed = []
        for index, python in enumerate(args.python or PYTHON_VERSIONS):
            print(
                f"\nChecking pycroscope with Python {python} and {wheel.name}",
                flush=True,
            )
            env = dict(
                os.environ, UV_PROJECT_ENVIRONMENT=str(scratch / f"venv-{index}")
            )
            # Do not let a caller's checkout shadow the wheel under test.
            env.pop("PYTHONPATH", None)
            try:
                run(
                    [
                        "uv",
                        "run",
                        "--locked",
                        "--python",
                        python,
                        "--extra",
                        "tests",
                        "--with",
                        str(wheel),
                        "python",
                        "-m",
                        "pytest",
                        *pytest_args,
                    ],
                    cwd=checkout,
                    env=env,
                )
            except subprocess.CalledProcessError:
                failed.append(python)
        if failed:
            print(
                f"\nPycroscope compatibility failed for: {', '.join(failed)}",
                flush=True,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
