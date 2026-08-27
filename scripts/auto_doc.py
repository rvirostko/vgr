"""
Create a Markdown file from internal source
"""

from pathlib import Path
import re
import sys

# NB: __file__ is for the vgr package, not this one...
from vgr import __version__, __version_date__, __file__
from vgr.functions import (
    get_function_entries,
)
from vgr.operators import (
    get_operator_entries,
)
from vgr.stmt_exec import (
    get_statement_entries,
)

_STATEMENTS = []
_OPERATORS = []

def gen_auto_docs() -> None:
    _STATEMENTS.extend(get_statement_entries().keys())
    _OPERATORS.extend(get_operator_entries().keys())
    path = Path("vgr-" + __version__ + ".md")
    with path.open("w", encoding="utf-8", newline="\n", errors='backslashreplace') as f:
        _write_cover_page(f)
        _write_toc(f)
        _write_running(f)
        _write_repl(f)
        _write_variables(f)
        _write_statements(f)
        _write_operators(f)
        _write_functions(f)

# TODO need to expand links in copy doc

def _write_cover_page(f) -> None:
    f.write(read_doc_file("cover_pg.md").format(__version__=__version__, __version_date__=__version_date__))

def _write_toc(f) -> None:
    _write_page_break(f)
    _write_anchor("toc", f)
    _copy_doc_file("toc.md", f)

def _write_running(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-running", f)
    _copy_doc_file("running.md", f)

def _write_repl(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-repl", f)
    _copy_doc_file("repl.md", f)

def _write_variables(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-variables", f)
    _copy_doc_file("variables.md", f)

def _write_statements(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-statements", f)
    _copy_doc_file("statements.md", f)
    _write_all_doc(f, get_statement_entries(), 'statement-')

def _write_functions(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-functions", f)
    _copy_doc_file("functions.md", f)
    _write_all_doc(f, get_function_entries(), 'function-', True)

def _write_operators(f) -> None:
    _write_page_break(f)
    _write_anchor("chapter-operators", f)
    _copy_doc_file("operators.md", f)
    _write_all_doc(f, get_operator_entries(), 'operator-')

def _write_page_break(f) -> None:
    f.write('\n<div style="page-break-before: always; break-before: page;"></div>\n')

def _write_anchor(anchor_id: str, f) -> None:
    f.write("\n")
    f.write(_anchor(anchor_id))
    f.write("\n\n")

def _alpha_first_key(s: str):
    """
    Sort alphabetic-leading strings first, then everything else
    Default ordering is preserved within each group.
    """
    return (not s[:1].isalpha(), s)

def _write_all_doc(f, entries: dict, anchor_prefix: str, is_function: bool=False) -> None:
    names = list(entries.keys())
    names.sort(key=_alpha_first_key)
    for name in names:
        func = entries[name][0]
        doc = (func.__doc__ or "").strip()
        if doc:
            lines = doc.splitlines()
            title = lines[0].strip().strip("*").rstrip(".")
            doc = ''
            mk_links = False
            for line in lines[1:]:
                mk_links = mk_links or line.strip().startswith('Also see')
                if mk_links: line = re.sub(r"`([^`]+)`", _expand_hyperlink, line)
                doc += line + '\n'
                doc = doc.lstrip()
            heading = f'`{name}{"()" if is_function else ""}` - {title}'
        else:
            heading = f'`{name}{"()" if is_function else ""}`'
        f.write('<div style="padding-top: 2rem; break-inside: avoid; page-break-inside: avoid;">\n')
        f.write('\n---\n\n')
        f.write(_heading(heading, anchor_prefix + name, 3))
        f.write('\n---\n\n')
        primary_name = func.bound_ops[0] if hasattr(func, 'bound_ops') else name
        if name == primary_name:
            f.write(doc or '_No documentation available_')
        else:
            # write a link to primary
            # cannot make assumption about anchor prefix: see Add()
            f.write("See " + _link(f'`{primary_name}`', _anchor_for(primary_name)))
        f.write('\n</div>\n')

def read_doc_file(src_filename: str) -> str:
    module_path = Path(__file__).resolve()
    src_file = Path(module_path.parent / "doc" / src_filename)
    if src_file.is_file():
        with open(src_file, 'r', encoding='utf-8', errors='backslashreplace') as file_in:
            return file_in.read().rstrip() + '\n'
    print(f"Did not find {src_file}", file=sys.stdout)
    return ''

def _copy_doc_file(src_filename: str, output) -> None:
    output.write(read_doc_file(src_filename))

def _anchor_for(text: str) -> str:
    if text.endswith("()"): return "function-" + text[:-2].casefold()
    if text in _STATEMENTS: return "statement-" + text.casefold()
    if text in _OPERATORS: return "operator-" + text.casefold()
    return text.casefold()

def _expand_hyperlink(match) -> str:
    text = match.group(1)  # text inside backticks
    return _link(f'`{text}`', _anchor_for(text))

def _heading(title: str, anchor_id: str, level: int = 2) -> str:
    return f'{_anchor(anchor_id)}\n\n{"#" * level} {title}\n'

def _fix_anchor(anchor_id: str) -> str:
    return anchor_id.replace(' ', '_').replace('<', '_lt_').replace('>', '_gt_').replace('"', '_q_')

def _link(text: str, anchor_id: str) -> str:
    return f'[{text}](#{_fix_anchor(anchor_id)})'

def _anchor(anchor_id: str) -> str:
    return f'<a id="{_fix_anchor(anchor_id).casefold()}"></a>'

if __name__ == "__main__":
    gen_auto_docs()
