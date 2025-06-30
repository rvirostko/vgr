"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the functions.
"""

from collections import defaultdict
from collections.abc import Sequence, Iterable
from functools import lru_cache
from itertools import zip_longest
from typing import Any, Callable
import inspect
import re

from mathpak import (
    base_name,
    compile_pattern,
    dir_name,
    encode_url,
    file_exists,
    format_duration,
    format_json,
    format_timestamp,
    int_arg,
    is_dir,
    is_file,
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
    poly_ascii,
    poly_base64_decode,
    poly_base64_encode,
    poly_bin,
    poly_bit_not,
    poly_bool,
    poly_capitalize,
    poly_casefold,
    poly_ceil,
    poly_center,
    poly_chr,
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
    poly_isfinite,
    poly_isfloat,
    poly_isidentifier,
    poly_isinf,
    poly_isint,
    poly_islist,
    poly_islower,
    poly_isnan,
    poly_isnumber,
    poly_isnumeric,
    poly_isprintable,
    poly_isspace,
    poly_isstr,
    poly_istitle,
    poly_isupper,
    poly_iszero,
    poly_join,
    poly_lastitem,
    poly_leftstr,
    poly_list,
    poly_ljust,
    poly_lookup,
    poly_lower,
    poly_max,
    poly_mean,
    poly_median,
    poly_min,
    poly_mod,
    poly_mode,
    poly_multimode,
    poly_number,
    poly_oct,
    poly_ord,
    poly_parse_bin,
    poly_parse_hex,
    poly_parse_int,
    poly_parse_oct,
    poly_pow,
    poly_pstdev,
    poly_pvariance,
    poly_repr,
    poly_reverse,
    poly_rfind,
    poly_rightstr,
    poly_rindex,
    poly_rjust,
    poly_round,
    poly_rsplit,
    poly_shl,
    poly_shorten,
    poly_shr,
    poly_sizeof,
    poly_sort,
    poly_split,
    poly_splitlines,
    poly_startswith,
    poly_stdev,
    poly_str,
    poly_strlen,
    poly_strrev,
    poly_substr,
    poly_sum,
    poly_swapcase,
    poly_title,
    poly_translate,
    poly_trunc,
    poly_type,
    poly_unique,
    poly_upper,
    poly_add,
    poly_vappend,
    poly_variance,
    poly_vbit_and,
    poly_vbit_or,
    poly_vbit_xor,
    poly_vdig,
    poly_div,
    poly_fdiv,
    poly_vlstrip,
    poly_vmatches_all,
    poly_vmatches,
    poly_mul,
    poly_vprepend,
    poly_vregex_replace,
    poly_vremoveprefix,
    poly_vremovesuffix,
    poly_vreplace,
    poly_vrstrip,
    poly_vstrip,
    poly_sub,
    poly_zfill,
    strip_nulls,
    to_json_string,
    to_json,
)

def _default_to(value: Any, default: Any) -> Any:
    """
**Returns the default if a value is _None_**

* _value_.DefaultTo(_default_)
"""
    return default if value is None else value

def _id(obj: Any) -> Any:
    """
**Returns the internal, unique ID used by the item**

* _value_.Id()
"""
    return id(obj)

def _enumerate(obj: Any, start_at: int=0) -> Any:
    """
**Create an enumeration for a collection**

* _value_.Enumerate()
* _value_.Enumerate(_start_at_)

The _start_at_ argument defines the number used in the enumerated tuple.
The default value for _start_at_ is zero.
Enumeration of values that are not collections produces an enumeration of a single entry.
Enumerating _None_ returns an empty list.
"""
    if obj is None: return []
    start_at = int_arg(start_at, "StartAt")
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        return list(enumerate(obj, start=start_at))
    return [(start_at, obj)]

def _negate(x: Any) -> Any:
    """
**Returns the negation of a value**

* _value_.Negate()

The _value_'s type determines what is returned:
* _None_ : always returns _True_
* String : returns _value_ unchanged
* Boolean : returns the logical negation
* Int and Float : return the arithmetic negation
* Lists and Dictionaries : distributed negation
"""
    if x is None: return True
    if isinstance(x, bool): return not x
    if isinstance(x, (int, float)): return -x
    if isinstance(x, (list, tuple)): return type(x)(_negate(x1) for x1 in x)
    if isinstance(x, dict): return {k: _negate(v) for k, v in x.items()}
    return x

def _slice(x: Any, start: int=None, stop: int=None, step: int=None) -> Any:
    """
**Extract a portion of a list or string**

* _value_.Slice()
* _value_.Slice(_start_)
* _value_.Slice(_start_, _stop_)
* _value_.Slice(_start_, _stop_, _step_)
"""
    start = int_arg(start, "Start") if start is not None else None
    stop = int_arg(stop, "Stop") if stop is not None else None
    step = int_arg(step, "Step") if step is not None else None
    if x is None: return None
    # Treat bytes and bytearray like strings (return same type)
    if isinstance(x, (str, bytes, bytearray)): return x[start:stop:step]
    # Accept any object that supports slicing via __getitem__
    if isinstance(x, Sequence): return list(x[start:stop:step])
    # Convert iterable to list then slice
    if isinstance(x, Iterable): return list(list(x)[start:stop:step])
    return x

def _combine_with(first: Any, *rest) -> Any:
    """
**Combine elements of collections into a list of tuples**

* _value_.CombineWith()
* _value_.CombineWith(_expresssion_ [,_expression_...])

Combines the elements of the listed collections into an array of arrays.
Each element will have the _N_th matching values joined together.
If the lists are of unequal length, _None_ values are used for the
missing items.

"""
    def normalize(x):
        return x if isinstance(x, Iterable) and not isinstance(x, (str, bytes, bytearray)) else [x]
    iterables = [normalize(first)] + [normalize(arg) for arg in rest]
    return list(zip_longest(*iterables))

def _is_empty(x: Any) -> bool:
    """
**Test a value to see if it is _empty_**

* _value_.IsEmpty()

A value is considered empty if:
* It is _None_
* It is a list that has no items
* It is a dictionary that has attributes
* It is a string that has zero length or
  consists of only space characters
* It is a number that is zero
* It is the boolean _False_
"""
    if isinstance(x, (list, tuple, dict)): return len(x) == 0
    if isinstance(x, str): return len(x) == 0 or x.isspace()
    if isinstance(x, (int, float)): return x == 0
    return x is None

def _is_not_empty(x: Any) -> bool:
    """
**Test a value to see if it is _not empty_**

* _value_.IsNotEmpty()

A value is considered empty if:
* It is a list that has one or more items
* It is a dictionary that has one or more attributes
* It is a string that consists of more than just space characters
* It is a number that is not zero
* It is the boolean _True_
"""
    if isinstance(x, (list, tuple, dict)): return len(x) > 0
    if isinstance(x, str): return len(x) > 0 and not x.isspace()
    if isinstance(x, (int, float)): return x != 0
    return x is not None

def _length(x: Any) -> bool:
    """
**Return the length of an an item**

* _value_.Length()

Returns the length of lists and strings.
For dictionaries, the number of attributes is returned.
For all other values _None_ is returned.
"""
    return len(x) if hasattr(x, '__len__') else None

def _plural(x: Any, plural: Any='s', singular: Any='') -> Any:
    """
**Return a suffix for pluralization**

* _value_.Plural()
* _value_.Plural(_plural_)
* _value_.Plural(_plural_, _singular_)

If _value_ is a number is not equal to one, or a value that
has a length that is not one, then the _plural_ value is returned.
Otherwise, the _singular_ value is returned.
The defaults arguments are _s_ and an empty string respectively.
The values for _plural_ and _signular_ can be any any values.

"""
    if isinstance(x, (int, float)):
        is_one = x == 1
    else:
        is_one = hasattr(x, "__len__") and len(x) == 1
    return singular if is_one else plural

_BUILT_IN_FUNCS = {
    "Abs":            poly_abs,
    "Add":            poly_add,
    "AppendStr":      poly_vappend,
    "ASCII":          poly_ascii,
    "Base64Decode":   poly_base64_decode,
    "Base64Encode":   poly_base64_encode,
    "BaseName":       base_name,
    "BitAnd":         poly_vbit_and,
    "BitNot":         poly_bit_not,
    "BitOr":          poly_vbit_or,
    "BitXor":         poly_vbit_xor,
    "Bool":           poly_bool,
    "Capitalize":     poly_capitalize,
    "CaseFold":       poly_casefold,
    "Ceil":           poly_ceil,
    "Center":         poly_center,
    "Centre":         poly_center,
    "Chr":            poly_chr,
    "CombineWith":    _combine_with,
    "CompilePattern": compile_pattern,
    "Contains":       poly_contains_any,
    "ContainsAll":    poly_contains_all,
    "ContainsAny":    poly_contains_any,
    "CountOf":        poly_count,
    "DefaultTo":      _default_to,
    "Dig":            poly_vdig,
    "DirectoryName":  dir_name,
    "DirName":        dir_name,
    "Div":            poly_div,
    "DivMod":         poly_divmod,
    "EncodeURL":      encode_url,
    "EndsWith":       poly_endswith,
    "Enumerate":      _enumerate,
    "ExpandTabs":     poly_expandtabs,
    "FileExists":     file_exists,
    "FindStr":        poly_find,
    "FirstItem":      poly_firstitem,
    "Float":          poly_float,
    "Floor":          poly_floor,
    "FloorDiv":       poly_fdiv,
    "Format":         poly_format,
    "FormatDuration": format_duration,
    "FormatJSON":     format_json,
    "FormatTimestamp":format_timestamp,
    "Hash":           poly_hash,
    "Id":             _id,
    "In":             poly_in,
    "IndexOf":        poly_index,
    "Int":            poly_int,
    "IsAlnum":        poly_isalnum,
    "IsAlpha":        poly_isalpha,
    "IsAscii":        poly_isascii,
    "IsBool":         poly_isbool,
    "IsDecimal":      poly_isdecimal,
    "IsDigit":        poly_isdigit,
    "IsDirectory":    is_dir,
    "IsEmpty":        _is_empty,
    "IsFile":         is_file,
    "IsFinite":       poly_isfinite,
    "IsFloat":        poly_isfloat,
    "IsIdentifier":   poly_isidentifier,
    "IsInf":          poly_isinf,
    "IsInt":          poly_isint,
    "IsList":         poly_islist,
    "IsLower":        poly_islower,
    "IsNan":          poly_isnan,
    "IsNotEmpty":     _is_not_empty,
    "IsNumber":       poly_isnumber,
    "IsNumeric":      poly_isnumeric,
    "IsPrintable":    poly_isprintable,
    "IsSpace":        poly_isspace,
    "IsStr":          poly_isstr,
    "IsTitle":        poly_istitle,
    "IsUpper":        poly_isupper,
    "IsZero":         poly_iszero,
    "Item":           poly_getitem,
    "Join":           poly_join,
    "LastItem":       poly_lastitem,
    "LeftJustify":    poly_ljust,
    "LeftShift":      poly_shl,
    "LeftStr":        poly_leftstr,
    "LeftStrip":      poly_vlstrip,
    "Len":            _length,
    "Length":         _length,
    "List":           poly_list,
    "Lookup":         poly_lookup,
    "Lower":          poly_lower,
    "Matches":        poly_vmatches,
    "MatchesAll":     poly_vmatches_all,
    "MatchesAny":     poly_vmatches,
    "Max":            poly_max,
    "MdBlockQuote":   md_blockquote,
    "MdBold":         md_bold,
    "MdCode":         md_code,
    "MdCodeBlock":    md_code_block,
    "MdHeading":      md_heading,
    "MdItalics":      md_italics,
    "MdLink":         md_link,
    "MdOrderedList":  md_ordered_list,
    "MdStrikeThrough":md_strikethrough,
    "MdUnorderedList":md_unordered_list,
    "Mean":           poly_mean,
    "Median":         poly_median,
    "Min":            poly_min,
    "Mod":            poly_mod,
    "Mode":           poly_mode,
    "Mul":            poly_mul,
    "MultiMode":      poly_multimode,
    "Negate":         _negate,
    "Number":         poly_number,
    "Ord":            poly_ord,
    "ParseBinary":    poly_parse_bin,
    "ParseHex":       poly_parse_hex,
    "ParseInt":       poly_parse_int,
    "ParseJSON":      parse_json,
    "ParseOctal":     poly_parse_oct,
    "ParseUrl":       parse_url,
    "Plural":         _plural,
    "Pow":            poly_pow,
    "PrependStr":     poly_vprepend,
    "PStdev":         poly_pstdev,
    "PVariance":      poly_pvariance,
    "RegexReplace":   poly_vregex_replace,
    "RemovePrefix":   poly_vremoveprefix,
    "RemoveSuffix":   poly_vremovesuffix,
    "ReplaceStr":     poly_vreplace,
    "Repr":           poly_repr,
    "Reverse":        poly_reverse,
    "ReverseStr":     poly_strrev,
    "RFindStr":       poly_rfind,
    "RightJustify":   poly_rjust,
    "RightShift":     poly_shr,
    "RightStr":       poly_rightstr,
    "RightStrip":     poly_vrstrip,
    "RIndexOf":       poly_rindex,
    "Round":          poly_round,
    "RSplit":         poly_rsplit,
    "ShortenStr":     poly_shorten,
    "SizeOf":         poly_sizeof,
    "Slice":          _slice,
    "Sort":           poly_sort,
    "Split":          poly_split,
    "SplitLines":     poly_splitlines,
    "StartsWith":     poly_startswith,
    "Stdev":          poly_stdev,
    "Str":            poly_str,
    "StringLen":      poly_strlen,
    "Strip":          poly_vstrip,
    "StripNulls":     strip_nulls,
    "StrLen":         poly_strlen, # a 'C'-like name
    "StrRev":         poly_strrev, # a (MS) 'C'-like name
    "Sub":            poly_sub,
    "SubStr":         poly_substr,
    "Sum":            poly_sum,
    "SwapCase":       poly_swapcase,
    "TitleCase":      poly_title,
    "ToBinary":       poly_bin,
    "ToBool":         poly_bool,
    "ToFloat":        poly_float,
    "ToHex":          poly_hex,
    "ToInt":          poly_int,
    "ToJSON":         to_json,
    "ToJSONStr":      to_json_string,
    "ToList":         poly_list,
    "ToNumber":       poly_number,
    "ToOctal":        poly_oct,
    "ToStr":          poly_str,
    "Translate":      poly_translate,
    "Trunc":          poly_trunc,
    "Type":           poly_type,
    "Unique":         poly_unique,
    "Upper":          poly_upper,
    "Variance":       poly_variance,
    "ZeroFill":       poly_zfill,
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

@lru_cache
def get_function_entries():
    return {
        name: (name.lower().replace('_', ''), (func.__doc__ or '').lower()) for name, func in _FUNC_OPS.items()
    }

@lru_cache
def get_function_names():
    return sorted(_FUNC_OPS.keys())

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

def get_function(name: str) -> tuple:
    """Get the entry for the named function: (canonical_name, function)"""
    canonical_name = _FUNC_INDEX.get(name.lower(), None)
    if canonical_name: return (canonical_name, _FUNC_OPS.get(canonical_name))
    return None

def get_function_op(name: str):
    """Given a function name get the function that implements it"""
    function = get_function(name)
    if function: return function[1]
    raise NotImplementedError(f'Function {repr(name)} not implemented') # SNO

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
