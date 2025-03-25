from typing import Any

def poly_and(x: Any, y: Any) -> Any:
    return bool(x) and bool(y)

def poly_or(x: Any, y: Any) -> Any:
    return bool(x) or bool(y)

def poly_not(x: Any) -> Any:
    return not bool(x)
