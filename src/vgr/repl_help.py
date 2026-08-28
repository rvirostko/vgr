
import re
from importlib.metadata import (
    distribution,
    metadata,
)
from pathlib import Path
from typing import Callable

from rapidfuzz import fuzz

from .stmt_exec import get_statement_entries
from .operators import get_operator_entries
from .functions import get_function_entries
from .md_print import md_println

_HEADING_PATTERN = re.compile(r'^(#+)\s+(.*)$', re.MULTILINE)
_ANCHOR_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(#([^)]+)\)')
_HTML_ANCHOR_PATTERN = re.compile(r'<a\s+id="[^"]+"></a>', re.IGNORECASE)
_COLLAPSE_NEWLINE_PATTERN = re.compile(r'\n{2,}')

def _md_fixup(text: str) -> str:
    text = _ANCHOR_LINK_PATTERN.sub(r'`\1`', text)
    text = _HTML_ANCHOR_PATTERN.sub('', text)
    text = _HEADING_PATTERN.sub(lambda m: f"**{m.group(2).strip()}**", text)
    return _COLLAPSE_NEWLINE_PATTERN.sub('\n\n', text)

_FUNCTION_TOPIC_KEY = ("function", "func",)
_OPERATOR_TOPIC_KEY = ("operator", "ops", "op",)
_STATEMENT_TOPIC_KEY = ("statement", "stmt",)

def _default_help_action(topic: str, q: str) -> None:
    # If no explicit topic that matches, then see what we can find
    # in statements, functions, and operators
    q = topic + ' ' + q
    func_help = _search_function_help(q)
    if len(func_help) == 1:
        _display_function_help(q, func_help)
    else:
        op_help = _search_operator_help(q)
        if len(op_help) == 1:
            _display_operator_help(q, op_help)
        else:
            stmt_help = _search_statement_help(q)
            if stmt_help:
                _display_statement_help(q, stmt_help)
            else:
                md_println("\n", "_Use **help topics** to list topics_", "\n")

def _search_statement_help(q: str) -> list:      return search_entries(get_statement_entries(), q)
def _display_statement_help(q, results) -> None: _display_help_results("Statements", q, results)
def _list_statements() -> None:
    all_stmts = _all_help(get_statement_entries())
    all_stmts.sort(key=lambda t: t[0])
    _display_statement_help(None, all_stmts)

def _search_operator_help(q: str) -> list:      return search_entries(get_operator_entries(), q)
def _display_operator_help(q, results) -> None: _display_help_results("Operators", q, [(func.bound_ops[0], func) for _name, func in results])
def _list_operators() -> None:
    all_ops = _all_help(get_operator_entries())
    all_ops.sort(key=lambda t: t[1].bound_ops[0])
    _display_operator_help(None, all_ops)

def _search_function_help(q: str) -> list:      return search_entries(get_function_entries(), q)
def _display_function_help(q, results) -> None: _display_help_results("Functions", q, [(name + "()", func) for name, func in results])
def _list_functions() -> None:
    all_funcs = _all_help(get_function_entries())
    all_funcs.sort(key=lambda t: t[0])
    _display_function_help(None, all_funcs)

def _all_help(entries: list) -> list: return unique_by_func([(name, entries[name][0]) for name in entries.keys()])

def _display_help_results(search_type: str, q: str, results: list) -> None:
    if len(results) == 0:
        # We could not find anything
        md_println("\n", f'_Nothing matches{" " + repr(q) if q else ""}_', "\n")
    elif len(results) == 1:
        # We got an single match
        # Show the help for the item
        print_doc(results[0][1])
    else:
        # Multiple results
        # Show as a list with a summary
        lines = []
        lines.append(f'**{"Search Results" if q else search_type}-**')
        for name, func in results:
            doc = (func.__doc__ or "").strip()
            if doc:
                # Display first non-blank line, stripped of bolding (the convention) and no sentence
                lines.append(f'* `{name}` - {doc.splitlines()[0].strip().strip("*").rstrip(".")}')
            else:
                lines.append(f'* `{name}`')
        md_println("\n", "\n".join(lines), "\n")

def print_doc(func: Callable) -> None:
    """Prints the documentation for a function to the console as Markdown text"""
    doc = (func.__doc__ or "").strip()
    md_println("\n", doc or '***Sorry, no documentation available***', "\n")

_LIST_TOPICS = { # help list <topic>
    _FUNCTION_TOPIC_KEY:  _list_functions,
    _OPERATOR_TOPIC_KEY:  _list_operators,
    _STATEMENT_TOPIC_KEY: _list_statements,
}

def _print_type_list(_topic: str, q: str) -> None:
    sub_topic = q
    for key in sorted(_LIST_TOPICS.keys()):
        for list_key in key:
            if _fuzzy_match(list_key, sub_topic):
                _LIST_TOPICS[key]()
                return
    _default_help_action('', q)

def _fuzzy_match(key: str, s: str) -> bool:
    # short items need to be an exact match, longer ones can be fuzzy
    return key == s  if len(s) <= 4 else fuzz.ratio(key, s) >= 70.0

_HELP_TOPICS = {
    _FUNCTION_TOPIC_KEY:  lambda _topic, q: _display_function_help(q, _search_function_help(q)) if q else _list_functions(),
    _OPERATOR_TOPIC_KEY:  lambda _topic, q: _display_operator_help(q, _search_operator_help(q)) if q else _list_operators,
    _STATEMENT_TOPIC_KEY: lambda _topic, q: _display_statement_help(q, _search_statement_help(q)) if q else _list_statements(),
    ("help", "topics", "?",) : lambda _topic, _q: print_doc(repl_help),
    ("license",):              lambda _topic, _q: md_println("\n", _md_fixup(_read_license_file()), "\n"),
    ("authors",):              lambda _topic, _q: md_println(_md_fixup(_get_authors()), "\n"),
    ("list",):                 _print_type_list,
}

def repl_help(*args) -> None:
    """
**REPL Commands**

* **exit** : Ends the REPL session using the VGR `Exit` statement
* **cd *directory***: Change the current working directory
* **history** : Display REPL command history
* **history --clear** : Erase REPL command history
* **history --max *n*** : Set how many commands will be saved in the REPL command history
* **multiline [on | off]** : Begin or end multiline editing in the REPL
* **pwd** : Display the current working directory
* **shell** : Enter an interactive subshell
* **shell *command*** : Execute a shell command

**Help Topics**

* **help list [functions | statements | operators]** : List the names of the available items
* **help license** : The license which governs VGR's use
* **help authors** : VGR's authors
* help *anything else* : Search language features looking for help.
  For example **help Add** will return informtion for `Add()` while
  **help statement Add** gets information for the like-named statement.
"""
    if len(args) < 1:
        topic = "help"
        query = ""
    else:
        topic, *args = args
        topic = topic.strip().lower()
        query = ' '.join(args).strip()
        # If the topic ends with "()" then we only search functions
        if bool(re.search(r"\([^)]*\)$", topic)):
            query = topic + ' ' + query
            _display_function_help(query, _search_function_help(query))
            return
    # Go through the list of topics seeing if we have a match
    for key in _HELP_TOPICS.keys():
        for topic_key in key:
            # short topics need to be an exact match, longer ones can be fuzzy
            if _fuzzy_match(topic_key, topic):
                _HELP_TOPICS[key](topic, query)
                return
    _default_help_action(topic, query)

# pylint: disable=bare-except
def _read_license_file():
    """Read license text in both dev and installed environments."""
    try:
        # When installed: read from package metadata
        dist = distribution('vgr')
        license_files = dist.files
        for file in license_files:
            if file.match('*/LICENSE.md') or file.name == 'LICENSE.md':
                return file.read_text()
    except:
        pass
    # Fallback for development: navigate up from package location
    try:
        package_dir = Path(__file__).parent  # vgr/__init__.py location
        license_path = package_dir.parent.parent / 'LICENSE.md'  # up to project root
        if license_path.exists():
            return license_path.read_text()
    except:
        pass
    return "**License file not found**"

# pylint: disable=bare-except
def _get_authors():
    """Get authors from package metadata as Markdown."""
    try:
        meta = metadata('vgr')
        author_email = meta.get('Author-Email', '')
        if not author_email: return "Authors not available"
        pattern = r'([^<,]+?)\s*<([^>]+)>'
        matches = re.findall(pattern, author_email)
        if not matches: return author_email  # Return raw if parsing fails
        # Format as Markdown list
        lines = [f"- **{name.strip()}** — {email.strip()}"
                 for name, email in matches]
        return '\n'.join(lines)
    except:  # pylint: disable=bare-except
        return "Package metadata error"

# Pull out weights etc for better tuning
_FULL_SCORE_WEIGHT = 1.5
_WEAK_SCORE_RATIO = 0.7

def search_entries(entries: dict, query: str="", limit: int = 10) -> list[tuple[str, Callable]]:
    """
    Search using some fuzzy logic. entries should be in the form of:

        key: Canonical name, value: (implementing function, name normalized, documentation normalized)

    """
    def norm_key(k: str) -> str:
        return re.sub(r'\s+', ' ', k.strip().replace('-', ' ').casefold())
    if not entries: return []
    q = query.strip().casefold().removesuffix("()").removesuffix("(")
    tokens = q.split()
    scores = {}
    for name, (_, name_norm, doc_norm) in entries.items():
        # 1. Match against full query
        query_score = max(fuzz.QRatio(q, name_norm), fuzz.QRatio(q, doc_norm))
        # 2. Match individual tokens
        token_score = sum(max(fuzz.partial_ratio(tok, name_norm), fuzz.partial_ratio(tok, doc_norm)) for tok in tokens)
        # 3. Composite score: prioritize full match, reward partial token matches
        scores[name] = query_score * _FULL_SCORE_WEIGHT + token_score
    # Only include matches above threshold, sorted by score descending
    threshold = max(scores.values()) * _WEAK_SCORE_RATIO
    filtered_matches = [
        (name, score) for name, score in scores.items() if score >= threshold
    ]
    # Sort by descending score
    filtered_matches.sort(key=lambda x: -x[1])
    # If the query is an "exact" match, return only that entry
    top_name = filtered_matches[0][0] if filtered_matches else None
    if top_name and norm_key(top_name) == norm_key(q):
        return [(top_name, entries[top_name][0])]
    # Otherwise, convert the filtered matches into an array and return
    # references that are unique by function
    return unique_by_func([(name, entries[name][0]) for name, _score in filtered_matches], limit)

def unique_by_func(entries: list, limit: int=None) -> list:
    funcs = set()
    rc = []
    for name, func in entries:
        if func not in funcs:
            rc.append((name, func))
            funcs.add(func)
            if limit and len(rc) >= limit: break
    return rc
