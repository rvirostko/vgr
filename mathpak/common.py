#! /usr/bin/env python3

from typing import Any, Callable

def str_to_number(s: str):
    try:
        x: float = float(s.strip())
        return int(x) if x.is_integer() else x
    except ValueError:
        raise TypeError(f'Cannot convert "{s}" to a number')

def dist_list(op: Callable[[Any, Any], Any], x: list, y: Any) -> list:
    """Distribute op over the list: [op(<list>, y)]"""
    return [op(x1, y) for x1 in x]

def dist_tuple(op: Callable[[Any, Any], Any], x: tuple, y: Any) -> tuple:
    """Distribute op over the tuple: (op(<list>, y))"""
    return tuple(op(x1, y) for x1 in x)

def matching_default(x: Any) -> Any:
    t = type(x)
    if t in (int, float): return 0
    if t is list: return []
    if t is tuple: return tuple()
    if t is dict: return {}
    if t is str: return ''
    raise TypeError(f'No default value for {t.__name__}')

# For non-commutative mathematical operations that don't define behaviors for
# dictionaries and have "natural" operations on int/float
# Generally it attempts to cast strings to numbers and
# distributes operations over collections.
math_overrides = {
    (int, str): lambda op, x, y: op(x, str_to_number(y)),
    (float, str): lambda op, x, y: op(x, str_to_number(y)),
    (str, int): lambda op, x, y: op(str_to_number(x), y),
    (str, float): lambda op, x, y: op(str_to_number(x), y),
    (str, str): lambda op, x, y: op(str_to_number(x), str_to_number(y)),
    (list, int): dist_list,
    (list, float): dist_list,
    (list, str): dist_list,
    (tuple, int): dist_tuple,
    (tuple, float): dist_tuple,
    (tuple, str): dist_tuple,
}

import timeit
def time_test(op, cases: list[tuple], times: int=100_000) -> None:
    def tester():
        for x, y in cases:
            try:
                op(x, y)
            except TypeError as e:
                print(f'TypeError: {e}')
    if times == 1:
        print()
        print(60*'=')
        print(op.__doc__, end='')
        print(60*'=')
        for x, y in cases:
            try:
                print(f'{op.__name__}({repr(x)}, {repr(y)}) = ', end='')
                print(f'{repr(op(x, y))}')
            except TypeError as e:
                print(f'TypeError: {e}')
    else:
        factor = times / 1_000_000
        time = timeit.timeit(tester, number=times)
        print(f"{op.__name__}(): {time / factor:.2f} usec")

def main(): pass
if __name__ == "__main__": main()
