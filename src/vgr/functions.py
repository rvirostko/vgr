"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the functions.
"""

from collections import defaultdict
from functools import lru_cache
from typing import Any, Callable
import inspect

from .builtins import (
    base_name,
    build_list,
    compile_pattern,
    default_to,
    dir_name,
    encode_url,
    file_exists,
    format_duration,
    format_json,
    format_timestamp,
    is_dir,
    is_file,
    md_blockquote,
    md_strong,
    md_code_block,
    md_code,
    md_heading,
    md_emphasis,
    md_link,
    md_ordered_list,
    md_strikethrough,
    md_unordered_list,
    parse_url,
    poly_abs,
    poly_add,
    poly_append,
    poly_apply,
    poly_ascii,
    poly_base64_decode,
    poly_base64_encode,
    poly_between,
    poly_bin,
    poly_bit_and,
    poly_bit_not,
    poly_bit_or,
    poly_bit_xor,
    poly_bool,
    poly_capitalize,
    poly_casefold,
    poly_ceil_multiple,
    poly_ceil,
    poly_center,
    poly_checksum,
    poly_chr,
    poly_clamp,
    poly_clear_bit,
    poly_clone,
    poly_combine_lists,
    poly_combine_using,
    poly_contains_all,
    poly_contains_any,
    poly_count_leading_zeros,
    poly_count_ones,
    poly_count_trailing_zeros,
    poly_count_zeros,
    poly_count,
    poly_dict_create,
    poly_div,
    poly_divmod,
    poly_endswith,
    poly_enumerate,
    poly_eq,
    poly_expandtabs,
    poly_extract_bits,
    poly_false,
    poly_fdiv,
    poly_findstr,
    poly_firstitem,
    poly_float,
    poly_floor_multiple,
    poly_floor,
    poly_format,
    poly_ge,
    poly_getitem,
    poly_getkeys,
    poly_getkeyvalue,
    poly_getvalues,
    poly_gt,
    poly_hash,
    poly_hex_decode,
    poly_hex_encode,
    poly_hex,
    poly_highest_one_bit,
    poly_id,
    poly_imatches,
    poly_in,
    poly_index,
    poly_int,
    poly_isalnum,
    poly_isalpha,
    poly_isascii,
    poly_isbool,
    poly_isdecimal,
    poly_isdict,
    poly_isdigit,
    poly_isempty,
    poly_iseven,
    poly_isfinite,
    poly_isfloat,
    poly_isinf,
    poly_isint,
    poly_islist,
    poly_islower,
    poly_isnan,
    poly_isnegative,
    poly_isnone,
    poly_isnotnone,
    poly_isnumber,
    poly_isnumeric,
    poly_isodd,
    poly_ispattern,
    poly_ispositive,
    poly_isprintable,
    poly_isspace,
    poly_isstr,
    poly_istitle,
    poly_isupper,
    poly_iszero,
    poly_join,
    poly_lastitem,
    poly_le,
    poly_leftstr,
    poly_length,
    poly_list_append,
    poly_list_insert,
    poly_list_prepend,
    poly_list_remove_first,
    poly_list_remove_last,
    poly_list_remove,
    poly_list_replace,
    poly_list,
    poly_ljust,
    poly_lookupitem,
    poly_lower,
    poly_lowest_one_bit,
    poly_lstrip,
    poly_lt,
    poly_matches_all,
    poly_matches,
    poly_max,
    poly_mean,
    poly_median,
    poly_min,
    poly_mod,
    poly_mode,
    poly_mul,
    poly_multimode,
    poly_ne,
    poly_negate,
    poly_not_imatch,
    poly_not_in,
    poly_not_match,
    poly_not_empty,
    poly_number,
    poly_oct,
    poly_ord,
    poly_parse_bin,
    poly_parse_csv,
    poly_parse_hcl,
    poly_parse_hex,
    poly_parse_ini,
    poly_parse_int,
    poly_parse_json,
    poly_parse_oct,
    poly_parse_yaml,
    poly_plural,
    poly_pow,
    poly_pred,
    poly_prepend,
    poly_pstdev,
    poly_pvariance,
    poly_regex_replace,
    poly_removekey,
    poly_removeprefix,
    poly_removesuffix,
    poly_replace,
    poly_repr,
    poly_reverse,
    poly_reverse_bits,
    poly_reverse_bytes,
    poly_rfindstr,
    poly_rightstr,
    poly_rindex,
    poly_rjust,
    poly_rotate_left,
    poly_rotate_right,
    poly_round_multiple,
    poly_round,
    poly_rsplit,
    poly_rstrip,
    poly_set_bit,
    poly_set_bits,
    poly_setkeyvalue,
    poly_shl,
    poly_shorten,
    poly_shr,
    poly_sign,
    poly_slice,
    poly_sort,
    poly_split,
    poly_splitlines,
    poly_startswith,
    poly_stdev,
    poly_str,
    poly_strip,
    poly_stringlen,
    poly_reversestr,
    poly_sub,
    poly_substr,
    poly_succ,
    poly_sum,
    poly_swapcase,
    poly_is_bit_set,
    poly_title,
    poly_toggle_bit,
    poly_translate,
    poly_true,
    poly_trunc,
    poly_type,
    poly_unique,
    poly_upper,
    poly_variance,
    poly_zfill,
    remove_file,
    strip_nulls,
    time_now,
)
from .vgr_callable import VgrCallable

# Note: This needs to stay here because
# builtins doesn't know about VgrCallable
def _is_function(obj: Any=None) -> Any:
    """
**Is a value a function**

* IsFunction(*value*)
* *value*.IsFunction()

```vgr
None.IsFunction() → False
Set f(x) -> x+1
f.IsFunction() → True
```
"""
    return isinstance(obj, VgrCallable)

_BUILT_IN_FUNCS: dict[str, Callable[..., Any]] = {
    "Abs":            poly_abs,
    "Add":            poly_add,
    "AppendStr":      poly_append,
    "Apply":          poly_apply,
    "ASCII":          poly_ascii,
    "Base64Decode":   poly_base64_decode,
    "Base64Encode":   poly_base64_encode,
    "BaseName":       base_name,
    "BitAnd":         poly_bit_and,
    "BitNot":         poly_bit_not,
    "BitOr":          poly_bit_or,
    "BitXor":         poly_bit_xor,
    "Capitalize":     poly_capitalize,
    "CaseFold":       poly_casefold,
    "Ceil":           poly_ceil,
    "CeilMultiple":   poly_ceil_multiple,
    "Center":         poly_center,
    "Checksum":       poly_checksum,
    "Chr":            poly_chr,
    "Clamp":          poly_clamp,
    "ClearBit":       poly_clear_bit,
    "Clone":          poly_clone,
    "CombineLists":   poly_combine_lists,
    "CombineUsing":   poly_combine_using,
    "CompilePattern": compile_pattern,
    "ContainsAll":    poly_contains_all,
    "ContainsAny":    poly_contains_any,
    "CountLeadingZeroBits": poly_count_leading_zeros,
    "CountOf":        poly_count,
    "CountOneBits":   poly_count_ones,
    "CountTrailingZeroBits": poly_count_trailing_zeros,
    "CountZeroBits":  poly_count_zeros,
    "DefaultTo":      default_to,
    "Dictionary":     poly_dict_create,
    "DirectoryName":  dir_name,
    "Div":            poly_div,
    "DivMod":         poly_divmod,
    "DoesNotIMatch":  poly_not_imatch,
    "DoesNotMatch":   poly_not_match,
    "EncodeUrl":      encode_url,
    "EndsWith":       poly_endswith,
    "Enumerate":      poly_enumerate,
    "ExpandTabs":     poly_expandtabs,
    "ExtractBits":    poly_extract_bits,
    "FileExists":     file_exists,
    "FindStr":        poly_findstr,
    "FirstItem":      poly_firstitem,
    "Floor":          poly_floor,
    "FloorDiv":       poly_fdiv,
    "FloorMultiple":  poly_floor_multiple,
    "Format":         poly_format,
    "FormatDuration": format_duration,
    "FormatJson":     format_json,
    "FormatTimestamp":format_timestamp,
    "GetKeys":        poly_getkeys,
    "GetKeyValue":    poly_getkeyvalue,
    "GetValues":      poly_getvalues,
    "Hash":           poly_hash,
    "HexDecode":      poly_hex_decode,
    "HexEncode":      poly_hex_encode,
    "HighestOneBit":  poly_highest_one_bit,
    "Id":             poly_id,
    "IMatches":       poly_imatches,
    "IndexOf":        poly_index,
    "IsAlpha":        poly_isalpha,
    "IsAlphaNumeric": poly_isalnum,
    "IsAscii":        poly_isascii,
    "IsBetween":      poly_between,
    "IsBitSet":       poly_is_bit_set,
    "IsBoolean":      poly_isbool,
    "IsDecimal":      poly_isdecimal,
    "IsDictionary":   poly_isdict,
    "IsDigit":        poly_isdigit,
    "IsDirectory":    is_dir,
    "IsEmpty":        poly_isempty,
    "IsEqualTo":      poly_eq,
    "IsEven":         poly_iseven,
    "IsFalse":        poly_false,
    "IsFile":         is_file,
    "IsFinite":       poly_isfinite,
    "IsFloat":        poly_isfloat,
    "IsFunction":     _is_function,
    "IsGreaterThan":  poly_gt,
    "IsIn":           poly_in,
    "IsInf":          poly_isinf,
    "IsInteger":      poly_isint,
    "IsLessThan":     poly_lt,
    "IsList":         poly_islist,
    "IsLower":        poly_islower,
    "IsNan":          poly_isnan,
    "IsNegative":     poly_isnegative,
    "IsNone":         poly_isnone,
    "IsNotEmpty":     poly_not_empty,
    "IsNotEqualTo":   poly_ne,
    "IsNotGreaterThan": poly_le,
    "IsNotIn":        poly_not_in,
    "IsNotLessThan":  poly_ge,
    "IsNotNone":      poly_isnotnone,
    "IsNumber":       poly_isnumber,
    "IsNumeric":      poly_isnumeric,
    "IsOdd":          poly_isodd,
    "IsPattern":      poly_ispattern,
    "IsPositive":     poly_ispositive,
    "IsPrintable":    poly_isprintable,
    "IsSpace":        poly_isspace,
    "IsString":       poly_isstr,
    "IsTitle":        poly_istitle,
    "IsTrue":         poly_true,
    "IsUpper":        poly_isupper,
    "IsZero":         poly_iszero,
    "Item":           poly_getitem,
    "Join":           poly_join,
    "LastItem":       poly_lastitem,
    "LeftJustify":    poly_ljust,
    "LeftShift":      poly_shl,
    "LeftStr":        poly_leftstr,
    "LeftStrip":      poly_lstrip,
    "Length":         poly_length,
    "List":           build_list,
    "ListAppend":     poly_list_append,
    "ListInsert":     poly_list_insert,
    "ListPrepend":    poly_list_prepend,
    "ListRemove":     poly_list_remove,
    "ListRemoveFirst":poly_list_remove_first,
    "ListRemoveLast": poly_list_remove_last,
    "ListReplace":    poly_list_replace,
    "LookupItem":     poly_lookupitem,
    "Lower":          poly_lower,
    "LowestOneBit":   poly_lowest_one_bit,
    "Matches":        poly_matches,
    "MatchesAll":     poly_matches_all,
    "Max":            poly_max,
    "MdBlockQuote":   md_blockquote,
    "MdCode":         md_code,
    "MdCodeBlock":    md_code_block,
    "MdEmphasis":     md_emphasis,
    "MdHeading":      md_heading,
    "MdLink":         md_link,
    "MdOrderedList":  md_ordered_list,
    "MdStrikeThrough":md_strikethrough,
    "MdStrong":       md_strong,
    "MdUnorderedList":md_unordered_list,
    "Mean":           poly_mean,
    "Median":         poly_median,
    "Min":            poly_min,
    "Mod":            poly_mod,
    "Mode":           poly_mode,
    "Mul":            poly_mul,
    "MultiMode":      poly_multimode,
    "Negate":         poly_negate,
    "Not":            poly_false,
    "Ord":            poly_ord,
    "ParseBinary":    poly_parse_bin,
    "ParseCSV":       poly_parse_csv,
    "ParseHCL":       poly_parse_hcl,
    "ParseHex":       poly_parse_hex,
    "ParseINI":       poly_parse_ini,
    "ParseInt":       poly_parse_int,
    "ParseJSON":      poly_parse_json,
    "ParseOctal":     poly_parse_oct,
    "ParseUrl":       parse_url,
    "ParseYAML":      poly_parse_yaml,
    "Plural":         poly_plural,
    "Pow":            poly_pow,
    "Pred":           poly_pred,
    "PrependStr":     poly_prepend,
    "PStdev":         poly_pstdev,
    "PVariance":      poly_pvariance,
    "RegexReplace":   poly_regex_replace,
    "RemoveFile":     remove_file,
    "RemoveKey":      poly_removekey,
    "RemovePrefix":   poly_removeprefix,
    "RemoveSuffix":   poly_removesuffix,
    "ReplaceStr":     poly_replace,
    "Repr":           poly_repr,
    "Reverse":        poly_reverse,
    "ReverseStr":     poly_reversestr,
    "ReverseBits":    poly_reverse_bits,
    "ReverseBytes":   poly_reverse_bytes,
    "RFindStr":       poly_rfindstr,
    "RightJustify":   poly_rjust,
    "RightShift":     poly_shr,
    "RightStr":       poly_rightstr,
    "RightStrip":     poly_rstrip,
    "RIndexOf":       poly_rindex,
    "RotateLeft":     poly_rotate_left,
    "RotateRight":    poly_rotate_right,
    "Round":          poly_round,
    "RoundMultiple":  poly_round_multiple,
    "RSplit":         poly_rsplit,
    "SetBit":         poly_set_bit,
    "SetBits":        poly_set_bits,
    "SetKeyValue":    poly_setkeyvalue,
    "ShortenStr":     poly_shorten,
    "Sign":           poly_sign,
    "Slice":          poly_slice,
    "Sort":           poly_sort,
    "Split":          poly_split,
    "SplitLines":     poly_splitlines,
    "StartsWith":     poly_startswith,
    "Stdev":          poly_stdev,
    "StringLen":      poly_stringlen,
    "Strip":          poly_strip,
    "StripNulls":     strip_nulls,
    "Sub":            poly_sub,
    "SubStr":         poly_substr,
    "Succ":           poly_succ,
    "Sum":            poly_sum,
    "SwapCase":       poly_swapcase,
    "Timestamp":      time_now,
    "TitleCase":      poly_title,
    "ToBinary":       poly_bin,
    "ToBoolean":      poly_bool,
    "ToFloat":        poly_float,
    "ToggleBit":      poly_toggle_bit,
    "ToHex":          poly_hex,
    "ToInteger":      poly_int,
    "ToList":         poly_list,
    "ToNumber":       poly_number,
    "ToOctal":        poly_oct,
    "ToString":       poly_str,
    "TranslateStr":   poly_translate,
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
_FUNC_OPS: dict[str, Callable[..., Any]] = {}

# This index provides a way to find functions independent of case.
# Use get_function_op() to find entries.
_FUNC_INDEX: list[str] = {}

@lru_cache
def get_function_entries() -> dict[str, tuple[Callable[..., Any], str, str]]:
    """
    key: function name
    value: function, name (lc), documentation
    """
    return {
        name: (func, name.lower(), (func.__doc__ or '').lower())
        for name, func in _FUNC_OPS.items()
    }

def function_names_pattern() -> str:
    """
    Return a regex string that will match built-in
    function names.
    """
    functions = sorted(_FUNC_OPS.keys(), key=len, reverse=True)
    return r"(?i)\b(" + "|".join(functions) + r")(?=\s*\()"

def add_builtin_functions() -> None:
    for name, function in _BUILT_IN_FUNCS.items(): add_function('built-in', name, function)

def add_function(extn_name: str, name: str, function: Callable) -> None:
    lc = name.lower()
    if lc in _FUNC_INDEX: raise ValueError(f'Extension {extn_name!r} tried to redefine {name!r}')
    _FUNC_OPS[name] = function
    _FUNC_INDEX[lc] = name

# The max value of an arg range when we have variable arguments
_IS_VARARGS = float('inf')

def get_function(name: str) -> tuple[str, Callable[..., Any]]:
    """Get the entry for the named function: (canonical_name, function)"""
    canonical_name = _FUNC_INDEX.get(name.lower(), None)
    if canonical_name is None: raise ValueError(f'Function {name!r} has no canonical name') # SNO
    return (canonical_name, _FUNC_OPS.get(canonical_name))

def get_function_op(name: str) -> Callable[..., Any]:
    """Given a function name get the function that implements it"""
    function = get_function(name)
    if not function: raise NotImplementedError(f'Function {name!r} not implemented') # SNO
    return function[1]

def get_function_defs(weight: int=99) -> str:
    """Dynamically generate the LARK patterns for functions based on our dictionary"""
    weight = str(weight)
    return (
                '// Functional style\n' +
                _gen_function_defs(weight, 'function', 'FNAME', False) +
                "\n\n" +
                '// Transformational pipeline style\n' +
                _gen_function_defs(weight, 'dotfunction', 'DOT_FNAME', True)
           )

def _gen_function_defs(weight: str, rule_name, group_label, dot_invocation: bool) -> str:
    # Group the functions acording to their argument counts
    # Take into account alias found in _FUNC_INDEX
    func_groups = defaultdict(list)
    for operation in _FUNC_OPS.values():
        arg_range = _get_arg_range(operation, dot_invocation)
        if arg_range is not None:
            func_groups[arg_range].extend(k for k, v in _FUNC_OPS.items() if v is operation)
    fnames = {}
    rc = ''
    # Generate the list of function names per arg count group
    for (min_args, max_args) in sorted(func_groups):
        label = f'{group_label}{min_args}'
        if min_args != max_args:
            label += f'_{"N" if max_args == _IS_VARARGS else max_args}'
        fnames[(min_args, max_args)] = label
        # We emit each by-arg-length group as a regex designed to eliminate
        # "prefix" problems. First we order the names longest to shortest, then end
        # the pattern in such as way that we look ahead for the open paren, but don't capture it.
        rc += '\n' + f'\n{label}.{weight}: /('
        rc += '|'.join(key for key in sorted(func_groups[(min_args, max_args)], key=lambda x: (-len(x), x)))
        rc += ')\\s*(?=[(])/i'
    first = True
    # The function rule is a combination of the by-arg-length names and a pattern for their argument count
    for (min_args, max_args), label in fnames.items():
        if first:
            rc += f'\n{rule_name}.{weight}: '
            first = False
        else:
            rc += '    | '
        rc += label + ' "("'
        arg_count = 0
        # Required arguments patterns
        if min_args > 0:
            rc += ' expr'
            arg_count += 1
            for _ in range(min_args - 1):
                rc += ' _SEP expr'
                arg_count += 1
        # Do we have any optional arguments?
        if arg_count < max_args:
            if min_args == 0:
                rc += ' (expr'
                max_args = max_args if max_args == _IS_VARARGS else (max_args - 1)
            if max_args == _IS_VARARGS:
                rc += ' (_SEP expr)*'
            else:
                while arg_count < max_args:
                    rc += ' (_SEP expr)?'
                    arg_count += 1
            rc += ")?" if min_args == 0 else ''
        rc +=  ' ")"\n'
    return rc.strip()

def _get_arg_range(op, dot_invocation: bool) -> tuple:
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
        elif param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            if param.default == inspect.Parameter.empty:
                req_args += 1
            else:
                opt_args += 1
    if dot_invocation:
        # Because the function is applied to something, we adjust
        if req_args > 0:
            req_args -= 1
        else:
            if opt_args > 0:
                opt_args -= 1
            else:
                # If the function can't be used as a dot function
                # because it has no args, so ignore it
                if not positional: return None
    return (req_args, _IS_VARARGS if positional else (req_args + opt_args))
