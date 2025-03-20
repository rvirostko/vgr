#! /usr/bin/python3

import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from output import JSONRecordWriter, CSVRecordWriter, MarkdownRecordWriter, RecordLimiter, RecordCartesianProduct, RecordWriter, TemplateRecordWriter

def main():

    # These would be in the data from the select statement's parse tree
    offset = 0#4
    limit = None#4
    ascii = False#True
    include_null = False#True
    root = None#'people'
    compact = True
    indent = 2
    sort_keys = True
    # The data that would come back from the query
    # TODO need to test output with single dict
    headers = [ "name", "age", "pos" ]
    product = [False, False, False]
    data = [
        ["Alice", 25, "Engineer"],
        ["Bob", 30, "Doctor"],
        ["Carol", 28, "Data || Analyst"],
        ["Dave", 35, "Data | Engineer"],
        ["Jimbo", 22, ["Hobo", "Jerk"]],
        ["Limbo", None, ["Hobo", "流浪"]],
        ["Complex", 99, {'a': 1, 'b': [2,3]}]
    ]

    for output_type in ('markdown', 'json-array', 'json-root', 'json-line', 'csv', 'template'):
        out: RecordWriter = None
        if output_type == 'markdown':
            out = (MarkdownRecordWriter().
                    set_encode_ascii(ascii).
                    set_headers(headers))
        elif output_type == 'template':
            out = (TemplateRecordWriter().
                   set_encode_ascii(ascii).
                   set_headers(headers))
        elif output_type == 'csv':
            out = (CSVRecordWriter().
                    set_encode_ascii(ascii).
                    set_headers(headers).
                    set_quoting().
                    set_quotechar().
                    set_lineterminator().
                    set_escapechar())
        elif output_type.startswith('json'):
            out = (JSONRecordWriter().
                    set_encode_ascii(ascii).
                    set_headers(headers).
                    set_compact(compact).
                    set_include_null(include_null).
                    set_indent(indent).
                    set_sort_keys(sort_keys))
            if output_type == 'json-root':
                out.set_root('results')
            if output_type == 'json-line':
                out.set_exclude_array_wrapper()
        else:
            raise ValueError(output_type)

        # Order is important since projections can generate more than one row
        # It depends upon how you want to interpret the limit/offset, and that is TBD
        out = RecordLimiter.wrap(out, limit, offset)
        out = RecordCartesianProduct.wrap(out, product)

        print(f'{output_type}-')
        if out.start():
            for row in data:
                if not out.write(row): break
            out.finish()
        print()

if __name__ == "__main__":
    main()
