"""
The help system
"""

from typing import Callable

from rapidfuzz import fuzz
from rapidfuzz.fuzz import ratio
from rich.console import Console, Theme
from rich.markdown import Markdown

from functions import get_function_entries, get_function_op, get_function_names, get_function

_THEME = Theme({
    "markdown.text": "",  # Default terminal style
    # NB: Headings are all centered and look horrible: don't use
    #     until Markdown is fixed
    #     Also, __ul__ renders as bold
    # Foreground colors: standard names, 256-color, and hex
	# Background colors: on color
	# Text styles: bold, italic, underline, reverse, blink, dim, strike
    #"markdown.h1": "bold underline",
    #"markdown.h2": "bold",
    #"markdown.h3": "bold",
    #"markdown.h4": "bold",
    #"markdown.h5": "bold",
    #"markdown.h6": "bold",
    #"markdown.list": "",
    #"markdown.item": "",
    "markdown.block_quote": "",
    #"markdown.bold": "bold",
    #"markdown.italic": "italic",
    "markdown.code": "bold",
    "markdown.code_block": "bold",
    "markdown.hr": "bold",
    "markdown.link": "underline",
    "markdown.image": "underline",
}, inherit=True)

_CONSOLE = Console(width=80, theme=_THEME)

def search_functions(query: str, limit: int = 10) -> list[tuple[str, Callable]]:
    """Search the functions using some fuzzy logic"""
    q = (query or "").strip().replace('_', '').lower()
    # If no args, return all
    if not q: return [(name, get_function_op(name)) for name in get_function_names()]
    # Return exact match immediately if found
    entry = get_function(q)
    if entry: return [entry]
    tokens = q.split()
    scores = {}
    # Canonical name, (Name normalized, documentation normalized)
    for name, (name_norm, doc_norm) in get_function_entries().items():
        # 1. Match against full query
        full_score = max(fuzz.QRatio(q, name_norm), fuzz.QRatio(q, doc_norm))
        # 2. Match individual tokens
        token_scores = [max(fuzz.partial_ratio(tok, name_norm), fuzz.partial_ratio(tok, doc_norm)) for tok in tokens]
        # 3. Composite score: prioritize full match, reward partial token matches
        score = full_score * 1.5 + sum(token_scores)
        scores[name] = score
    # Return top N by score
    top_matches = sorted(scores.items(), key=lambda x: -x[1])[:limit]
    return [(name, get_function_op(name)) for name, _ in top_matches]

def print_doc(func) -> None:
    doc = (func.__doc__ or "").strip()
    print()
    print_md(doc if doc else '_Sorry, no documentation available_')
    print()

def print_md(s: str) -> None:
    if s:_CONSOLE.print(Markdown(s))

def is_probably(word: str, s: str, threshold: float = 65.0) -> bool:
    """Return True if s is close enough to the word using a fuzzy match."""
    return ratio((s or "").strip().lower(), word) >= threshold
