#! /usr/bin/python3

import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from output import JSONRecordWriter, CSVRecordWriter, MarkdownRecordWriter, RecordLimiter, RecordCartesianProduct, RecordWriter, TemplateRecordWriter

def create(output_type, encode_ascii, headers, omit_headers, compact, include_null, indent, sort_keys):
    if output_type == 'markdown':
        return MarkdownRecordWriter(encode_ascii=encode_ascii,
                                    headers=headers,
                                    omit_headers=omit_headers
                                    )
    if output_type == 'template':
        return TemplateRecordWriter(encode_ascii=encode_ascii,
                                    headers=headers,
                                    omit_headers=omit_headers
                                    )
    if output_type == 'csv':
        return CSVRecordWriter(encode_ascii=encode_ascii,
                               headers=headers,
                               omit_headers=omit_headers
                               )
        # TODO fix
        #out.quoting = out.quoting
        #out.quotechar = out.quotechar
        #out.lineterminator = out.lineterminator
        #out.set_escapechar = out.escapechar
    if output_type.startswith('json'):
        return JSONRecordWriter(encode_ascii=encode_ascii,
                                headers=headers,
                                omit_headers=omit_headers,
                                compact=compact,
                                include_null=include_null,
                                indent=indent,
                                sort_keys=sort_keys,
                                root='results' if output_type == 'json-root' else None,
                                array_wrapper = output_type != 'json-line'
                                )
    raise ValueError(output_type)

def main():
    data = [
        ["Alice", 25, "Engineer"],
        ["Bob", 30, "Doctor"],
        ["Carol", 28, "Data || Analyst"],
        ["Dave", 35, "Data | Engineer"],
        ["Jimbo", 22, ["Hobo", "Jerk"]],
        ["Limbo", None, ["Hobo", "流浪"]],
        ["Complex", 99, {'a': 1, 'b': [2,3]}]
    ]
    headers = [ "name", "age", "pos" ]
    for output_type in ('markdown', 'json-array', 'json-root', 'json-line', 'csv', 'template'):
        for omit_headers in [True, False]:
            for encode_ascii in [True, False]:
                for offset in [0, 2]:
                    for limit in [None, 4]:
                        for include_null in [True, False]:
                            for compact in [True, False]:
                                for indent in [0, 2, 8]:
                                    for sort_keys in [True, False]:
                                        for product in [[False, False, False], [False, False, True], [False, True, True]]:
                                            out: RecordWriter = create(output_type=output_type, encode_ascii=encode_ascii, headers=headers, compact=compact, include_null=include_null, indent=indent, sort_keys=sort_keys, omit_headers=omit_headers)
                                            # Order is important since projections can generate more than one row
                                            # It depends upon how you want to interpret the limit/offset, and that is TBD
                                            wrapper_config = {
                                                'limit': limit,
                                                'offset': offset,
                                                'product': product,
                                            }
                                            out = RecordLimiter.wrap(out, **wrapper_config)
                                            out = RecordCartesianProduct.wrap(out, **wrapper_config)
                                            print(repr(out), flush=True)
                                            print(f'{output_type}-', flush=True)
                                            if out.start():
                                                for row in data:
                                                    if not out.write(row): break
                                                out.finish()
                                            print(flush=True)

if __name__ == "__main__":
    main()
