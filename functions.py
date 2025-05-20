"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the functions.
"""

import re
from collections import defaultdict
import inspect
from typing import Any, Callable

from mathpak import (
    compile_pattern,
    encode_url,
    format_json,
    md_blockquote,
    md_bold,
    md_code_block,
    md_code,
    md_heading,
    md_italics,
    md_link,
    md_ordered_list,
    md_strikethrough,
    md_unordered_list,
    parse_json,
    parse_url,
    poly_abs,
    poly_base64_decode,
    poly_base64_encode,
    poly_bin,
    poly_bit_not,
    poly_bool,
    poly_capitalize,
    poly_casefold,
    poly_ceil,
    poly_center,
    poly_contains_all,
    poly_contains_any,
    poly_count,
    poly_divmod,
    poly_endswith,
    poly_expandtabs,
    poly_find,
    poly_firstitem,
    poly_float,
    poly_floor,
    poly_format,
    poly_getitem,
    poly_hash,
    poly_hex,
    poly_in,
    poly_index,
    poly_int,
    poly_isalnum,
    poly_isalpha,
    poly_isascii,
    poly_isbool,
    poly_isdecimal,
    poly_isdigit,
    poly_isempty,
    poly_isfloat,
    poly_isidentifier,
    poly_isint,
    poly_islist,
    poly_islower,
    poly_isnumber,
    poly_isnumeric,
    poly_isprintable,
    poly_isspace,
    poly_isstr,
    poly_istitle,
    poly_isupper,
    poly_join,
    poly_lastitem,
    poly_leftstr,
    poly_len,
    poly_list,
    poly_ljust,
    poly_lookup,
    poly_lower,
    poly_mod,
    poly_number,
    poly_oct,
    poly_parse_bin,
    poly_parse_hex,
    poly_parse_int,
    poly_parse_oct,
    poly_pow,
    poly_repr,
    poly_rfind,
    poly_rightstr,
    poly_rindex,
    poly_rjust,
    poly_round,
    poly_rsplit,
    poly_shl,
    poly_shr,
    poly_sizeof,
    poly_sort,
    poly_split,
    poly_splitlines,
    poly_startswith,
    poly_str,
    poly_substr,
    poly_swapcase,
    poly_title,
    poly_translate,
    poly_trunc,
    poly_type,
    poly_unique,
    poly_upper,
    poly_vadd,
    poly_vappend,
    poly_vbit_and,
    poly_vbit_or,
    poly_vbit_xor,
    poly_vdig,
    poly_vdiv,
    poly_vfdiv,
    poly_vlstrip,
    poly_vmatches_all,
    poly_vmatches,
    poly_vmul,
    poly_vprepend,
    poly_vregex_replace,
    poly_vremoveprefix,
    poly_vremovesuffix,
    poly_vreplace,
    poly_vrstrip,
    poly_vstrip,
    poly_vsub,
    poly_zfill,
    strip_nulls,
    to_json_string,
    to_json,
)

def _default_to(value: Any, default: Any) -> Any:
    """Returns a default value if the argument is None.

* Fluent: _expression_.DefaultTo(_expression_)
* Procedural: DefaultTo(_expression_, _expression_)
"""
    return default if value is None else value

_BUILT_IN_FUNCS = {
  "Abs": poly_abs,
  "Add": poly_vadd,
  "AppendStr": poly_vappend,
  "Base64Decode": poly_base64_decode,
  "Base64Encode": poly_base64_encode,
  "BitAnd": poly_vbit_and,
  "BitNot": poly_bit_not,
  "BitOr": poly_vbit_or,
  "BitXor": poly_vbit_xor,
  "Bool": poly_bool,
  "Capitalize": poly_capitalize,
  "CaseFold": poly_casefold,
  "Ceil": poly_ceil,
  "Center": poly_center,
  "CompilePattern": compile_pattern,
  "Contains": poly_contains_any,
  "ContainsAll": poly_contains_all,
  "ContainsAny": poly_contains_any,
  "CountOf": poly_count,
  "DefaultTo": _default_to,
  "Dig": poly_vdig,
  "Div": poly_vdiv,
  "DivMod": poly_divmod,
  "EncodeURL": encode_url,
  "EndsWith": poly_endswith,
  "ExpandTabs": poly_expandtabs,
  "FindStr": poly_find,
  "FirstItem": poly_firstitem,
  "Float": poly_float,
  "Floor": poly_floor,
  "FloorDiv": poly_vfdiv,
  "Format": poly_format,
  "FormatJSON": format_json,
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
  "Join": poly_join,
  "LastItem": poly_lastitem,
  "LeftJustify": poly_ljust,
  "LeftShift": poly_shl,
  "LeftStr": poly_leftstr,
  "LeftStrip": poly_vlstrip,
  "Len": poly_len,
  "Length": poly_len,
  "List": poly_list,
  "Lookup": poly_lookup,
  "Lower": poly_lower,
  "Matches": poly_vmatches,
  "MatchesAll": poly_vmatches_all,
  "MatchesAny": poly_vmatches,
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
  "Mul": poly_vmul,
  "Number": poly_number,
  "ParseBinary": poly_parse_bin,
  "ParseHex": poly_parse_hex,
  "ParseInt": poly_parse_int,
  "ParseJSON": parse_json,
  "ParseOctal": poly_parse_oct,
  "ParseUrl": parse_url,
  "Pow": poly_pow,
  "PrependStr": poly_vprepend,
  "RegexReplace": poly_vregex_replace,
  "RemovePrefix": poly_vremoveprefix,
  "RemoveSuffix": poly_vremovesuffix,
  "ReplaceStr": poly_vreplace,
  "Repr": poly_repr,
  "RFindStr": poly_rfind,
  "RightJustify": poly_rjust,
  "RightShift": poly_shr,
  "RightStr": poly_rightstr,
  "RightStrip": poly_vrstrip,
  "RIndexOf": poly_rindex,
  "Round": poly_round,
  "RSplit": poly_rsplit,
  "SizeOf": poly_sizeof,
  "Sort": poly_sort,
  "Split": poly_split,
  "SplitLines": poly_splitlines,
  "StartsWith": poly_startswith,
  "Str": poly_str,
  "Strip": poly_vstrip,
  "StripNulls": strip_nulls,
  "Sub": poly_vsub,
  "SubStr": poly_substr,
  "SwapCase": poly_swapcase,
  "TitleCase": poly_title,
  "ToBinary": poly_bin,
  "ToBool": poly_bool,
  "ToFloat": poly_float,
  "ToHex": poly_hex,
  "ToInt": poly_int,
  "ToJSON": to_json,
  "ToJSONStr": to_json_string,
  "ToNumber": poly_number,
  "ToOctal": poly_oct,
  "ToString": poly_str,
  "Translate": poly_translate,
  "Trunc": poly_trunc,
  "Type": poly_type,
  "Unique": poly_unique,
  "Upper": poly_upper,
  "ZeroFill": poly_zfill,
}

# Binds a (pretty) name to the function to be executed
# Additionally, we should use functions here rather than lambdas
# so we can grab the __DOC__ for help functions.
_FUNC_OPS = {}

# This index provides a way to find functions independent of case.
# Use get_function_op() to find entries.
# It's also used to generate the big regex to identify function names
_FUNC_INDEX = {}

def _to_snake_case(s: str) -> str:
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', s)  # insert _ before A-Z if preceded by lowercase or digit
    s = re.sub(r'(?<=[A-Z])([A-Z][a-z])', r'_\1', s)  # handle acronym boundary: XMLParser -> XML_Parser
    return s.lower()

def add_builtin_functions() -> None:
    for name, function in _BUILT_IN_FUNCS.items(): add_function('built-in', name, function)

def add_function(extn_name: str, name: str, function: Callable) -> None:
    lc = name.lower()
    if lc in _FUNC_INDEX:
        raise ValueError(f'Extension {repr(extn_name)} tried to redefine {repr(name)}')
    _FUNC_OPS[name] = function
    _FUNC_INDEX[lc] = name
    _FUNC_INDEX[_to_snake_case(name)] = name

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
