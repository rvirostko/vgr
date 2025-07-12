"""
The help system
"""

from typing import Callable

from rapidfuzz import fuzz
from rapidfuzz.fuzz import ratio
from rich.console import Console, Theme
from rich.markdown import Markdown

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

# Pull out weights etc for better tuning
_FULL_SCORE_WEIGHT = 1.5
_WEAK_SCORE_RATIO = 0.7

def search_entries(entries: dict, query: str="", limit: int = 10) -> list[tuple[str, Callable]]:
    """
    Search using some fuzzy logic. entries should be in the form of:

        key: Canonical name, value: (implementing function, name normalized, documentation normalized)

    """
    if not entries: return []
    q = query.strip().replace('_', '').casefold().removesuffix("()").removesuffix("(")
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
    if top_name and top_name.casefold().replace('_', '').replace(' ', '') == q:
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

def print_doc(func: Callable) -> None:
    doc = (func.__doc__ or "").strip()
    print()
    print_md(doc if doc else '_Sorry, no documentation available_')
    print()

def print_md(s: str) -> None:
    if s: Console(theme=_THEME).print(Markdown(s))

def is_probably(word: str, s: str, threshold: float = 65.0) -> bool:
    """Return True if s is close enough to the word using a fuzzy match."""
    return ratio((s or "").strip().lower(), word) >= threshold
