"""
Functions is responsible for converting a requested function name to an implementation.
It also generates the grammar fragments used to identify the functions.
"""

from collections import defaultdict
from collections.abc import Sequence, Iterable
from functools import lru_cache
from typing import Any, Callable
import inspect

from .mathpak import (
    base_name,
    bound_ops,
    build_dict,
    build_list,
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
    poly_clone,
    poly_combine_lists,
    poly_combine_using,
    poly_contains_all,
    poly_contains_any,
    poly_count,
    poly_div,
    poly_divmod,
    poly_endswith,
    poly_eq,
    poly_exact_eq,
    poly_expandtabs,
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
    poly_gt,
    poly_getvalues,
    poly_hash,
    poly_hex_decode,
    poly_hex_encode,
    poly_hex,
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
    poly_isfinite,
    poly_isfloat,
    poly_isinf,
    poly_isint,
    poly_islist,
    poly_islower,
    poly_isnan,
    poly_isnumber,
    poly_isnumeric,
    poly_is_pattern,
    poly_isprintable,
    poly_isspace,
    poly_isstr,
    poly_istitle,
    poly_isupper,
    poly_iszero,
    poly_join,
    poly_lookupitem,
    poly_lastitem,
    poly_le,
    poly_leftstr,
    poly_list_append,
    poly_list_create,
    poly_list_insert,
    poly_list_prepend,
    poly_list_remove_first,
    poly_list_remove_last,
    poly_list_remove,
    poly_list_replace,
    poly_list,
    poly_ljust,
    poly_lower,
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
    poly_not_imatches,
    poly_not_in,
    poly_not_matches,
    poly_notempty,
    poly_number,
    poly_oct,
    poly_ord,
    poly_parse_bin,
    poly_parse_hex,
    poly_parse_int,
    poly_parse_oct,
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
    poly_rfindstr,
    poly_rightstr,
    poly_rindex,
    poly_rjust,
    poly_round_multiple,
    poly_round,
    poly_rsplit,
    poly_rstrip,
    poly_setkeyvalue,
    poly_shl,
    poly_shorten,
    poly_shr,
    poly_sign,
    poly_sort,
    poly_split,
    poly_splitlines,
    poly_startswith,
    poly_stdev,
    poly_str,
    poly_strip,
    poly_strlen,
    poly_strrev,
    poly_sub,
    poly_substr,
    poly_succ,
    poly_sum,
    poly_swapcase,
    poly_title,
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
    to_json_string,
    to_json,
)
from .vgr_callable import VgrCallable

def _default_to(value: Any, default: Any) -> Any:
    """
**Returns the default if a value is _None_**

* DefaultTo(_value_, _default_)
* _value_.DefaultTo(_default_)

```vgr
**TODO**
```
"""
    return default if value is None else value

def _is_function(obj: Any) -> Any:
    """
**Returns _True_ if the value is a function**

* IsFunction(_value_)
* _value_.IsFunction()

```vgr
None.IsFunction() → False
Set f(x) -> x+1
f.IsFunction() → True
```
"""
    return isinstance(obj, VgrCallable)

def _id(obj: Any) -> Any:
    """
**Returns the internal, unique ID used by the value**

* Id(_value_)
* _value_.Id()

```vgr
**TODO**
```
"""
    return id(obj)

def _enumerate(obj: Any, start_at: int=0) -> Any:
    """
**Create an enumeration for a collection**

* Enumerate(_value_)
* Enumerate(_value_, _start_at_)
* _value_.Enumerate()
* _value_.Enumerate(_start_at_)

The _start_at_ argument defines the number used in the enumerated value.
The default value for _start_at_ is zero.
Enumeration of values that are not collections produces an enumeration of a single entry.
Enumerating _None_ returns an empty list.

```vgr
None.Enumerate() → []
5.Enumerate() → [[0, 5]]
[5].Enumerate() → [[0, 5]]
[5].Enumerate(-3) → [[-3, 5]]
math.float.Enumerate(1) → [[1, "max", 1.7976931348623157e+308],
    [2, "min", 2.2250738585072014e-308]]
```
"""
    if obj is None: return []
    start_at = int_arg(start_at, "StartAt")
    if isinstance(obj, dict):
        return [[i, k, v] for i, (k, v) in enumerate(obj.items(), start=start_at)]
    if isinstance(obj, list):
        return [[i, x] for i, x in enumerate(obj, start=start_at)]
    return [[start_at, obj]]

def _negate(x: Any) -> Any:
    """
**Returns the negation of a value**

* Negate(_value_)
* _value_.Negate()

The _value_'s type determines what is returned:

* _None_ : always returns _True_
* String : returns _value_ unchanged
* Boolean : returns the logical negation
* Int and Float : return the arithmetic negation
* Lists and Dictionaries : distributed negation

```vgr
**TODO**
```
"""
    if x is None: return True
    if isinstance(x, bool): return not x
    if isinstance(x, (int, float)): return -x
    if isinstance(x, (list, tuple)): return list(_negate(x1) for x1 in x)
    if isinstance(x, dict): return {k: _negate(v) for k, v in x.items()}
    return x

def _slice(x: Any, start: int=None, stop: int=None, step: int=None) -> Any:
    """
**Extract a portion of a list or string**

* _value_.Slice()
* _value_.Slice(_start_)
* _value_.Slice(_start_, _stop_)
* _value_.Slice(_start_, _stop_, _step_)

```vgr
**TODO**
```
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

def _length(x: Any) -> bool:
    """
**Return the length of an an item**

* Length(_value_)
* _value_.Length()

Returns the length of lists and strings.
For dictionaries, the number of attributes is returned.
For all other values _None_ is returned.

```vgr
**TODO**
```
"""
    return len(x) if hasattr(x, '__len__') else None

@bound_ops("||", "Or", "∨")
def logical_or(eval_arg, args: list) -> Any:
    """
**Logical Or operation**

* _x_ || _y_
* _x_ Or _y_
* _x_ ∨ _y_

The values for _x_ and _y_  are evaluated as booleans.

```vgr
**TODO**
```
"""
    # NOTE! args is from the parse tree,
    #       not the evaluated expressions
    for arg in args:
        if eval_arg(arg): return True
    return False

@bound_ops("&&", "And", "∧")
def logical_and(eval_arg, args: list) -> Any:
    """
**Logical And operation**

* _x_ && _y_
* _x_ And _y_
* _x_ ∧ _y_

The values for _x_ and _y_  are evaluated as booleans.

```vgr
**TODO**
```
"""
    # NOTE! args is from the parse tree,
    #       not the evaluated expressions
    for arg in args:
        if not eval_arg(arg): return False
    return True

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
    "Centre":         poly_center,
    "Checksum":       poly_checksum,
    "Chr":            poly_chr,
    "Clamp":          poly_clamp,
    "Clone":          poly_clone,
    "CombineLists":   poly_combine_lists,
    "CombineUsing":   poly_combine_using,
    "CompilePattern": compile_pattern,
    "ContainsAll":    poly_contains_all,
    "ContainsAny":    poly_contains_any,
    "CountOf":        poly_count,
    "DefaultTo":      _default_to,
    "DirectoryName":  dir_name,
    "Div":            poly_div,
    "DivMod":         poly_divmod,
    "EncodeUrl":      encode_url,
    "EndsWith":       poly_endswith,
    "Enumerate":      _enumerate,
    "ExpandTabs":     poly_expandtabs,
    "FileExists":     file_exists,
    "FindStr":        poly_findstr,
    "FirstItem":      poly_firstitem,
    "Floor":          poly_floor,
    "FloorDiv":       poly_fdiv,
    "FloorMultiple":  poly_floor_multiple,
    "Format":         poly_format,
    "FormatDuration": format_duration,
    "FormatJSON":     format_json,
    "FormatTimestamp":format_timestamp,
    "GetKeys":        poly_getkeys,
    "GetKeyValue":    poly_getkeyvalue,
    "GetValues":      poly_getvalues,
    "Hash":           poly_hash,
    "HexDecode":      poly_hex_decode,
    "HexEncode":      poly_hex_encode,
    "Id":             _id,
    "IndexOf":        poly_index,
    "IsAlpha":        poly_isalpha,
    "IsAlphaNumeric": poly_isalnum,
    "IsAscii":        poly_isascii,
    "IsBetween":      poly_between,
    "IsBool":         poly_isbool,
    "IsDecimal":      poly_isdecimal,
    "IsDictionary":   poly_isdict,
    "IsDigit":        poly_isdigit,
    "IsDirectory":    is_dir,
    "IsEmpty":        poly_isempty,
    "IsEqualTo":      poly_eq,
    "IsFalse":        poly_false,
    "IsFile":         is_file,
    "IsFinite":       poly_isfinite,
    "IsFloat":        poly_isfloat,
    "IsFunction":     _is_function,
    "IsGreaterThan":  poly_gt,
    "IsIn":           poly_in,
    "IsInf":          poly_isinf,
    "IsInt":          poly_isint,
    "IsLessThan":     poly_lt,
    "IsList":         poly_islist,
    "IsLower":        poly_islower,
    "IsNan":          poly_isnan,
    "IsNotEmpty":     poly_notempty,
    "IsNotEqualTo":   poly_ne,
    "IsNotGreaterThan": poly_le,
    "IsNotIn":        poly_not_in,
    "IsNotLessThan":  poly_ge,
    "IsNumber":       poly_isnumber,
    "IsNumeric":      poly_isnumeric,
    "IsPattern":      poly_is_pattern,
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
    "Length":         _length,
    "List":           poly_list_create,
    "ListAppend":     poly_list_append,
    "ListInsert":     poly_list_insert,
    "ListPrepend":    poly_list_prepend,
    "ListRemove":     poly_list_remove,
    "ListRemoveFirst":poly_list_remove_first,
    "ListRemoveLast": poly_list_remove_last,
    "ListReplace":    poly_list_replace,
    "LookupItem":     poly_lookupitem,
    "Lower":          poly_lower,
    "Matches":        poly_matches,
    "MatchesAll":     poly_matches_all,
    "MatchesAny":     poly_matches,
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
    "Not":            poly_false,
    "Ord":            poly_ord,
    "ParseBinary":    poly_parse_bin,
    "ParseHex":       poly_parse_hex,
    "ParseInt":       poly_parse_int,
    "ParseJSON":      parse_json,
    "ParseOctal":     poly_parse_oct,
    "ParseUrl":       parse_url,
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
    "ReverseStr":     poly_strrev,
    "RFindStr":       poly_rfindstr,
    "RightJustify":   poly_rjust,
    "RightShift":     poly_shr,
    "RightStr":       poly_rightstr,
    "RightStrip":     poly_rstrip,
    "RIndexOf":       poly_rindex,
    "Round":          poly_round,
    "RoundMultiple":  poly_round_multiple,
    "RSplit":         poly_rsplit,
    "SetKeyValue":    poly_setkeyvalue,
    "ShortenStr":     poly_shorten,
    "Sign":           poly_sign,
    "Slice":          _slice,
    "Sort":           poly_sort,
    "Split":          poly_split,
    "SplitLines":     poly_splitlines,
    "StartsWith":     poly_startswith,
    "Stdev":          poly_stdev,
    "StringLen":      poly_strlen,
    "Strip":          poly_strip,
    "StripNulls":     strip_nulls,
    "StrLen":         poly_strlen, # a 'C'-like name
    "StrRev":         poly_strrev, # a (MS) 'C'-like name
    "Sub":            poly_sub,
    "SubStr":         poly_substr,
    "Succ":           poly_succ,
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

# Needs to include all items bound to operators
_OP_FUNCS: list[Callable[..., Any]] = [
    # TODO why is this turned off?
    #    def unary_not(self, tree): return NotOperation(tree)
    build_dict, # dict
    build_list, # array
    logical_and, # and_op
    logical_or, # or_op
    poly_add, # add_op
    poly_bit_and, # bit_and_op
    poly_bit_or, # bit_or_op
    poly_bit_xor, # bit_xor_op
    poly_ceil, # poly_ceil_op
    poly_contains_all, # contains_all_op
    poly_contains_any, # contains_op
    poly_div, # div_op
    poly_eq, # eq_op
    poly_exact_eq, # exact_eq_op
    poly_floor, # poly_floor_op
    poly_ge, # ge_op
    poly_gt, # gt_op
    poly_imatches, # imatches_op
    poly_in, # in_op
    poly_le, # le_op
    poly_lt, # lt_op
    poly_matches_all, # matches_all_op
    poly_matches, # matches_op
    poly_mod, # mod_op
    poly_mul, # mul_op
    poly_ne, # neq_op
    poly_not_imatches, # not_imatches_op
    poly_not_in, # not_in_op
    poly_not_matches, # not_matches_op
    poly_pow, # pow_op
    poly_shl, # shl_op
    poly_shr, # shr_op
    poly_sub, # sub_op
    # def c_ternary(self, tree): return Ternary(tree, (0, 1, 2))
    # def py_ternary(self, tree): return Ternary(tree, (1, 0, 2))
    # def set_var(self, tree): return SetVarOperation(tree)
]

def function_names_pattern() -> str:
    """
    Return a regex string that will match built-in
    function names.
    """
    functions = sorted(_FUNC_OPS.keys(), key=len, reverse=True)
    return r"(?i)\b(" + "|".join(functions) + r")(?=\s*\()"

@lru_cache
def get_operator_entries():
    entries = {}
    for func in _OP_FUNCS:
        # See mathpak/common for the bound_ops decorator
        if hasattr(func, 'bound_ops'):
            for op in func.bound_ops:
                entries[op] = (func, op.lower().replace(' ', ''), (func.__doc__ or '').lower())
    return entries

def add_builtin_functions() -> None:
    for name, function in _BUILT_IN_FUNCS.items(): add_function('built-in', name, function)

def add_function(extn_name: str, name: str, function: Callable) -> None:
    lc = name.lower()
    if lc in _FUNC_INDEX:
        raise ValueError(f'Extension {extn_name!r} tried to redefine {name!r}')
    _FUNC_OPS[name] = function
    _FUNC_INDEX[lc] = name

# The max value of an arg range when we have variable arguments
_IS_VARARGS = float('inf')

def get_function(name: str) -> tuple[str, Callable[..., Any]]:
    """Get the entry for the named function: (canonical_name, function)"""
    canonical_name = _FUNC_INDEX.get(name.lower(), None)
    if canonical_name is None: return None
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
                '// function-style invocation\n' +
                _gen_function_defs(weight, 'function', 'FNAME', False) +
                "\n\n" +
                '// method-style invocation\n' +
                _gen_function_defs(weight, 'dotfunction', 'DFNAME', True)
           )

def _gen_function_defs(weight: str, rule_name, group_label, dot_invocation: bool=False) -> str:
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
        req_args -= 1
        # If the function can't be used in this manner, ignore it
        if req_args < 0: return None
    return (req_args, _IS_VARARGS if positional else (req_args + opt_args))
