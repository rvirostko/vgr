import json
from pathlib import Path
import pytest

_CONFIG_PATH = Path(__file__).parent / "add_xfail.json"

import json
def _load_add_xfail() -> dict:
    if not _CONFIG_PATH.exists(): return {}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f) # NB: should be an array

# An dictionary:
#  Key: test id
#  Value: string, reason why
_ADD_XFAIL: dict = _load_add_xfail()

def pytest_collection_modifyitems(config, items):
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is not None:
            path = callspec.params.get("path")
            if path is not None and path.name in _ADD_XFAIL:
                reason = f"{path.name}: {_ADD_XFAIL[path.name]}"
                print(f"NOTE - Adding xfail to {reason}")
                item.add_marker(pytest.mark.xfail(reason=reason, strict=False))
