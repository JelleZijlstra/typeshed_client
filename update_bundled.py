#!/usr/bin/env python3

from pathlib import Path
import shutil
import subprocess
import tempfile


def update_bundled() -> None:
    ts_client = Path("typeshed_client")
    assert (
        ts_client.is_dir()
    ), "this script must be run at the root of the typeshed_client repository"
    bundled_ts_dir = ts_client / "typeshed"
    if bundled_ts_dir.exists():
        shutil.rmtree(bundled_ts_dir)
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        subprocess.check_call(
            ["git", "clone", "https://github.com/python/typeshed.git", "--depth", "1"],
            cwd=temp_dir,
        )
        shutil.copytree(temp_dir / "typeshed" / "stdlib", bundled_ts_dir)
    subprocess.check_call(["git", "add", str(bundled_ts_dir)])


if __name__ == "__main__":
    update_bundled()
