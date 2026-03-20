"""
HttpData is a collection of the parsed and processed options
from Http statements
"""

from collections import namedtuple
from dataclasses import dataclass, field, fields

from lark import Tree

from ..builtins import poly_isempty

_REDACTED_FIELDS = {'password'}

# ---------------------------------------------------------------------------
# Setting — carries a resolved value and its source tree node.
# The tree node is retained only for conflict/error reporting during
# cross field validation. After that, tree references are no longer needed.
# ---------------------------------------------------------------------------
class Setting(namedtuple('Setting', ['value', 'tree'])):
    @property
    def is_missing(self) -> bool:
        """True when value is None or empty string."""
        return self.value is None or (isinstance(self.value, str) and poly_isempty(self.value))

# ---------------------------------------------------------------------------
# HttpData — single combined dataclass for all options.
# Fields primed to None, meaning "not provided by user, apply default".
# User-supplied None is treated the same as not provided.
# Headers and parameters accumulate across multiple clauses.
# ---------------------------------------------------------------------------
@dataclass
class HttpData:
    # positional - required for requests only
    method:             Setting = None

    # positional — required for connect and action, no default possible
    url:                Setting = None

    # connect only options
    connection_name:    Setting = None
    verify_ssl:         Setting = None   # trinary: None / True / False
    ca_cert:            Setting = None
    connect_timeout:    Setting = None
    http_version:       Setting = None

    # auth — shared between connect (defaults) and request (overrides)
    user:               Setting = None
    password:           Setting = None
    authentication:     Setting = None   # constrained: "basic", "digest"

    # req — shared between connect (defaults) and request (overrides)
    timeout:            Setting = None
    read_timeout:       Setting = None
    write_timeout:      Setting = None
    follow_redirects:   Setting = None   # trinary: None / True / False
    max_redirects:      Setting = None

    # accumulating — merged across connect (defaults) and request (overrides)
    headers:            dict = field(default_factory=dict)
    parameters:         dict = field(default_factory=dict)

    # request only
    body:               Setting = None
    giving:             Setting = None   # value is tuple/path

    @staticmethod
    def is_missing(setting: Setting) -> bool:
        """
        True when the Setting is None (never set) or its value is missing.
        Delegates to Setting.is_missing when the Setting exists.
        """
        return setting is None or setting.is_missing

    def get_content_type(self) -> str:
        return self.headers.get('Content-Type', '') if self.headers else None

    def _set_content_type(self, value: str) -> None:
        if self.headers is None: self.headers = {}
        self.headers['Content-Type'] = value.strip() if value else None

    @staticmethod
    def tree_for(setting: Setting, default_tree: Tree) -> Tree:
        return setting.tree if setting is not None and setting.tree is not None else default_tree

    def __str__(self) -> str:
        parts = []
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue
            if isinstance(value, Setting):
                if value.value is None:
                    continue
                if f.name in _REDACTED_FIELDS:
                    parts.append(f'{f.name}={"*" * len(str(value.value))}')
                else:
                    parts.append(f'{f.name}={value.value!r}')
            elif isinstance(value, dict):
                if value:
                    parts.append(f'{f.name}={value!r}')
            else:
                parts.append(f'{f.name}={value!r}')
        return f'HttpData({", ".join(parts)})'
