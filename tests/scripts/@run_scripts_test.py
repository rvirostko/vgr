# pylint: disable=invalid-name

from io import TextIOWrapper
from pathlib import Path

import subprocess
import sys
import pytest

SCRIPTS_DIR = Path(__file__).parent
LOG_DIR = Path(__file__).resolve().parents[2] / "test-log"

def run_subprocess(cmd: list[str]) -> tuple[int, str, str]:
    """Run subprocess, always showing and saving output"""
    cmd_line = [sys.executable, "-m", "vgr"]
    cmd_line.extend(cmd)
    result = subprocess.run(cmd_line, capture_output=True, text=True, check=False)
    # Always print outputs for inspection (requires pytest -s to work?)
    print(result.stdout, end="", file=sys.stdout)
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode, result.stdout, result.stderr

def write_results(f: TextIOWrapper, stdout: str, stderr: str) -> None:
    if stdout:
        f.write("\n--- STDOUT ---\n")
        f.write(stdout)
    if stderr:
        f.write("\n--- STDERR ---\n")
        f.write(stderr)

# -------------------------------
# .vgr FILES
# -------------------------------

@pytest.mark.parametrize(
    "path",
    list(SCRIPTS_DIR.glob("*.vgr")),
    ids=lambda p: p.name,
)
def test_vgr_files(path: Path):
    """Execute .vgr files via --file"""
    LOG_DIR.mkdir(exist_ok=True)
    code, stdout, stderr = run_subprocess(["--file", str(path)])
    with (LOG_DIR / (path.name + ".txt")).open("w", encoding="utf-8") as f: write_results(f, stdout, stderr)
    if "!" in path.name:
        assert code != 0, f"! Expected failure but got success for {path.name!r}"
    else:
        assert code == 0, f"! Expected success but got failure for {path.name!r}"

# -------------------------------
# .vstatement FILES
# -------------------------------

@pytest.mark.parametrize(
    "path",
    list(SCRIPTS_DIR.glob("*.vstatements")),
    ids=lambda p: p.name,
)
def test_vgr_statements(path: Path):
    """Execute line-by-line via --execute"""
    LOG_DIR.mkdir(exist_ok=True)
    with path.open() as fh:
        with (LOG_DIR / (path.name + ".txt")).open("w", encoding="utf-8") as f:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if line and not line.startswith("#"):
                    code, stdout, stderr = run_subprocess(["--execute", line])
                    write_results(f, stdout, stderr)
                    if "!" in path.name:
                        assert code != 0, f"! Expected failure but line succeeded: {path.name!r}:{i}"
                    else:
                        assert code == 0, f"! Expected success but line failed: {path.name!r}:{i}"
