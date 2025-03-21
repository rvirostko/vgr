#! /usr/bin/env python3

from collections import defaultdict
from typing import Any
import argparse
import ast
import csv
import fnmatch
import glob
import inspect
import json
import math
import os
import re
import sys
import zipfile

from lark import Lark, Tree, Token, Transformer, Visitor, v_args, exceptions

from mathpak import *
from output import prepare_path, verify_relative_path, IORedirector

from data_dict import DataDictionary
from interactive import CmdLine

# Binds a (pretty) name to the function to be executed
# Additionally, we should use functions here rather than lambdas
# so we can grab the __DOC__ for help functions.
_FUNC_OPS = {
  "Abs": poly_abs,
  "Add": poly_vadd,
  "Append": poly_vappend,
  #"Attr": ???,                       # TODO see attrgetter, better name?
  "BitAnd": poly_vbit_and,
  "BitNot": poly_bit_not,
  "BitOr": poly_vbit_or,
  "BitXor": poly_vbit_xor,
  "Bool": poly_bool,
  "Capitalize": poly_capitalize,
  "CaseFold": poly_casefold,
  "Ceil": poly_ceil,
  "Class": poly_class,
  "Contains": poly_contains,
  "CountOf": poly_count,
  "Div": poly_vdiv,
  "EndsWith": poly_endswith,
  "ExpandTabs": poly_expandtabs,
  "FirstItem": poly_firstitem,
  "Float": poly_float,
  "Floor": poly_floor,
  "FloorDiv": poly_vfdiv,
  "GE": poly_ge,
  "Hash": poly_hash,
  "IMatch": poly_imatch,
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
  "LE": poly_le,
  "LeftShift": poly_shl,
  "LeftStr": poly_leftstr,
  "LeftStrip": poly_lstrip,
  "Len": poly_len,
  "Lookup": poly_lookup,
  "Lower": poly_lower,
  "Match": poly_match,
  "Mod": poly_mod,
  "Mul": poly_vmul,
  "Number": poly_number,
  "Pow": poly_exp,
  "Prepend": poly_vprepend,
  "RemovePrefix": poly_removeprefix,
  "RemoveSuffix": poly_removesuffix,
  "ReplaceStr": poly_replace,
  "Repr": poly_repr,
  "RightShift": poly_shr,
  "RightStr": poly_rightstr,
  "RightStrip": poly_rstrip,
  "RIndexOf": poly_rindex,
  "Round": poly_round,
  "RSort": poly_rsort,
  "SizeOf": poly_sizeof,
  "Sort": poly_sort,
  "StartsWith": poly_startswith,
  "Str": poly_str,
  "Strip": poly_strip,
  "Sub": poly_vsub,
  "SubStr": poly_substr,
  "SwapCase": poly_swapcase,
  "TitleCase": poly_title,
  "Translate": poly_translate,
  "TrueDiv": poly_div,
  "Trunc": poly_trunc,
  "Type": poly_type,
  "Unique": poly_unique,
  "Upper": poly_upper,
}

"""This index provides a way to find functions independent of case.
Use get_function_op() to find entries"""
_FUNC_INDEX = {k.lower(): k for k in _FUNC_OPS}

# List of tokens that we don't try to translate in exceptions
_TOKEN_PASS = ('NAME',)

def get_function_op(name: str):
    """Given a function name get the function that implements it"""
    rc = _FUNC_OPS.get(_FUNC_INDEX.get(name.lower()), None)
    if not rc: raise NotImplementedError(f'Function {name} not yet implemented')
    return rc

# The max value of an arg range when we have variable arguments
_IS_VARARGS = float('inf')

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

def get_function_defs(w: int=99) -> str:
    """Dynamically generate the LARK patterns for functions based on our dictionary"""
    w = str(w)
    # Group the functions acording to their argument counts
    func_groups = defaultdict(list)
    for name, op in _FUNC_OPS.items(): func_groups[get_arg_range(op)].append(name)
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

_VALID_TARGETS = ['ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role']

class ImplicitContextAdder(Transformer):
    """
    Modifies 'var_ref' nodes by prepending TARGET if needed
    Assuming target is "kv":
        * kv -> kv (no change, type is a target type)
        * name -> kv.name (not a target type)
    """
    def __init__(self):
        super().__init__()
        self._target = None
        self._valid_contexts = None

    def add_contexts(self, tree, target: str, valid_contexts):
        try:
            self._target = target
            self._valid_contexts = valid_contexts
            return super().transform(tree)
        finally:
            self._target = None
            self._valid_contexts = None

    def var_ref(self, children):
        first_child = children[0]
        if first_child.value not in self._valid_contexts:
            # Add the target as an implied context for the name
            children.insert(0, Token("NAME", self._target))
            # TODO , first_child.start_pos, first_child.line, first_child.column,
            # first_child.end_line, first_child.end_column, first_child.end_pos))
        return Tree("var_ref", children)

# pylint: disable=invalid-name
# disabled because we MUST have methods named the same as the tokens
# and the tokens MUST have uppercase names
class ConstantsNormalizer(Transformer):
    def ESCAPED_STRING(self, token):
        # Removes the quoting and interprets escape sequences
        # TODO: needs lots of test cases as this reportedly has problems
        return self._new_token(token, "STRING", ast.literal_eval(token.value))
    def TRUE(self, token): return self._new_token(token, token.type, True)
    def FALSE(self, token): return self._new_token(token, token.type, False)
    def NONE(self, token): return self._new_token(token, 'NONE', None)
    def INF(self, token): return self._new_token(token, 'FLOAT', math.inf)
    def NAN(self, token): return self._new_token(token, 'FLOAT', math.nan)
    def DEC_NUMBER(self, token): return self._to_int(token, 10)
    def HEX_NUMBER(self, token): return self._to_int(token, 16)
    def OCT_NUMBER(self, token): return self._to_int(token, 8)
    def BIN_NUMBER(self, token): return self._to_int(token, 2)
    def FLOAT_NUMBER(self, token): return self._new_token(token, 'FLOAT', float(token.value))
    def _to_int(self, token, base: int): return self._new_token(token, 'INT', int(token.value, base))
    def _new_token(self, token, new_type: str, value: Any):
        return Token(new_type, value, token.start_pos, token.line, token.column,
                     token.end_line, token.end_column, token.end_pos)
    # TODO arrays?
# pylint: enable=invalid-name

class Operation(Tree):
    def __init__(self, base: Tree, op):
        super().__init__(base.data, base.children or [])
        self._op = op
    def execute(self, args: tuple) -> Any: return self._op(*args)
    def op_name(self) -> str: return self._op.__name__ if self._op else 'None'

def build_array(*values: Any) -> list[Any]:
    """We build an array from the collected values"""
    return None if values is None else list(values)

def var_ref(*path: str)-> Any:
    """This is the lookup of a top-level variable"""
    return _DD.get_var_user(*path)

def deref_var(data: Any, *path: str) -> Any:
    """This is the lookup of a path relative to data"""
    return _DD.get_var_user_relative(data, *path)

@v_args(tree=True)
class OperationBinder(Transformer):
    """Binds functions to expression operations"""
    def add_op(self, tree): return Operation(tree, poly_add)
    def array(self, tree): return Operation(tree, build_array)
    def bit_and_op(self, tree): return Operation(tree, poly_bit_and)
    def bit_or_op(self, tree): return Operation(tree, poly_bit_or)
    def bit_xor_op(self, tree): return Operation(tree, poly_bit_xor)
    def contains_op(self, tree): return Operation(tree, poly_contains)
    def deref(self, tree): return Operation(tree, deref_var)
    def div_op(self, tree): return Operation(tree, poly_div)
    def eq_op(self, tree): return Operation(tree, poly_eq)
    def exp_op(self, tree): return Operation(tree, poly_exp)
    def fdiv_op(self, tree): return Operation(tree, poly_fdiv)
    def function(self, tree): return Operation(tree, get_function_op(tree.children.pop(0).value))
    def ge_op(self, tree): return Operation(tree, poly_ge)
    def gt_op(self, tree): return Operation(tree, poly_gt)
    def imatch_op(self, tree): return Operation(tree, poly_imatch)
    def in_op(self, tree): return Operation(tree, poly_in)
    def le_op(self, tree): return Operation(tree, poly_le)
    def lt_op(self, tree): return Operation(tree, poly_lt)
    def match_op(self, tree): return Operation(tree, poly_match)
    def mod_op(self, tree): return Operation(tree, poly_mod)
    def mul_op(self, tree): return Operation(tree, poly_mul)
    def neq_op(self, tree): return Operation(tree, poly_ne)
    def not_contains_op(self, tree): return Operation(tree, poly_not_contains)
    def not_imatch_op(self, tree): return Operation(tree, poly_not_imatch)
    def not_in_op(self, tree): return Operation(tree, poly_not_in)
    def not_match_op(self, tree): return Operation(tree, poly_not_match)
    def or_op(self, tree): return Operation(tree, poly_or)
    def shl_op(self, tree): return Operation(tree, poly_shl)
    def shr_op(self, tree): return Operation(tree, poly_shr)
    def sub_op(self, tree): return Operation(tree, poly_sub)
    def unary_not(self, tree): return Operation(tree, poly_not)
    def var_ref(self, tree): return Operation(tree, var_ref)
    def function_call(self, tree):
        # The expression becomes the first argument to the function,
        # and it takes the place of the wrapper from parsing
        expr, func = tree.children
        func.children.insert(0, expr)
        return func

class TreeSplitter(Visitor):
    def __init__(self):
        super().__init__()
        self._target = None
        self._predicates = None
        self._outputs = None
        self._labels = None
        self._limit = None
        self._offset = None

    def split(self, tree: Tree):
        self.visit(tree)
        return self

    def get_target(self) -> str:
        return self._target

    def get_outputs(self) -> list:
        return self._outputs if self._outputs else []

    def get_label(self, output) -> str:
        # if it is an output_as, it will have two children
        # the second child will be either a NAME or a STRING, but all we need
        # is its value regardless of type
        return output.children[1].value if len(output.children) > 1 else None

    def get_predicates(self) -> list:
        return self._predicates if self._predicates else []

    def get_limit(self) -> int:
        return self._limit

    def get_offset(self) -> int:
        return self._offset

    def outputs(self, node):
        self._outputs = []
        self._labels = None
        self._outputs.extend(node.children)

    def output(self, node):
        # When there is a single output, there is no outputs rule...
        if self._outputs is None:
            self._outputs = []
            self._labels = None
            self._outputs.append(node)

    def output_as(self, node):
        self.output(node)

    def select(self, node):
        for child in node.children:
            if isinstance(child, Token) and child.type == 'TARGET':
                self._target = child.value
                break

    def where_clause(self, node):
        self._predicates = []
        self._predicates.extend(node.children)

    def limit_clause(self, node):
        children = node.children
        if len(children) >= 1: self._limit = poly_int(poly_firstitem(eval_expr(children[0])))
        if len(children) >= 2: self._offset = poly_int(poly_firstitem(eval_expr(children[1])))

class StatementSourceMgr:
    def __init__(self, statement_text, origin: str=''):
        self._statement_text: str = statement_text or ''
        self._origin: str = origin

    def source_for(self, tree: Tree) -> str:
        if not self._statement_text or tree is None: return ''
        start, end = self._subtree_span(tree)
        return self._statement_text[start:end]

    def origin(self) -> str:
        return self._origin

    def _subtree_span(self, node):
        """
        Recursively finds the start and end positions of a subtree in the source text.

        Returns:
            (start_pos, end_pos) where:
            - start_pos is the earliest character index of any token in the subtree.
            - end_pos is the last character index + 1 of any token in the subtree.
            If no tokens are found, returns (None, None).
        """
        start_pos = None
        end_pos = None

        def traverse(n):
            nonlocal start_pos, end_pos
            if isinstance(n, Token):
                if n.start_pos is not None:
                    if start_pos is None or n.start_pos < start_pos:
                        start_pos = n.start_pos
                    if end_pos is None or (n.end_pos is not None and n.end_pos > end_pos):
                        end_pos = n.end_pos
            elif isinstance(n, Tree):
                for child in n.children: traverse(child)
                # Some Tree nodes have meta positions, but we can't fully trust it.
                if hasattr(n, "meta") and n.meta:
                    if hasattr(n.meta, "start_pos") and n.meta.start_pos is not None:
                        if start_pos is None or n.meta.start_pos < start_pos:
                            start_pos = n.meta.start_pos
                    if hasattr(n.meta, "end_pos") and n.meta.end_pos is not None:
                        if end_pos is None or n.meta.end_pos > end_pos:
                            end_pos = n.meta.end_pos
        traverse(node)
        return start_pos, end_pos

def _flag_value(statement: Tree) -> bool:
    # default for a flag is a request to turn on
    if not statement.children: return True
    return poly_bool(poly_firstitem(eval_expr(statement.children[0])))

def execute_echo(statement: Tree) -> None:
    """Turn echo mode on or off

* ECHO [;]
* ECHO _expression_ [;]

When on, statements are echoed before execution
"""
    _DD.set_echo(_flag_value(statement))
    print_verbose('Echo =', _DD.is_echo())

def execute_debug(statement: Tree) -> None:
    """Turn debug mode on or off

* DEBUG [;]
* DEBUG _expression_ [;]

When on, additional technical output is generated.
"""
    _DD.set_debug(_flag_value(statement))
    print_verbose('Debug =', _DD.is_debug())

def execute_verbose(statement: Tree) -> None:
    """Turn verbose mode on or off

* VERBOSE [;]
* VERBOSE _expression_ [;]

When on, additional operational output is generated.
"""
    _DD.set_verbose(_flag_value(statement))
    print_verbose('Verbose =', _DD.is_verbose()) # Yeah... can only print true

def execute_exit(statement: Tree) -> None:
    """Terminate execution

* EXIT [;]
* EXIT _expression_ [;]

The _expression_ is a numeric the code returned to the shell.
The default return code is zero.
Note that "True" returns one and "False" returns zero.
"""
    rc: int = None
    if statement.children:
        x: Any = poly_firstitem(eval_expr(statement.children[0]))
        try:
            rc = poly_int(x)
        except ValueError:
            rc = int(poly_bool(x))
    print_verbose('Exit Code =', rc)
    sys.exit(rc)

def execute_assert(statement: Tree) -> None:
    """Assert that a condition is met, terminating execution if it is not

* ASSERT _expression_ [;]
* ASSERT _expression_ : _expression_ [, _expression]... [;]

The first expression is evaluated as a boolean value which must be true for execution to continue.

The optional expressions following the colon compose a a string message printed if the first expression
is not true. It is composed in the same manner as Printf, with the first one being a string containing
formatting syntax as used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

If no message is given the the failing expression is used as the message

Execution ends with an exit code of 1 indicating failure
"""
    exprs = [*statement.children]
    v: bool = poly_bool(eval_expr(exprs.pop(0))) if len(exprs) else False
    if not v:
        msg: str = None
        if len(exprs) > 0:
            try:
                msg = poly_str(eval_expr(exprs.pop(0)))
                if msg is not None: msg = msg.format(*[eval_expr(expr) for expr in exprs])
            except Exception as e:
                print_stderr(f'While evaluating {SOURCE_MGR.source_for(statement)} on line {statement.meta.line}: ', e)
                msg = None
        print_stderr(f'Line {statement.meta.line}:',
                     (str(msg) if msg is not None else f'{SOURCE_MGR.source_for(statement)} failed'))
        sys.exit(1)

def execute_set(statement: Tree) -> None:
    """Assign a value to a variable.

* SET _variable_ [= | := | TO) _expression_ [;]
* LET _variable_ [= | :=] _expression_ [;]
"""
    var_name, expr = statement.children
    _DD.set_var_user(eval_expr(expr), *(name.value for name in var_name.children))

def execute_load_from(statement: Tree) -> None:
    """Assign a value to a variable from a file.

* LOAD _variable_ FROM [FILE] _expression_ [;]
* LOAD _variable_ FROM [FILE] _expression_ JSON [OBJECT] [;]
* LOAD _variable_ FROM [FILE] _expression_ JSON [OBJECT] PER LINE [;]
* LOAD _variable_ FROM [FILE] _expression_ CSV [;]
* LOAD _variable_ FROM [FILE] _expression_ TEXT [;]

The _expression_ is resolved to string as file to be loaded

If no type is included, the type is inferred from the extension of the file
name with TEXT as the default.
"""
    var_name = statement.children[0]
    filename = eval_filename_expr(statement.children[1])
    mode = None
    if len(statement.children) > 2:
        mode = statement.children[2].data
    else:
        ext = os.path.splitext(filename)[1].lower()
        mode = 'csv_file' if ext == '.csv' else 'json_object' if ext == '.json' else 'text_file'
    with open(filename, 'r', encoding='utf-8') as f:
        data: Any = None
        if mode == 'text_file': data = f.read()
        elif mode == 'json_object': data = json.load(f)
        elif mode == 'json_objects': data = [json.loads(line) for line in f if line.strip()]
        elif mode == 'csv_file': data = list(csv.DictReader(f))
        else: raise ValueError(f'Unknown mode {mode}') # SNO
        _DD.set_var_user(data, *(name.value for name in var_name.children))

def execute_print(statement: Tree) -> None:
    """Print values, similar to AWK's print statement

* PRINT [;]
* PRINT _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below)

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
"""
    print_stdout(*[eval_expr(expr) for expr in statement.children],
                    sep=str(_DD.get_var_user(*_OFS_PATH) or ' '),
                    end=str(_DD.get_var_user(*_ORS_PATH) or '\n'))

def execute_printf(statement: Tree) -> None:
    """Print formatted values, similar to AWK's printf statement

* PRINTF [;]
* PRINTF _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed

The first expression is resolved to a string used to format the other values

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)
"""
    exprs = [*statement.children]
    format_string = poly_str(eval_expr(exprs.pop(0))) if len(exprs) else ''
    print_stdout(str(format_string).format(*[eval_expr(expr) for expr in exprs]), end='')

def execute_exhibit(statement: Tree) -> None:
    """The display the name and values of variables

* EXHIBIT [;]
* EXHIBIT _variable_ [, _variable_]... [;]

The values are displayed on individual lines. If a variable has sub variables, each
portion is displayed on its own line.

Without arguments, all variables are displayed

Unlike PRINT and PRINTF, the values display are the _representation_ of the data, not
its printable value. This lets you diferentiate between an integer and a string, and
see control characters.
"""
    def exhibit_value(name: str, value: Any) -> None:
        if isinstance(value, dict):
            for key in sorted(value.keys()): exhibit_value(f'{name}.{key}', value[key])
        else:
            print_stdout(f'{name} = {repr(value)}')
    children = statement.children
    if children:
        for var_name in children:
            path = tuple(name.value for name in var_name.children)
            exhibit_value('.'.join(path), _DD.get_var_user(*path))
    else:
        for key in sorted(_DD.keys()): exhibit_value(key, _DD.get_var(key))

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stderr(), **kwargs)

def print_debug(*args, **kwargs) -> None:
    if _DD.is_debug(): print_stderr(*args, **kwargs)

def print_verbose(*args, **kwargs) -> None:
    if _DD.is_verbose(): print_stderr(*args, **kwargs)

def print_exception(statement: Tree, e: Exception) -> None:
    print_stderr(f'Line {statement.meta.line}: {SOURCE_MGR.source_for(statement)}')
    print_stderr(exception_type(e), ': ', str(e))

def execute_open(statement: Tree) -> None:
    """Send command output or error output to a file

* OPEN [OUTPUT | ERROR] [FILE] _expression_ [OVERWRITE] [;]
* OPEN [OUTPUT | ERROR] [FILE] _expression_ NO OVERWRITE [;]
* OPEN [OUTPUT | ERROR] [FILE] _expression_ [EXTEND | APPEND] [;]

The _expression_ is resolved to string as file to be opened

If output is being sent to another file, it is closed first.

When EXTEND or APPEND is used, output is added to the end of an existing file.
When NO OVERWRITE is used, the command will fail if the file already exists.
Otherwise, if OVERWRITE is used of no mode is given and the file already exists, its contents are truncated.

All redirection is closed at program termination.

See CLOSE
"""
    stream = eval_stream_name(statement.children[0])
    filename = eval_filename_expr(statement.children[1])
    mode = 'w'
    if len(statement.children) > 2: mode = statement.children[2].data.lower()
    if mode not in ('a', 'w', 'x'): raise ValueError(f'Unknown mode {mode}') # SNO
    try:
        getattr(_REDIR, stream)(prepare_path(filename), mode=mode)
        print_verbose(stream, "redirected to", filename)
    except Exception as e:
        print_exception(statement, e)
        sys.exit(1)

def eval_stream_name(node: Tree) -> str:
    stream = node.data.lower()
    if stream not in ('stderr', 'stdout'): raise ValueError(f'Unknown stream {stream}') # SNO
    return stream

def eval_to_list_str(clause: Tree, name: str) -> str:
    return [eval_to_str(expr, name) for expr in clause.children]

def eval_to_str(expr: Tree, name: str) -> str:
    rc = eval_expr(expr)
    if not isinstance(rc, str): raise TypeError(f'{name} must be a string; found {type(rc).__name__}')
    return rc

def eval_filename_expr(expr: Tree) -> str:
    return verify_relative_path(eval_to_str(expr, 'File name'))

def execute_close(statement: Tree) -> None:
    """Close the output or error file

* CLOSE OUTPUT [FILE] [;]
* CLOSE ERROR [FILE] [;]

Once closed, command output and errors resumes their default destinations.

All redirection is closed at program termination.
"""
    stream = eval_stream_name(statement.children[0])
    getattr(_REDIR, stream)(None)
    print_verbose(stream, "closed")

def eval_expr(expr: Any) -> Any:
    if isinstance(expr, Tree):
        if isinstance(expr, Operation): return expr.execute(tuple(eval_expr(arg_exp) for arg_exp in expr.children))
        raise NotImplementedError(f'Unhandled type {expr.data}')
    if isinstance(expr, Token): return expr.value
    raise NotImplementedError(f'Unknown type {expr.type()}')

def execute_zip(statement: Tree):
    """Create a ZIP Archive

* CREATE ZIP [FILE] _expression_ [_option_ [, _option_]...]

Options are

* INCLUDE _expression_...
* EXCLUDE _expression_...
* COMMENT _expression_
* PASSWORD _expression_

Include and exclude expressions are strings that include files or
directories. Directories are included recursively. Files and directories must
be relative to the current directory.

_Password is not currently implemented but may be specified_

"""
    zip_name = eval_filename_expr(statement.children.pop(0))
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    comment: str = None
    password: str = None
    for child in statement.children:
        arg_type = child.data
        if arg_type == 'include': include_patterns.extend(eval_to_list_str(child, 'Include'))
        elif arg_type == 'exclude': exclude_patterns.extend(eval_to_list_str(child, 'Exclude'))
        elif arg_type == 'comment': comment = eval_to_str(child.children[0], 'Comment')
        elif arg_type == 'password': password = eval_to_str(child.children[0], 'Password')
        else: raise ValueError(f'Unhandled type {repr(arg_type)}')
    added_files = set()
    # General follow zip's -r behavior when it comes to subdirs
    for pattern in include_patterns:
        for match in glob.glob(pattern, recursive=True):
            abs_match = verify_relative_path(os.path.abspath(match))
            if os.path.isfile(abs_match):
                added_files.add(abs_match)
            elif os.path.isdir(abs_match):
                # Mimic `zip -r`, adding all files under the directory
                for root, _, files in os.walk(abs_match):
                    for file in files: added_files.add(os.path.abspath(os.path.join(root, file)))
    # Use the excluded patterns to filter what was included
    added_files = {
        f for f in added_files if not any(fnmatch.fnmatch(f, pattern) for pattern in exclude_patterns)
    }
    print_verbose('Creating', zip_name)
    with zipfile.ZipFile(prepare_path(zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
        # TODO this is only used for reading, so we need to switch libraries
        if password: zf.setpassword(password.encode())
        if comment: zf.comment = comment.encode('utf-8')
        if added_files:
            for file in sorted(added_files):
                relpath = os.path.relpath(file)
                print_verbose('Adding', relpath)
                zf.write(file, relpath)
        else:
            print_verbose('Created an empty archive')

def execute_select(statement: Tree):
    ts = TreeSplitter().split(statement)
    # If the user has defined something, or it is one of the pre-loaded
    # prefixes or the target types, then it is a known context and
    # not subject to getting the target prefix added to it
    statement = ImplicitContextAdder().add_contexts(statement, ts.get_target(), _VALID_TARGETS + _DD.keys())
    ts.split(statement)
    print(f'Target     : {ts.get_target()}')
    print(f'Predicates : {len(ts.get_predicates())}')
    for i, p in enumerate(ts.get_predicates()): print(f'\t{i + 1} : {SOURCE_MGR.source_for(p)}')
    print(f'Outputs    : {len(ts.get_outputs())}')
    for i, o in enumerate(ts.get_outputs()):
        text = SOURCE_MGR.source_for(o)
        label = ts.get_label(o)
        label = '_'.join(text.strip().split()) if label is None else label
        print(f'\t{i + 1} : {text} "{label}"')
    print(f'Limit      : {ts.get_limit()}')
    print(f'Offset     : {ts.get_offset()}')

STATEMENT_HANDLERS = {
    'assert': execute_assert,
    'close': execute_close,
    'debug': execute_debug,
    'echo': execute_echo,
    'exhibit': execute_exhibit,
    'exit': execute_exit,
    'load_from': execute_load_from,
    'open': execute_open,
    'print': execute_print,
    'printf': execute_printf,
    'select': execute_select,
    'set': execute_set,
    'verbose': execute_verbose,
    'zip': execute_zip,
}

def remove_comments(input_text: str) -> str:
    """Removes comments but preserves lines for Lark metadata accuracy."""
    # We do Hash, C-style, and SQL style
    return re.sub(r'(^|;)[ \t]*(#|//|--).*', r'\1\n', input_text)

def execute_statements(statement_text: str, source: str=None) -> None:
    statement_text = remove_comments(statement_text)
    if not statement_text or statement_text.isspace(): return
    statements: Tree = _PARSER.parse(statement_text)
    global SOURCE_MGR
    SOURCE_MGR = StatementSourceMgr(statement_text, source)
    for statement in statements.children:
        handler = STATEMENT_HANDLERS.get(statement.data)
        if not handler: raise NotImplementedError(f'No handler established for {statement.data}')
        statement = ConstantsNormalizer().transform(statement)
        statement = OperationBinder().transform(statement)
        text = statement_text[statement.meta.start_pos : statement.meta.end_pos]
        _DD.set_var(None,text, *_STATEMENT_PATH)
        if _DD.is_echo(): print_stdout(text)
        if _DD.is_debug(): print_tree(statement)
        handler(statement)

def print_tree(item: Any, indent=2) -> None:
    prefix = ' ' * indent  # Indentation for nested levels
    if isinstance(item, Tree):
        tree: Tree = item
        op = f':{tree.op_name()}' if isinstance(item, Operation) else ''
        print_stderr(f'{prefix}({tree.data}{op}', end=('\n' if tree.children else ''))
        for child in tree.children: print_tree(child, indent + 2)
        print_stderr(f'{prefix if tree.children else ""})')  # close the rule
    else:
        if isinstance(item, Token):
            token: Token = item
            print_stderr(f'{prefix}{token.type}: {token.value} (Pos: {token.line}:{token.column} {type(token.value)})')
        else:
            raise ValueError(item.type()) # What else can there be?

def token_value(token_name) -> str:
    """Lark tokens to their values for error display"""
    if token_name not in _TOKEN_PASS:
        for terminal in _PARSER.parser.lexer_conf.terminals:
            # Get the regex pattern or literal value
            if terminal.name == token_name: return repr(terminal.pattern.value)
    # Fallback to token name if no mapping is found
    return token_name

def get_expected(e: Exception) -> str:
    rc = ''

    if hasattr(e, 'token') and e.token:
        rc += token_value(e.token) + 'unexpected.'

    if hasattr(e, 'expected') and e.expected:
        expected = [tok for tok in e.expected]
        if expected:
            rc = '\nExpected '
            values = [token_value(tok) for tok in sorted(expected)]
            if len(values) == 1: rc += values[0]
            elif len(values) == 2: rc += values[0] + ' or ' + values[1]
            else: rc += ', '.join(values[:-1]) + ', or ' + values[-1]
            rc += '.'
    return rc

_ERROR_XLATE = {
    exceptions.UnexpectedInput: "Syntax error",
    exceptions.UnexpectedToken: "Unexpected input",
    exceptions.UnexpectedEOF: "Unexpected End-of-File",
    exceptions.UnexpectedCharacters: "Unexpected character",
    exceptions.ParseError: "Error",
    ValueError: "Error"
}

def exception_type(e: Exception) -> str:
    """
    Convert the exception type into a human-readable string based on a dictionary.
    If no custom message is found, fallback to the default class name.
    """
    etype = type(e)
    return _ERROR_XLATE.get(etype, etype.__name__)

class VGRCmdLine(CmdLine):
    _VGR_ENV_PREFIX = 'VGR_'
    _VGR_PREFIX = '_vgr'
    _PROMPT_PATH = (_VGR_PREFIX, 'prompt')
    _HISTORY_PATH = (_VGR_PREFIX, 'history')
    _HISTORY_SIZE_PATH = (_VGR_PREFIX, 'history_size')
    _DEFAULT_HISTORY_SIZE = 100
    _DEFAULT_HISTORY = '~/.vgr_history'
    _DEFAULT_PROMPT = 'vgr> '

    def __init__(self, dd: DataDictionary):
        self._dd = dd
        self.prompt = self._get_vgr_default(self._PROMPT_PATH[1], self._DEFAULT_PROMPT)
        self.history_filename = self._get_vgr_default(self._HISTORY_PATH[1], self._DEFAULT_HISTORY)
        self.max_history_entries = self._get_vgr_default_int(self._HISTORY_SIZE_PATH[1], self._DEFAULT_HISTORY_SIZE)
        super().__init__()

    def execute_statements(self, text: str) -> None:
        try:
            execute_statements(text)
        except exceptions.UnexpectedInput as e:  # Covers most parsing errors
            print(f'{e.get_context(text)}{exception_type(e)} at line {e.line}, column {e.column}.{get_expected(e)}')
        except Exception as e:
            print(exception_type(e), ': ', str(e))

    @property
    def debug(self) -> bool: return self._dd.is_debug()

    @property
    def verbose(self) -> bool: return self._dd.is_verbose()

    @verbose.setter
    def verbose(self, value: bool): self._dd.set_verbose(value)

    @property
    def prompt(self) -> str:
        return str(self._dd.get_var(None, *self._PROMPT_PATH) or self._DEFAULT_PROMPT)

    @prompt.setter
    def prompt(self, value: str):
        self._dd.set_var(None, value or self._DEFAULT_PROMPT, *self._PROMPT_PATH)

    @property
    def history_filename(self) -> str:
        return self._expand_fn(str(self._dd.get_var(None, *self._HISTORY_PATH) or self._DEFAULT_HISTORY))

    @history_filename.setter
    def history_filename(self, value: str) -> None:
        self._dd.set_var(None, self._expand_fn(value or self._DEFAULT_HISTORY), *self._HISTORY_PATH)

    @property
    def max_history_entries(self) -> int:
        try:
            return int(self._dd.get_var(None, *self._HISTORY_SIZE_PATH) or self._DEFAULT_HISTORY_SIZE)
        except ValueError:
            return self._DEFAULT_HISTORY_SIZE

    @max_history_entries.setter
    def max_history_entries(self, value: int) -> None:
        self._dd.set_var(None, value or self._DEFAULT_HISTORY_SIZE, *self._HISTORY_SIZE_PATH)

    def _get_vgr_default(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and return it or the default value"""
        return os.getenv(self._VGR_ENV_PREFIX + env_var.upper(), default)

    def _get_vgr_default_int(self, env_var: str, default: Any) -> str:
        """Look for a matching environment variable (uppercase) and try to convert to an int"""
        try:
            return int(self._get_vgr_default(env_var, default))
        except ValueError:
            return default

    def _expand_fn(self, fn: str) -> str:
        return os.path.abspath(os.path.expanduser(fn))

def execute_interactive() -> None:
    print("Type 'exit' to exit")
    try:
        VGRCmdLine(_DD).run()
    finally:
        _REDIR.end_redirects()

_DD: DataDictionary = None
_PARSER: Lark = None
_REDIR: IORedirector = None
# Initialize with no text
SOURCE_MGR: StatementSourceMgr = StatementSourceMgr('')
_VGR_PREFIX = '_vgr'
_GRAMMAR_PATH = (_VGR_PREFIX, 'grammar')
_STATEMENT_PATH = (_VGR_PREFIX, 'statement')
_ARG_PREFIX = 'arg'
_OFS_PATH = (_ARG_PREFIX, 'ofs')
_ORS_PATH = (_ARG_PREFIX, 'ors')

def main():
    global _DD, _REDIR, _PARSER
    parser = argparse.ArgumentParser(
        description="Generic Reporting for Hashicorp Vault - prototype"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--execute', type=str, metavar='STATEMENTS', help='Execute the given statements')
    group.add_argument('-f', '--file', action='append', metavar='FILE', help='Execute statements stored in a file')
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    parser.add_argument('--echo', action='store_true', help="Enable statement echo")
    parser.add_argument('--grammar',  metavar="FILE", type=str, default='vgr.ebnf', help='Grammar definition')
    parser.add_argument('user_args', nargs='*', metavar='NAME=VALUE', help='Additional arguments')
    parsed = parser.parse_args()

    _DD = DataDictionary()
    _DD.add_protected_prefix(_ARG_PREFIX)
    _DD.add_immutable_prefix(_VGR_PREFIX)
    _DD.set_debug(parsed.debug)
    _DD.set_verbose(parsed.verbose)
    _DD.set_echo(parsed.echo)
    # Pick up the defaults AWK would use
    # Since we don't allow the env space to be changed,
    # we have to keep our own copies for the user to change with
    # either Set or with command line arguments
    _DD.set_var(None, os.getenv('OFS', ' '), *_OFS_PATH)
    _DD.set_var(None, os.getenv('ORS', '\n'), *_ORS_PATH)

    # NB: User args can override debug/echo/verbose...
    for arg in parsed.user_args:
        if '=' in arg:
            name, value = re.split(r'\s*=', arg, 1)
            path = tuple(step for step in re.split(r'\s*[.]\s*', name.strip()))
            if path:
                # Strip off the quotes
                match = re.fullmatch(r'\s*"([^"]*)"\s*', value)
                path = (_ARG_PREFIX,) + path
                _DD.set_var(None, match.group(1) if match else coerce_value(value), *path)

    _REDIR = IORedirector()

    with open(parsed.grammar, "r", encoding="utf-8") as file:
        grammar = file.read()
        generated = '\n\n'.join((
            get_function_defs(),
            'TARGET: ' + ' | '.join(tuple(f'"{t}"i' for t in _VALID_TARGETS)),
        ))
        grammar = grammar.format(GENERATED_CODE=generated)
        _DD.set_var(None, grammar, *_GRAMMAR_PATH)
        _PARSER = Lark(grammar, start='statements', parser='lalr', debug=True, propagate_positions=True)

    if parsed.execute:
        # For simple statements directly on the command line
        execute_statements(parsed.execute)
    elif parsed.file:
        # NB: we don't "sandbox" these files like we do with others
        for filepath in parsed.file:
            # For statements stored in a file
            statement_text = None
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    statement_text = f.read()
            except OSError as e:
                print_stderr(f"Error reading file {filepath}: {e}")
                break
            execute_statements(statement_text, filepath)
    else:
        if not sys.stdin.isatty():
            # Read from stdin, most likely from a "here" document
            execute_statements(sys.stdin.read())
        else:
            # Interactive execution of one or more statements
            execute_interactive()

if __name__ == '__main__':
    main()
