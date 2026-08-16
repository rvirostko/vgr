
from io import StringIO
from typing import Any
import json

import configparser
import csv
import hcl2
import yaml

from .registry import builtin

_PASS_THRU_TYPES = (dict, list)

@builtin("ParseJSON")
def poly_parse_json(value: Any=None) -> Any:
    """
**Parse a value as JSON data**

* ParseJSON(*value*)
* *value*.ParseJSON()

Returns `None` if value is `None`.

```vgr
**TODO**
```

Also see `ParseCSV()`, `ParseHCL()`, `ParseINI()`, `ParseYAML()`,
and the `Load` statement.
"""
    if value is None: return None
    if isinstance(value, _PASS_THRU_TYPES): return value
    return parse_json(str(value))

@builtin("ParseCSV")
def poly_parse_csv(value: Any=None) -> Any:
    """
**Parse a value as CSV data**

* ParseCSV(*value*)
* *value*.ParseCSV()

Returns `None` if value is `None`.

```vgr
**TODO**
```

Also see `ParseHCL()`, `ParseINI()`, `ParseJSON()`, `ParseYAML()`,
and the `Load` statement.
"""
    if value is None: return None
    if isinstance(value, list): return value
    if isinstance(value, dict): return [value]
    return parse_csv(str(value))

@builtin("ParseYAML")
def poly_parse_yaml(value: Any=None) -> Any:
    """
**Parse a value as YAML data**

* ParseYAML(*value*)
* *value*.ParseYAML()

Returns `None` if value is `None`.

```vgr
**TODO**
```

Also see `ParseCSV()`, `ParseHCL()`, `ParseINI()`, `ParseJSON()`,
and the `Load` statement.
"""
    if value is None: return None
    if isinstance(value, _PASS_THRU_TYPES): return value
    return parse_yaml(str(value))

@builtin("ParseHCL")
def poly_parse_hcl(value: Any=None) -> Any:
    """
**Parse a value as HCL data**

* ParseHCL(*value*)
* *value*.ParseHCL()

Returns `None` if value is `None`.

```vgr
**TODO**
```

Also see `ParseCSV()`, `ParseINI()`, `ParseJSON()`,  `ParseYAML()`,
and the `Load` statement.
"""
    if value is None: return None
    if isinstance(value, _PASS_THRU_TYPES): return value
    return parse_hcl(str(value))

@builtin("ParseINI")
def poly_parse_ini(value: Any=None) -> Any:
    """
**Parse a value as INI file data**

* ParseINI(*value*)
* *value*.ParseINI()

Returns `None` if value is `None`.

```vgr
**TODO**
```

Also see `ParseCSV()`, `ParseHCL()`, `ParseJSON()`, `ParseYAML()`,
and the `Load` statement.
"""
    if value is None: return None
    if isinstance(value, _PASS_THRU_TYPES): return value
    return parse_ini(str(value))

# Internal shared routines, but not builtin functions

def parse_json(content: str) -> Any:
    return json.loads(content) if content else {}

def parse_csv(content: str) -> list[dict]:
    if not content: return []
    reader = csv.DictReader(StringIO(content))
    return list(reader)

def parse_yaml(content: str) -> Any:
    return yaml.safe_load(content) if content else {}

def parse_hcl(content: str) -> dict:
    return hcl2.load(StringIO(content)) if content else {}

def parse_ini(content: str) -> dict:
    if not content: return {}
    parser = configparser.ConfigParser()
    parser.read_string(content)
    return {section: dict(parser.items(section)) for section in parser.sections()}
