#! /usr/bin/python3

from .common import time_test

from typing import Any

def poly_in(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_not_in(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_contains(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_not_contains(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def in_test():
    cases = [
        # TODO
    ]
    time_test(poly_in, cases)

if __name__ == "__main__": in_test()
