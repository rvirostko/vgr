#! /usr/bin/python3

from .common import time_test

from typing import Any

def poly_match(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_not_match(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_imatch(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def poly_not_imatch(x: Any, y: Any) -> Any:
    raise NotImplementedError() # TODO

def match_test():
    cases = [
        # TODO
    ]
    time_test(poly_match, cases)

if __name__ == "__main__": match_test()
