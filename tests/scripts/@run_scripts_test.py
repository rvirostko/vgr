# pylint: disable=invalid-name

from io import StringIO
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

import pytest

from vgr.data_dict import DataDictionary
from vgr.dd_config import dd_init, set_user_args
from vgr.functions import add_builtin_functions
from vgr.vgr import load_extensions, create_parser, create_md_lexer
from vgr.stmt_exec import create_exec_context, ExecContext, do_source
from vgr.app_exceptions import VgrException, VgrExitingException
from vgr.redir import print_stderr

SCRIPTS_DIR = Path(__file__).parent
ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "test-log"
SAMPLES_DIR = ROOT_DIR / "samples"

_state = {
    'init': False,
    'ctx': None,
}

def vgr_init():
    """Simulates command line start up"""
    if not _state['init']:
        dd = DataDictionary()
        dd_init(dd)
        add_builtin_functions()
        extensions = load_extensions(dd, False)
        parser = create_parser(extensions, False, False)
        create_md_lexer(parser)
        ctx = create_exec_context(parser, dd)
        _state['ctx'] = ctx
        ctx.debug = False
        ctx.verbose = False
        ctx.echo = False
        set_user_args(ctx, [])
    _state['init'] = True

def run_vgr_test_file(path: Path) -> tuple[int, str]:
    """Simulates running a file from the command line"""
    vgr_init()
    output_buf = StringIO()
    exit_code = VgrExitingException.EXIT_SUCCESS
    ctx:ExecContext = _state["ctx"]
    with redirect_stdout(output_buf), redirect_stderr(output_buf):
        try:
            ctx:ExecContext = _state["ctx"]
            ctx.debug = False
            ctx.echo = False
            ctx.verbose = False
            ctx.execute_statements("Reset All", '<test>')
            ctx.execute_statements("dev_test=True", '<test>', 'set') # like --assign
            do_source(ctx, path) # like --file
        except VgrExitingException as e:
            exit_code = e.exit_code
        except VgrException as e:
            exit_code = VgrExitingException.EXIT_FAILED
            print_stderr(str(e))
        except Exception as e: # pylint: disable=broad-exception-caught
            exit_code = VgrExitingException.EXIT_FAILED
            print_stderr(str(e))
    output = output_buf.getvalue()
    print()
    print("-" * 72)
    print(output)
    print()
    print("-" * 72)
    return (exit_code, output)

def run_vgr_test_statement(line: str) -> tuple[int, str]:
    vgr_init()
    output_buf = StringIO()
    exit_code = VgrExitingException.EXIT_SUCCESS
    ctx:ExecContext = _state["ctx"]
    with redirect_stdout(output_buf), redirect_stderr(output_buf):
        try:
            ctx:ExecContext = _state["ctx"]
            ctx.debug = False
            ctx.echo = False
            ctx.verbose = False
            ctx.execute_statements("Reset All", '<test>')
            ctx.execute_statements("dev_test=True", '<test>', 'set') # like --assign
            ctx.echo = True # like --echo
            ctx.execute_statements(line, '<test>') # like --execute
        except VgrExitingException as e:
            exit_code = e.exit_code
        except VgrException as e:
            exit_code = VgrExitingException.EXIT_FAILED
            print_stderr(str(e))
        except Exception as e: # pylint: disable=broad-exception-caught
            exit_code = VgrExitingException.EXIT_FAILED
            print_stderr(str(e))
    output = output_buf.getvalue()
    print(output)
    return (exit_code, output)

# -------------------------------
# .vgr FILES
# -------------------------------

@pytest.mark.parametrize(
    "path",
    list(SCRIPTS_DIR.glob("*.vgr")) + list(SAMPLES_DIR.glob("*.vgr")),
    ids=lambda p: p.name,
)
def test_vgr_files(path: Path):
    """Execute .vgr files via --file"""
    LOG_DIR.mkdir(exist_ok=True)
    code, stdout = run_vgr_test_file(path)
    with (LOG_DIR / (path.name + ".txt")).open("w", encoding="utf-8", errors='backslashreplace') as f:
        if stdout: f.write(stdout)
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
        with (LOG_DIR / (path.name + ".txt")).open("w", encoding="utf-8", errors='backslashreplace') as f:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                # ignore empty lines and comments
                if line and \
                    not line.startswith("#") and \
                    not line.startswith("//") and \
                    not (line.startswith("/*") and line.endswith("*/")):
                    code, stdout = run_vgr_test_statement(line)
                    if stdout: f.write(stdout)
                    if "!" in path.name:
                        assert code != 0, f"! Expected failure but line {i} succeeded: {path.name!r}:{i}"
                    else:
                        assert code == 0, f"! Expected success but line {i} failed: {path.name!r}:{i}"
                else:
                    # blank lines and comments
                    print(line)
