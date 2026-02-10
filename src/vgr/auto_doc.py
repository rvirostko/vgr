"""
Create a Markdown file from internal source
"""

from pathlib import Path
import re

from . import __version__, __version_date__
from .functions import (
    get_operator_entries,
    get_function_entries,
)
from .stmt_exec import (
    get_statement_entries,
)

_STATEMENTS = []
_OPERATORS = []

def gen_auto_docs() -> None:
    _STATEMENTS.extend(get_statement_entries().keys())
    _OPERATORS.extend(get_operator_entries().keys())
    path = Path("vgr-" + __version__ + ".md")
    with path.open("w", encoding="utf-8", newline="\n") as f:
        _create_cover_page(f)
        _write_toc(f)
        _write_statements(f)
        _write_operators(f)
        _write_functions(f)

def _write_toc(f) -> None:
    # TODO needs a "variables" overview
    f.write(f"""
<div style="page-break-before: always; break-before: page;"></div>

## CONTENTS

### {_link("Statements", "chapter-statements")}

### {_link("Operators", "chapter-operators")}

### {_link("Functions", "chapter-functions")}

""")

def _alpha_first_key(s: str):
    """
    Sort alphabetic-leading strings first, then everything else
    Default ordering is preserved within each group.
    """
    return (not s[:1].isalpha(), s)

def _write_statements(f) -> None:
    f.write(_heading("STATEMENTS", "chapter-statements"))
    # TODO blurb from file
    _write_all_doc(f, get_statement_entries(), 'statement-')

def _write_functions(f) -> None:
    f.write(_heading("FUNCTIONS", "chapter-functions"))
    # TODO blurb from file
    _write_all_doc(f, get_function_entries(), 'function-', True)

def _write_operators(f) -> None:
    f.write(_heading("OPERATORS", "chapter-operators"))
    # TODO blurb from file
    _write_all_doc(f, get_operator_entries(), 'operator-')

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
        f.write('\n</div>\n\n')

def _create_cover_page(f) -> None:
    f.write(f"""
<div align="center" style="padding: 20rem 0 30rem;">

---
<div style="font-size: 200%">VGR LANGUAGE REFERENCE</div>
<div style="font-size: 75%">Version {__version__} • {__version_date__}</div>

---
</div>

""")

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
