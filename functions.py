"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the functions.
"""

import re
from collections import defaultdict
import inspect
from typing import Any

from mathpak import poly_abs, poly_vadd, poly_vappend, poly_vbit_and, poly_vbit_or, poly_vbit_xor
from mathpak import poly_bit_not, poly_bool, poly_capitalize, poly_casefold
from mathpak import poly_ceil, poly_count, poly_vdiv
from mathpak import poly_endswith, poly_expandtabs, poly_firstitem, poly_float, poly_vfdiv
from mathpak import poly_floor, poly_hash, poly_in, poly_index
from mathpak import poly_int, poly_isalnum, poly_isalpha, poly_isascii, poly_isbool
from mathpak import poly_isdecimal, poly_isdigit, poly_isempty, poly_isfloat
from mathpak import poly_isidentifier, poly_isint, poly_islower, poly_islist, poly_isnumber
from mathpak import poly_isprintable, poly_isnumeric, poly_isspace
from mathpak import poly_isstr, poly_istitle, poly_isupper, poly_getitem
from mathpak import poly_lastitem, poly_shl, poly_leftstr, poly_vlstrip, poly_len, poly_list
from mathpak import poly_lookup, poly_lower, poly_vmatches, poly_vmatches_all, poly_mod, poly_vmul, poly_number
from mathpak import poly_pow, poly_vprepend, poly_vremoveprefix, poly_vremovesuffix
from mathpak import poly_vreplace, poly_repr, poly_shr, poly_rightstr, poly_vrstrip, poly_round
from mathpak import poly_rindex, poly_sizeof, poly_rsort, poly_sort, poly_startswith
from mathpak import poly_str, poly_vstrip, poly_vsub, poly_substr, poly_swapcase, poly_title
from mathpak import poly_translate, poly_trunc, poly_type, poly_unique, poly_upper
from mathpak import duration_to_ms, ms_to_duration, parse_url, compile_pattern
from mathpak import md_blockquote, md_bold, md_code, md_code_block, md_heading, md_italics, md_strikethrough
from mathpak import md_link, md_ordered_list, md_unordered_list
from mathpak import poly_format, poly_vregex_replace, poly_split, poly_rsplit
from mathpak import poly_contains_any, poly_contains_all

def _default_to(value: Any, default: Any) -> Any:
    """Returns a default value if the argument is None.

* Fluent: _expression_.DefaultTo(_expression_)
* Procedural: DefaultTo(_expression_, _expression_)
"""
    return default if value is None else value

# Binds a (pretty) name to the function to be executed
# Additionally, we should use functions here rather than lambdas
# so we can grab the __DOC__ for help functions.
#"Attr": ???,                       # TODO see attrgetter, better name?
_FUNC_OPS = {
  "Abs": poly_abs,
  "Add": poly_vadd,
  "AppendStr": poly_vappend,
  "BitAnd": poly_vbit_and,
  "BitNot": poly_bit_not,
  "BitOr": poly_vbit_or,
  "BitXor": poly_vbit_xor,
  "Bool": poly_bool,
  "Capitalize": poly_capitalize,
  "CaseFold": poly_casefold,
  "Ceil": poly_ceil,
  "CompilePattern": compile_pattern,
  "Contains": poly_contains_any,
  "ContainsAny": poly_contains_any,
  "ContainsAll": poly_contains_all,
  "CountOf": poly_count,
  "DefaultTo": _default_to,
  "Div": poly_vdiv,
  "DurationToMs": duration_to_ms, # Vault specific
  "EndsWith": poly_endswith,
  "ExpandTabs": poly_expandtabs,
  "FirstItem": poly_firstitem,
  "Float": poly_float,
  "Floor": poly_floor,
  "FloorDiv": poly_vfdiv,
  "Format": poly_format,
  "Hash": poly_hash,
  "In": poly_in,
  "IndexOf": poly_index,
  "Int": poly_int,
  "IsAlnum": poly_isalnum,
  "IsAlpha": poly_isalpha,
  "IsAscii": poly_isascii,
  "IsBool": poly_isbool,
  "IsDecimal": poly_isdecimal,
  "IsDigit": poly_isdigit,
  "IsEmpty": poly_isempty,
  "IsFloat": poly_isfloat,
  "IsIdentifier":  poly_isidentifier,
  "IsInt": poly_isint,
  "IsList": poly_islist,
  "IsLower": poly_islower,
  "IsNumber": poly_isnumber,
  "IsNumeric": poly_isnumeric,
  "IsPrintable": poly_isprintable,
  "IsSpace": poly_isspace,
  "IsStr": poly_isstr,
  "IsTitle": poly_istitle,
  "IsUpper": poly_isupper,
  "Item": poly_getitem,
  "LastItem": poly_lastitem,
  "LeftShift": poly_shl,
  "LeftStr": poly_leftstr,
  "LeftStrip": poly_vlstrip,
  "Len": poly_len,
  "Length": poly_len,
  "List": poly_list,
  "Lookup": poly_lookup,
  "Lower": poly_lower,
  "Matches": poly_vmatches,
  "MatchesAny": poly_vmatches,
  "MatchesAll": poly_vmatches_all,
  "MdBlockQuote": md_blockquote,
  "MdBold": md_bold,
  "MdCode": md_code,
  "MdCodeBlock": md_code_block,
  "MdHeading": md_heading,
  "MdItalics": md_italics,
  "MdLink": md_link,
  "MdOrderedList": md_ordered_list,
  "MdStrikeThrough": md_strikethrough,
  "MdUnorderedList": md_unordered_list,
  "Mod": poly_mod,
  "MsToDuration": ms_to_duration, # Vault specific
  "Mul": poly_vmul,
  "Number": poly_number,
  "ParseUrl": parse_url,
  "Pow": poly_pow,
  "PrependStr": poly_vprepend,
  "RemovePrefix": poly_vremoveprefix,
  "RemoveSuffix": poly_vremovesuffix,
  "ReplaceStr": poly_vreplace,
  "RegexReplace": poly_vregex_replace,
  "Repr": poly_repr,
  "RightShift": poly_shr,
  "RightStr": poly_rightstr,
  "RightStrip": poly_vrstrip,
  "RIndexOf": poly_rindex,
  "Round": poly_round,
  "RSplit": poly_rsplit,
  "RSort": poly_rsort,
  "SizeOf": poly_sizeof,
  "Sort": poly_sort,
  "Split": poly_split,
  "StartsWith": poly_startswith,
  "Str": poly_str,
  "Strip": poly_vstrip,
  "Sub": poly_vsub,
  "SubStr": poly_substr,
  "SwapCase": poly_swapcase,
  "TitleCase": poly_title,
  "Translate": poly_translate,
  "Trunc": poly_trunc,
  "Type": poly_type,
  "Unique": poly_unique,
  "Upper": poly_upper,
}

# This index provides a way to find functions independent of case.
# Use get_function_op() to find entries.
# It's also used to generate the big regex to identify function names
_FUNC_INDEX = {k.lower(): k for k in _FUNC_OPS} | { re.sub(r'([a-z])([A-Z])', r'\1_\2', k).lower(): k for k in _FUNC_OPS  }

# The max value of an arg range when we have variable arguments
_IS_VARARGS = float('inf')

def get_function_op(name: str):
    """Given a function name get the function that implements it"""
    rc = _FUNC_OPS.get(_FUNC_INDEX.get(name.lower()), None)
    if rc: return rc
    raise NotImplementedError(f'Function {name} not implemented') # SNO

def get_function_defs(w: int=99) -> str:
    """Dynamically generate the LARK patterns for functions based on our dictionary"""
    w = str(w)
    # Group the functions acording to their argument counts
    # Take into account alias found in _FUNC_INDEX
    func_groups = defaultdict(list)
    for name, op in _FUNC_OPS.items():
        arg_range = get_arg_range(op)
        func_groups[arg_range].append(name)
        for alias in [k for k, v in _FUNC_INDEX.items() if v == name]:
            if alias != name.lower():
                func_groups[arg_range].append(alias)
    fnames = {}
    rc = ''
    # Generate the list of function names per arg count group
    for (min_args, max_args) in sorted(func_groups):
        label = 'FNAME'
        if min_args == max_args:
            label += str(min_args)
        else:
            label += f'{min_args}_{"N" if max_args == _IS_VARARGS else max_args}'
        fnames[(min_args, max_args)] = label
        # We emit each by-arg-length group as a regex designed to eliminate
        # "prefix" problems. First we order the names longest to shortest, then end
        # the pattern in such as way that we look ahead for the open paren, but don't capture it.
        rc += '\n' + label + '.' + w + ': ' + '/('
        rc += '|'.join(key for key in sorted(func_groups[(min_args, max_args)], key=lambda x: (-len(x), x)))
        rc += ')\\s*(?=[(])/i'
    first = True
    # The function rule is a combination of the by-arg-length names and a pattern for their argument count
    for (min_args, max_args), label in fnames.items():
        if first:
            rc += '\nfunction.' + w + ': '
            first = False
        else:
            rc += '    | '
        rc += label + ' _LPAREN'
        arg_count = 0
        # Required arguments patterns
        if min_args > 0:
            rc += ' expr'
            arg_count += 1
            for _ in range(min_args - 1):
                rc += ' _COMMA expr'
                arg_count += 1
        # Do we have any optional arguments?
        if arg_count < max_args:
            if min_args == 0:
                rc += ' (expr'
                max_args = max_args if max_args == _IS_VARARGS else (max_args - 1)
            if max_args == _IS_VARARGS:
                rc += ' (_COMMA expr)*'
            else:
                while arg_count < max_args:
                    rc += ' (_COMMA expr)?'
                    arg_count += 1
            rc += ")?" if min_args == 0 else ''
        rc +=  ' _RPAREN\n'
    return rc.strip()

def get_arg_range(op) -> tuple:
    """Get the argument range for the function definition in the grammar"""
    if op is None: raise ValueError('Expected a function, but got None')
    # Get the signature of the function
    sig = inspect.signature(op)
    req_args = 0
    opt_args = 0
    positional = False
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            positional = True
        else:
            if param.default == inspect.Parameter.empty:
                req_args += 1
            else:
                opt_args += 1
    # because our functions are applied to something
    # and we want the grammar signature
    req_args -= 1
    if req_args < 0: raise ValueError(f'{op} : {req_args}') # SNO
    return (req_args, _IS_VARARGS if positional else (req_args + opt_args))
