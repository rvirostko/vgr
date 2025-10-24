# pylint: disable=invalid-name

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
    LOG_DIR.mkdir(exist_ok=True)
    # sanitize filename: join command tokens, replace os separators
    log_name = "_".join(Path(part).stem if Path(part).suffix else part for part in cmd)
    log_name = log_name.removeprefix("--file_").removeprefix("--source_")
    log_path = LOG_DIR / (log_name + ".txt")
    with log_path.open("w", encoding="utf-8") as f:
        if result.stdout:
            f.write("--- STDOUT ---\n")
            f.write(result.stdout)
        if result.stderr:
            f.write("--- STDERR ---\n")
            f.write(result.stderr)
    return result.returncode, result.stdout, result.stderr

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
    code, _, _ = run_subprocess(["--file", str(path)])
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
    """Execute line-by-line via --source"""
    with path.open() as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if line and not line.startswith("#"):
                code, _, _ = run_subprocess(["--source", line])
                if "!" in path.name:
                    assert code != 0, f"! Expected failure but line succeeded: {path.name!r}:{i}"
                else:
                    assert code == 0, f"! Expected success but line failed: {path.name!r}:{i}"
