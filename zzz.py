#! /usr/bin/python3

import csv
import sys

import itertools


headers = ["a", "b", "c"]
data = [
    [1, "Xx", [10, 20, 30]],
    [2, "Yy", [40, 50]],
    [3, "Zz", None],  # flattened NULL case
    [4, "Ww", []],    # flattened Empty list case
    [5, "Vv", 100],   # Scalar treated as list [100]
    [[6, 7], "Aa", 200],   # Non-scalar not flattened
    [8, None, 400],   # not flattened NULL case
]
flatten = [True, True, True]

def flatten_row(values: list[any], flatten_flags: list[bool]):
    iterable_values: list = []
    for value, flatten in zip(values, flatten_flags):
        if flatten:
            # Do NOT flatten strings into character array!
            if not isinstance(value, str) and hasattr(value, '__iter__'):
                if len(value) > 0:
                    iterable_values.append(value) # normal iterator should suffice
                else:
                    iterable_values.append([None]) # empty list, stills need to gen one row
            else:
                iterable_values.append([value]) # treat as a list of one
        else:
            iterable_values.append([value])
    for x in itertools.product(*iterable_values): yield x

def write_flattened(writer, row, flatten):
    for xrow in flatten_row(row, flatten): writer.writerow(xrow)

def main():
    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(headers)
    output = None
    if any(flatten):
        output = lambda row: write_flattened(csv_writer, row, flatten)
    else:
        output = lambda row: csv_writer.writerow(row)
    for row in data: output(row)

if __name__ == "__main__":
    main()