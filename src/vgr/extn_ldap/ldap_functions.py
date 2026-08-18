"""
Functions used to aid in the construction of LDAP quries.
"""

import re
from typing import Dict, Any, List, Generator

def _flatten(val: Any) -> Generator[Any, Any, Any]:
    """Recursively yield non-blank strings from val, ignoring others."""
    if isinstance(val, str) and val and not val.isspace():
        yield val
    elif isinstance(val, (list, tuple)):
        for item in val:
            yield from _flatten(item)

def _ensure_parens(x: str) -> str:
    """
Ensure that an LDAP filter string is wrapped in parentheses.

Args:
    filter_str: The LDAP filter string (e.g., "cn=bob")

Returns:
    The filter string wrapped in parentheses if not already.
"""
    if x is None or not isinstance(x, str): return x
    x = x.strip()
    if not x: raise ValueError('Filter cannot be empty')
    return x if (x.startswith('(') or x.startswith('!()')) and x.endswith(')') else f'({x})'

def ldap_escape(x: str=None) -> str:
    """
**Escape special characters in an LDAP filter value**
"""
    if x is None: return None
    x = str(x)
    return x.replace('(', r'\28') \
             .replace(')', r'\29') \
             .replace('\0', r'\00')

def _to_filter_list(*args) -> list:
    filters = list(_flatten(args))
    return [_ensure_parens(f) for f in filters]

def ldap_and(*args) -> str:
    """
**Combine two or more LDAP filter expressions with a logical AND**
"""
    if not args: return None
    filters = _to_filter_list(args)
    return None if not filters else filters[0] if len(filters) == 1 else f'(&{"".join(filters)})'

def ldap_or(*args) -> str:
    """
**Combine two or more LDAP filter expressions with a logical OR**
"""
    if not args: return None
    filters = _to_filter_list(args)
    return None if not filters else filters[0] if len(filters) == 1 else f'(|{"".join(filters)})'

def ldap_not(*args) -> str:
    """
**Negate an LDAP filter expression**
"""
    if not args: return None
    filters = [f'(!{f})' for f in _to_filter_list(args)]
    return None if not filters else filters[0] if len(filters) == 1 else ldap_and(filters)

def _gen_attr_op(prefix: str, operator: str, combiner: str, attr: str, *values: str) -> str:
    escaped_values = [ldap_escape(v) for v in _flatten(values)]
    if not escaped_values: raise ValueError(f'At least one value must be provided for attribute {attr!r}')
    filters = [f'{prefix}({attr}{operator}{v})' for v in escaped_values]
    if len(filters) == 1: return filters[0]
    return f"({combiner}{''.join(filters)})"

def _gen_attr_ineq(prefix: str, operator: str, attr: str, *values: str) -> str:
    return _gen_attr_op(prefix, operator, '&', attr, *values)

def attr_equals(*args) -> str:
    """
**Generate a filter for equality of an attribute with one or more values**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_op('', '=', '|', args[0], *args[1:])

def attr_not_equals(*args) -> str:
    """
**Generate a filter for inequality of an attribute with one or more values**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_op('!', '=', '&', args[0], *args[1:])

def attr_match(*args) -> str:
    """
**Generate a filter for approximate match of an attribute with one or more values**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_op('', '~=', '|', args[0], *args[1:])

def attr_lessthan(*args) -> str:
    """
**Generate a filter for less-than comparison of an attribute**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_ineq('!', '>=', args[0], *args[1:])

def attr_greaterthan(*args) -> str:
    """
**Generate a filter for greater-than comparison of an attribute**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_ineq('!', '<=', args[0], *args[1:])

def attr_lessthaneq(*args) -> str:
    """
**Generate a filter for less-than or equal-to comparison of an attribute**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_ineq('', '<=', args[0], *args[1:])

def attr_greaterthaneq(*args) -> str:
    """
**Generate a filter for greater-than or equal-to comparison of an attribute**

```vgr
**TODO**
```

"""
    if len(args) < 2: return None
    return _gen_attr_ineq('', '>=', args[0], *args[1:])

def attr_between(attr: str=None, low_value: str=None, high_value: str=None) -> str:
    """
**Generate a filter for an attribute being inside a range**

```vgr
**TODO**
```

"""
    if attr is None: return None
    return ldap_and(attr_greaterthaneq(attr, low_value), attr_lessthaneq(attr, high_value))

def attr_exists(attr: str=None) -> str:
    """
**Generate a filter for an attribute having any value**

```vgr
**TODO**
```

"""
    return attr_equals(attr, '*')

def attr_not_exists(attr: str=None) -> str:
    """
**Generate a filter for an attribute not having any value**

```vgr
**TODO**
```

"""
    return attr_not_equals(attr, '*')

# operator → builder function
_OP_MAP = {
    "=":  attr_equals,
    "!": attr_not_equals,
    "~": attr_match,
    "<":  attr_lessthan,
    "<=": attr_lessthaneq,
    ">":  attr_greaterthan,
    ">=": attr_greaterthaneq,
}

# regex to capture a leading operator
_LEADING_OP = re.compile(r'^\s*(<=|>=|!|~|=|<|>)(.*)$')

def _normalize_key(k: Any) -> str:
    k = _normalize_value(k)
    if not isinstance(k, str): return None
    s = k.strip()
    return None if not s else s.replace(' ', '_')

def _normalize_value(v: Any) -> str:
    if isinstance(v, list): return _normalize_value(v[0] if len(v) == 1 else None)
    if isinstance(v, bool): return str(v).casefold()
    if isinstance(v, (int, float)): return str(v)
    return v if isinstance(v, str) else None

def _split_with_ops(expr: str) -> List[str]:
    """
    Split on '&&' and '||' while preserving delimiters and empty/blank tokens.
    Returns a list like: [token, '&&', token, '||', token, ...]
    """
    return re.split(r'(\&\&|\|\|)', expr)

def _token_to_filter(attr: str, token: str) -> str:
    """
    Convert a single token into an LDAP filter fragment by:
      - detecting optional leading operator
      - defaulting to '=' when absent
      - preserving token value verbatim (no trim)
      - delegating to predefined helper functions
    """
    m = _LEADING_OP.match(token)
    if m:
        op, raw_val = m.group(1), m.group(2)
    else:
        op, raw_val = "=", token  # default equality
    builder = _OP_MAP.get(op)
    if builder is None:
        # SNO
        raise ValueError(f"Unsupported operator {op!r} for attribute {attr!r}") # pragma no cover
    return builder(attr, raw_val)

def _reduce_attr_tokens_to_filter(attr: str, parts: List[str]) -> str:
    """
    Given parts = [token, '&&', token, '||', token, ...],
    apply standard precedence: '&&' binds tighter than '||'.
    """
    # First, build a list of filters and operators in sequence.
    seq: List[Any] = []
    for p in parts:
        if p in ("&&", "||"):
            seq.append(p)
        else:
            seq.append(_token_to_filter(attr, p))

    # Group by && first
    groups: List[str] = []
    current: List[str] = []
    i = 0
    while i < len(seq):
        item = seq[i]
        if item == "||":
            # finalize current group
            if not current:
                # empty group => treat as empty token equality: builder('=', '')
                current.append(_token_to_filter(attr, ""))  # extremely edge, but consistent
            groups.append(current[0] if len(current) == 1 else ldap_and(current[0], *current[1:]))
            current = []
        elif item == "&&":
            # just a separator; next iteration will append next token into current group
            pass
        else:
            # filter fragment
            current.append(item)
        i += 1

    # finalize last group
    if current:
        groups.append(current[0] if len(current) == 1 else ldap_and(current[0], *current[1:]))

    # Now OR the groups (if multiple)
    if not groups:
        # No tokens? This means the original value was empty string split? Treat as equality with blank.
        return _token_to_filter(attr, "")
    return groups[0] if len(groups) == 1 else ldap_or(groups[0], *groups[1:])

def qbe_to_filter(qbe: Dict[Any, Any]=None) -> str:
    """
*Converts a dictionary to a query-by-example filter*

* *value*.ToLdapFilter()

The key-value pairs in the dictionary are converted to LDAP filter expressions.
Keys or values that are invalid are ignored. The dictionary must contain at
least one valid key-value pair.

* Key and values must be strings, intergers, floats, or booleans
* Leading and trailing spaces in keys are ignored. Embedded spaces are converted to an underscore.
* Values may be composed of _&&_ and _||_ for logical And and Or operations respectively.
* Values may start with an operator: =, !, ~, <, >, <=, >=. Equality is optional and assumed when operator is provided.

```vgr
**TODO**
```
"""
    if not isinstance(qbe, dict): return None
    attr_filters: List[str] = []
    for raw_k, raw_v in qbe.items():
        attr = _normalize_key(raw_k)
        if attr is None: continue
        norm_v = _normalize_value(raw_v)
        if norm_v is None: continue
        parts = _split_with_ops(norm_v)
        # parts includes tokens and delimiters; even "" tokens are preserved
        attr_filter = _reduce_attr_tokens_to_filter(attr, parts)
        attr_filters.append(attr_filter)
    if not attr_filters: raise ValueError('No usable attributes/values')
    return attr_filters[0] if len(attr_filters) == 1 else ldap_and(attr_filters[0], *attr_filters[1:])
