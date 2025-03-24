
# Command line for the prototype to drive the output options

import argparse

from output import CSVRecordWriter, JSONRecordWriter, MarkdownRecordWriter, TemplateRecordWriter
from output import RecordWriter, RecordLimiter, RecordCartesianProduct

def opt_name(s: str) -> str:
    return '--' + s.replace('_', '-')

def str_or_none(value):
    return None if value.lower() == "none" else literal_eval(value)

def int_or_none(value):
    if value.lower() == "none": return None
    try:
        return int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}") from e

def bool_or_none(value):
    v = value.lower()
    if v == "none": return None
    if v in {"true", "yes", "y", "on"}: return True
    if v in {"false", "no", "n", "off"}: return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")

# Metavar types
_BOOL = 'BOOL'
_CHAR = 'CHAR'
_FN = 'FILENAME'
_INT = 'INT'
_STR = 'STRING'

boolean_options = (
    ('array_wrapper', 'Output JSON as array'),
    ('auto_escape', 'Automatically escape template variables'),
    ('compact', 'JSON compact format'),
    ('include_nulls', 'Include null columns in output'),
    ('omit_headers', 'Do not add headers to output'),
    ('sort_keys', 'JSON sort output keys'),
)

string_options = (
    ('delimiter', _CHAR, 'CSV field delimiter'),
    ('escapechar', _CHAR, 'CSV escape character'),
    ('lineterminator', _STR, 'CSV line terminator'),
    ('quotechar', _CHAR, 'CSV quote character'),
    ('root', _STR, 'JSON Root element'),
    ('template_file', _FN, 'Template file'),
)

numeric_options = (
    ('limit', _INT, 'Maximum number of output records'),
    ('offset', _INT, 'Skip the first N output records'),
    ('indent', _INT, 'JSON indent level'),
)

def add_bool_arg(p, opt: tuple):
    name, opt_help = opt
    p.add_argument(opt_name(name), metavar=_BOOL, const=True, nargs='?', type=bool_or_none, default=argparse.SUPPRESS, help=opt_help)

def add_arg(p, type_func, opt: tuple):
    name, opt_metavar, opt_help = opt
    p.add_argument(opt_name(name), metavar=opt_metavar, nargs=1, type=type_func, default=argparse.SUPPRESS, help=opt_help)

def literal_eval(s: str) -> str:
     return None if s is None else s

def move_opt(key: str, source: dict, target: dict):
    if key in source: target[key] = source.pop(key)

def product_xform(value):
    """Transform numeric refs into an array of bools"""
    if value is None: return None
    indices = {int(v) - 1 for v in value if 0 <= int(v) <= 64}
    # Find max index (default -1 for empty input)
    max_index = max(indices, default=-1)
    return [i in indices for i in range(max_index + 1)]

def adjust_product(product: list, length: int):
    """Extend or clip product array to match length of header array"""
    if product is None: return None
    return product[:length] + [False] * (length - len(product))

def fix_single_value_args(input_dict):
    """vars() transformation leaves these arrays of one for opts"""
    for key, value in input_dict.items():
        if isinstance(value, list) and len(value) == 1:
            input_dict[key] = value[0]  # Convert list with one element to the element itself
    return input_dict

def create_writer(otype: str, opts: dict, controls: dict) -> RecordWriter:
    """Copied from stmt_select code: only supports stdout"""
    writer: RecordWriter = None
    if otype == 'csv':
        writer = CSVRecordWriter(**opts)
    elif otype == 'json':
        writer = JSONRecordWriter(**opts)
    elif otype == 'markdown':
        writer = MarkdownRecordWriter(**opts)
    elif otype == 'template':
        writer = TemplateRecordWriter(**opts)
    else:
        raise NotImplementedError(f'Output type {repr(otype)} not implemented')
    # Order is important since projections can generate more than one row
    # It depends upon how you want to interpret the limit/offset, and that is TBD
    writer = RecordLimiter.wrap(writer, **controls)
    writer = RecordCartesianProduct.wrap(writer, **controls)
    return writer

def extract_output_config(args) -> tuple:
    """Takes a set of generic args and extracts the info used by the output/writer"""
    opts = vars(args)
    product = opts.pop('product') if 'product' in opts else None
    fix_single_value_args(opts)
    if product: opts['product'] = product
    otype = opts.pop('output')
    output_keys = [t[0] for t in boolean_options + numeric_options + string_options] + ['output', 'quoting', 'template_type', 'product']
    opts = {k: v for k, v in opts.items() if k in output_keys}
    controls = {}
    move_opt('limit', opts, controls)
    move_opt('offset', opts, controls)
    if product:
        move_opt('product', opts, controls)
        controls['product'] = product_xform(controls.get('product'))
    return (otype, opts, controls)

def add_output_opts(parser):
    """Adds all the options used to control output to the parser"""
    parser.add_argument('--output', choices=['json', 'markdown', 'csv', 'template'],
                        default='csv', help='Output format (default: csv)'
                        )
    parser.add_argument('--quoting', choices=['all', 'minimal', 'none'],
                        default=argparse.SUPPRESS, help='CSV quoting behavior'
                        )
    parser.add_argument('--template-type', choices=['record', 'batch'],
                        default=argparse.SUPPRESS, help='Template output type'
                        )
    parser.add_argument("--product", nargs="+", type=int,
                        default=argparse.SUPPRESS, help='Produce cartesian product of numbered columns'
                        )
    for opt in boolean_options: add_bool_arg(parser, opt)
    for opt in string_options: add_arg(parser, str_or_none, opt)
    for opt in numeric_options: add_arg(parser, int_or_none, opt)

def main():
    """Stand-in for the app"""
    parser = argparse.ArgumentParser()
    add_output_opts(parser)
    args = parser.parse_args()

    otype, opts, controls = extract_output_config(args)

    # TODO add headers to opts
    opts['headers'] = []
    if 'product' in controls:
        controls['product'] = adjust_product(controls.get('product'), len(opts['headers']))
    writer = create_writer(otype, opts, controls)
    print(repr(writer))

if __name__ == '__main__':
    main()
