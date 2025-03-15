#! /usr/bin/env python3

from collections import defaultdict
from data_dict import DataDictionary
from lark import Lark, Tree, Token, Transformer, Visitor, v_args, UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken
from mathpak import *
from output import *
from typing import Any
import argparse
import ast
import csv
import glob
import inspect
import json
import os
import re
import sys
import zipfile

"""Binds a (pretty) name to the function to be executed"""
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
  "IsIdentifier":  poly_isidentifier,
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

def get_function_op(name: str):
    """Given a function name get the function that implements it"""
    rc = _FUNC_OPS.get(_FUNC_INDEX.get(name.lower()), None)
    if not rc: raise NotImplementedError(f'Function {name} not yet implemented')
    return rc

"""The max value of an arg range when we have variable arguments"""
_IS_VARARGS = float('inf')

def get_arg_range(op) -> tuple:
    """Get the argument range for the function definition in the grammar"""
    if op == None: raise ValueError('Expected a function, but got None')
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
        rc += ')\\s*(?=\()/i'
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

_VGR_GRAMMAR=f"""

// Omitted from the parse tree
_DOT: "."
_COMMA: ","
_LPAREN: "("
_RPAREN: ")"
_SEMICOLON: ";"
_OSB: "["
_CSB: "]"

// Converted to their literal values after parsing
TRUE: "true"i
FALSE: "false"i
NONE: "none"i | "nil"i | "null"i

// Numeric values
// NB: octal and binary regexs are shorter than the length
//     of the decimal regex, so we need to boost their
//     priorities so the former's leading zero doesn't get
//     prematurely matched by the latter.
HEX_NUMBER.2: /0[xX](_?[0-9a-fA-F])+/
OCT_NUMBER.2: /0[oO](_?[0-7])+/
BIN_NUMBER.2: /0[bB](_?[01])+/
DEC_NUMBER: /[+-]?[0-9](_?[0-9])*/
_SPECIAL_DEC: /[0-9](_?[0-9])*/
_EXP_PART: /[eE][+-][0-9](_?[0-9])*/
// NB: slight difference from Python as floats can't end with a "."
_DECIMAL: _DOT _SPECIAL_DEC | _SPECIAL_DEC _DOT _SPECIAL_DEC
FLOAT_NUMBER: /[+-]/? (_SPECIAL_DEC _EXP_PART | _DECIMAL _EXP_PART?)

// "snake case", "kabab case", and mixed version of the two
// For "kabab", it cannot start with a hyphen and an alpha character must follow a hyphen
// This is an attempt to prevent some subtraction operations from looking like identifiers
NAME: /[A-Za-z_]([A-Za-z0-9_]|-+[A-Za-z])*/

statements: statement+
?statement: assign
    | load_from
    | assert
    | print | printf | exhibit
    | open
    | close
    | delete
    | select
    | zip
    | exit

?assign: "Let"i var_name ("=" | ":=") expr _SEMICOLON? -> set
    | "Set"i var_name ("=" | ":=" | "To"i) expr _SEMICOLON? -> set
    | "Move"i expr "To"i var_name _SEMICOLON? -> move // This is here because Ian inadvertantly reminded me it exists

load_from: "Load"i var_name "From"i "File"i? expr load_source_type? _SEMICOLON?
load_source_type: "JSON"i "Object"i? -> json_object
    | "JSON"i "Object"i? "Per"i "Line"i -> json_objects
    | "CSV"i -> csv_file
    | "TEXT"i -> text_file

assert: "Assert"i expr (":" expr)? _SEMICOLON?

printf: "Printf"i (expr (_COMMA expr (_COMMA expr)*)?)? _SEMICOLON?

print: "Print"i (expr (_COMMA expr)*)? _SEMICOLON?

exhibit: "Exhibit"i (var_name (_COMMA var_name)*)? _SEMICOLON?

open: "Open"i io_type "File"i? expr open_ext? _SEMICOLON?
?io_type: ("Error"i | "stderr"i) -> stderr
    | ("Output"i | "stdout"i) -> stdout
?open_ext: ("Append"i | "Extend"i | "a") -> a
    | ("Overwrite"i | "w"i) -> w
    | ("No"i "Overwrite"i | "x"i) -> x
close: "Close"i io_type "File"i? _SEMICOLON? -> close

delete: "Delete"i "File"i? expr (_COMMA expr)* _SEMICOLON?

zip: "Create"i "Zip"i "File"i? expr (zip_option (_COMMA zip_option)*)? _SEMICOLON?
?zip_option: "Password"i expr -> password
    | "Comment"i expr -> comment
    | "Include"i expr+ -> include
    | "Exclude"i expr+ -> exclude

exit: "Exit"i expr?

select: "Select"i outputs? "From"i TARGET where_clause? (join_clause+ | auto_join_clause)? product_clause? limit_clause? for_clause? _SEMICOLON?

?for_clause: "For"i for_json
    | "For"i for_csv
    | "For"i for_markdown
    | "For"i for_template

for_json: "JSON"i (json_option (_COMMA json_option)*)?
?json_option: encode_ascii
    | encode_unicode
    | encode_unicode_sig
    | "Root"i NAME -> root
    | "Indent"i (DEC_NUMBER | NONE | var_name) -> indent
    | "Compact"i -> compact
    | include_nulls
    | exclude_nulls
    | "With" "Array"i? "Wrapper"i -> with_wrapper
    | ("Without"i | "No"i) "Array"i? "Wrapper"i -> no_wrapper
    | ("Sort"i "Keys"i? | "Sorted"i) -> sorted

for_csv: "CSV"i (csv_option (_COMMA csv_option)*)?
?csv_option: encode_ascii
    | encode_unicode
    | encode_unicode_sig
    | "Delimiter"i (ESCAPED_STRING | var_name) -> delimiter
    | "Quote"i ("Char"i | "Character"i) (ESCAPED_STRING | var_name) -> quotechar
    | "Escape"i ("Char"i | "Character"i) (ESCAPED_STRING | var_name) -> escapechar
    | "Line"i ("Ender"i | "Terminator"i) (ESCAPED_STRING | var_name) -> lineterminator
    | "Quote"i CSV_QUOTE_TYPE
    | omit_headers
CSV_QUOTE_TYPE: "Minimal"i | "All"i | "Nonnumeric"i | "None"i

for_markdown: "MarkDown"i (markdown_option (_COMMA markdown_option)*)?
?markdown_option: encode_ascii
    | encode_unicode
    | encode_unicode_sig
    | omit_headers

for_template: TEMPLATE_TYPE? "Template"i "File"i? (ESCAPED_STRING | var_name) (_COMMA template_option)*
TEMPLATE_TYPE: "Record"i | "Batch"i
?template_option: encode_ascii
    | encode_unicode
    | encode_unicode_sig
    | "Auto"i "Escape"i -> auto_escape
    | "Debug"i -> debug
    | include_nulls
    | exclude_nulls
    | "Tags"i (ESCAPED_STRING | var_name) -> tags

encode_ascii: "Ascii"i
encode_unicode: "Unicode"i | "UTF8"i | "UTF-8"i
encode_unicode_sig: "Excel"i | "UTF-8-SIG"i | "UTF8-SIG"i
exclude_nulls: ("Exclude"i | "No"i | "Without"i) ("Nulls"i | "Null"i "Values"i)
include_nulls: ("Include"i | "With"i) ("Nulls"i | "Null"i "Values"i)
omit_headers: ("Omit"i | "No"i) "Headers"i

join_clause: "Join"i TARGET "To"i NAME join_as? join_using?
join_as: "As"i (NAME | ESCAPED_STRING)
join_using: "Using"i attr_ref (_COMMA attr_ref)*
attr_ref: NAME (_DOT (NAME))+

auto_join_clause: "Auto"i "Join"i auto_join?
?auto_join: "All"i -> all
    | "None"i -> none
    | NAME (_COMMA NAME)*

?outputs: (output (_COMMA output)*)

output: expr
    | expr "As"i (NAME | ESCAPED_STRING) -> output_as

where_clause: "Where"i expr (("And"i | "&&") expr)*

// Either LIMIT <number> (OFFSET <number>)? or FETCH FIRST <number> ROWS ONLY
limit_clause: _limit_offset | _fetch_first
_limit_offset: "Limit"i (DEC_NUMBER | var_name) ("Offset"i (DEC_NUMBER | var_name))?
_fetch_first: "Fetch"i "First"i (DEC_NUMBER | var_name) "Rows"i "Only"i

product_clause: "Cartesian"i? "Product"i product_cols
product_cols: "All"i -> all
    | "None"i -> none
    | col_spec (_COMMA col_spec)*
?col_spec: DEC_NUMBER
    | NAME
    | ESCAPED_STRING

// Flattening operations out here allows the parse tree to hold
// the operation type explicitly instead of a generic "OP" where
// we need to deal with aliases
?expr: _LPAREN expr _RPAREN
    | "!" expr -> unary_not
    | expr _DOT function -> function_call
    | expr _DOT NAME -> deref
    | expr ("||" | "Or"i) expr -> or_op
    | expr ("+" | "\uFF0B") expr -> add_op
    | expr ("-" | "\u2212") expr -> sub_op
    | expr ("*" | "\u00D7") expr -> mul_op
    | expr ("/" | "\u00F7") expr -> div_op
    | expr "//" expr -> fdiv_op
    | expr ("%" | "Mod"i) expr -> mod_op
    | expr ("**" | "Pow"i) expr -> exp_op
    | expr "&" expr -> bit_and_op
    | expr "|" expr -> bit_or_op
    | expr ("^" | "Xor"i) expr -> bit_xor_op
    | expr ("<<" | "LShift"i) expr -> shl_op
    | expr (">>" | "RShift"i) expr -> shr_op
    | expr ("==" | "Equals"i  | "Is"i | "Is"i? "Equal"i "To"i) expr -> eq_op
    | expr ("!=" | "<>" | "\u2260" | "Is"i "Not"i | "Is"i? "Not"i "Equal"i "To"i) expr -> neq_op
    | expr ("<" | "Is"i? "Less"i "Than"i) expr -> lt_op
    | expr (">" | "Is"i? "Greater"i "Than"i) expr -> gt_op
    | expr ("<=" | "\u2264" | "Is"? "Not"i "Greater"i "Than"i) expr -> le_op
    | expr (">=" | "\u2265" | "Is"i? "Not"i "Less"i "Than"i) expr -> ge_op
    | expr "Is"i? "In"i expr -> in_op
    | expr "Is"i? "Not"i "In"i expr -> not_in_op
    | expr "Contains"i expr -> contains_op
    | expr (("Doesnt"i | "Does"i? "Not"i) "Contain"i) expr -> not_contains_op
    | expr ("~" | "Match"i | "Matches"i) expr -> match_op
    | expr ("IMatch"i | "IMatches"i) expr -> imatch_op
    | expr ("!~" | ("Doesnt"i | "Does"i? "Not"i) "Match"i) expr -> not_match_op
    | expr (("Doesnt"i | "Does"i? "Not"i) "IMatch"i) expr -> not_imatch_op
    | _OSB (expr (_COMMA expr)*)? _CSB -> array         // may become CARRAY at runtime
    | TRUE | FALSE
    | NONE
    | ESCAPED_STRING                                    // becomes STRING at runtime
    | HEX_NUMBER | BIN_NUMBER | OCT_NUMBER | DEC_NUMBER // becomes INT at runtime
    | FLOAT_NUMBER                                      // becomes FLOAT at runtime
    | NAME -> var_ref

var_name: NAME (_DOT NAME)*

// ---- BEGIN GENERATED CODE ----

// -- FROM get_function_defs()
{get_function_defs()}

// -- FROM _VALID_TARGETS
TARGET: {' | '.join(tuple(f'"{t}"i' for t in _VALID_TARGETS))}

// ---- END GENERATED CODE ----

%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

class ImplicitContextAdder(Transformer):
    """
    Modifies 'var_ref' nodes by prepending TARGET if needed
    Assuming target is "kv":
        * kv -> kv (no change, type is a target type)
        * name -> kv.name (not a target type)
    """
    def __init__(self, valid_contexts):
        super().__init__()
        self._target = None
        self._valid_contexts = None

    def transform(self, tree, target: str, valid_contexts):
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
            children.insert(0, Token("NAME", self._target)) ### TODO , first_child.start_pos, first_child.line, first_child.column, first_child.end_line, first_child.end_column, first_child.end_pos))
        return Tree("var_ref", children)

class ConstantsNormalizer(Transformer):
    def ESCAPED_STRING(self, token):
        # Removes the quoting and interprets escape sequences
        # TODO: needs lots of test cases as this reportedly has problems
        return self._new_token(token, "STRING", ast.literal_eval(token.value))
    def TRUE(self, token): return self._new_token(token, token.type, True)
    def FALSE(self, token): return self._new_token(token, token.type, False)
    def NONE(self, token): return self._new_token(token, 'NONE', None)
    def DEC_NUMBER(self, token): return self._to_int(token, 10)
    def HEX_NUMBER(self, token): return self._to_int(token, 16)
    def OCT_NUMBER(self, token): return self._to_int(token, 8)
    def BIN_NUMBER(self, token): return self._to_int(token, 2)
    def FLOAT_NUMBER(self, token): return self._new_token(token, 'FLOAT', float(token.value))
    def _to_int(self, token, base: int): return self._new_token(token, 'INT', int(token.value, base))
    def _new_token(self, token, type: str, value: Any): return Token(type, value, token.start_pos, token.line, token.column, token.end_line, token.end_column, token.end_pos)
    # TODO arrays?

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
    return _DD.get_var(*path)

def deref_var(data: Any, *path: str) -> Any:
    """This is the lookup of a path relative to data"""
    return _DD.get_var_relative(data, *path)

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

SOURCE: str = None
def set_source(s: str) -> str:
    global SOURCE
    SOURCE = s
    return s

def source_for(t: Tree) -> str:
    if not SOURCE: return ''
    start, end = get_subtree_span(t)
    return SOURCE[start:end]

def execute_exit(statement: Tree) -> None:
    rc: int = None
    if statement.children:
        x: Any = poly_firstitem(eval_expr(statement.children[0]))
        try:
            rc = poly_int(x)
        except ValueError:
            rc = int(poly_bool(x))
    sys.exit(rc)

def execute_assert(statement: Tree) -> None:
    # First required operand is the assertion itself
    v: Any = poly_bool(eval_expr(statement.children[0]))
    if not v:
        msg: Any = None
        # message is optional
        if len(statement.children) > 1: msg = poly_str(eval_expr(statement.children[1]))
        print(str(msg) if msg is not None else f'Assertion {source_for(statement)} failed', file=sys.stderr)
        sys.exit(1)

def execute_set(statement: Tree) -> None:
    """Assign a value to a variable.

* SET _variable_ [= | := | TO) _expression_ [;]
* LET _variable_ [= | :=] _expression_ [;]
"""
    var_name, expr = statement.children
    _DD.set_var(eval_expr(expr), *(name.value for name in var_name.children))

def execute_move(statement: Tree) -> None:
    """A COBOL variant of SET.

* MOVE _expression_ TO _variable_ [;]
"""
    expr, var_name = statement.children
    _DD.set_var(eval_expr(expr), *(name.value for name in var_name.children))

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
        _DD.set_var(data, *(name.value for name in var_name.children))

def execute_print(statement: Tree) -> None:
    """Print values, similar to AWK's print statement

* PRINT [;]
* PRINT _expression_ [, _expression_]... [;]

If no expressions are given, a new line is printed (see below)

The results of the expressions are separated by the string defined in _arg.ofs_.
Lines are ended by with the _arg.ors_ string. The defaults are space and new line and
are used if the values are set to _None_.
"""
    print_stdout(*[eval_expr(expr) for expr in statement.children], sep=_DD.get_ofs(), end=_DD.get_ors())

def execute_printf(statement: Tree) -> None:
    """Print formatted values, similar to AWK's printf statement

* PRINTF [;]
* PRINTF _expression_ [, _expression_]... [;]

If no expressions are given, nothing is printed

The first expression is resolved to a string used to format the other values

Formatting syntax is that used in [Python's str.format()](https://docs.python.org/3/library/string.html#formatstrings)

*At this time only positional parameters are supported*
"""
    exprs = [*statement.children]
    format_string = eval_expr(exprs.pop(0)) if len(exprs) else ''
    if not isinstance(format_string, str): raise TypeError(f'Format must be a string; found {type(format_string).__name__}')
    # TODO : how would we support the printing of values in the DD?
    print_stdout(format_string.format(*[eval_expr(expr) for expr in exprs]), end='')

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
            exhibit_value('.'.join(path), _DD.get_var(*path))
    else:
        for key in sorted(_DD.keys()): exhibit_value(key, _DD.get_var(key))

def print_stdout(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stdout(), **kwargs)

def print_stderr(*args, **kwargs) -> None:
    """Same as print() except that it can redirect to an output file"""
    print(*args, file=_REDIR.stderr(), **kwargs)

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
    getattr(_REDIR, stream)(prepare_path(filename), mode=mode)

def eval_stream_name(node: Tree) -> str:
    stream = node.data.lower()
    if stream not in ('stderr', 'stdout'): raise ValueError(f'Unknown stream {stream}') # SNO
    return stream

def eval_filename_expr(expr: Tree) -> str:
    filename = eval_expr(expr)
    if not isinstance(filename, str): raise TypeError(f'File name must be a string; found {type(filename).__name__}')
    return verify_relative_path(filename)

def execute_close(statement: Tree) -> None:
    """Close the output or error file

* CLOSE OUTPUT [FILE] [;]
* CLOSE ERROR [FILE] [;]

Once closed, command output and errors resumes their default destinations.

All redirection is closed at program termination.
"""
    stream = eval_stream_name(statement.children[0])
    getattr(_REDIR, stream)(None)

def execute_delete(statement: Tree) -> None:
    raise NotImplementedError('TODO')

def eval_expr(expr: Any) -> Any:
    if isinstance(expr, Tree):
        if isinstance(expr, Operation): return expr.execute(tuple(eval_expr(arg_exp) for arg_exp in expr.children))
        raise NotImplementedError(f'Unhandled type {expr.data}')
    else:
        if isinstance(expr, Token): return expr.value
        raise NotImplementedError(f'Unknown type {expr.type()}')

def execute_zip(statement: Tree):
    if 1==1: raise NotImplementedError('TODO')
    # first child is expr for file name, ensure for str
    # comment and password are expr, ensure for str
    # for include and exclude:
    #   children are expr.
    #   they can resolve to str, list or tuple
    #   if str, add to list
    #   if list/tuple, unwrap and recursively add (but must be strs)
    #
    zip_name: str = 'foo'
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    # TODO make sure we have at least one include
    comment: str = ''
    # TODO default comment?
    password: str = '' # TODO need other lib?
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        # TODO is this for write? zf.setpassword(password.bytes())
        added_files = set()
        # Collect files to include
        for pattern in include_patterns:
            for file in glob.glob(pattern, recursive=True):
                if os.path.isfile(file): added_files.add(os.path.abspath(file))
        for pattern in exclude_patterns:
            for file in glob.glob(pattern, recursive=True): added_files.remove(os.path.abspath(file))
        # TODO warning if there are no files
        for file in sorted(added_files): zf.write(file, os.path.relpath(file))
        if comment: zf.comment = comment.encode("utf-8")
        # TODO print verbose msg to stdout

def execute_select(statement: Tree):
    ts = TreeSplitter().split(statement)
    statement = ImplicitContextAdder().transform(statement, ts.get_target(), _VALID_TARGETS + _DD.get_internal_prefixes())
    ts.split(statement)
    print(f'Target     : {ts.get_target()}')
    print(f'Predicates : {len(ts.get_predicates())}')
    for i, p in enumerate(ts.get_predicates()): print(f'\t{i + 1} : {source_for(p)}')
    print(f'Outputs    : {len(ts.get_outputs())}')
    for i, o in enumerate(ts.get_outputs()):
        text = source_for(o)
        label = ts.get_label(o)
        label = "_".join(text.strip().split()) if label is None else label
        print(f'\t{i + 1} : {text} "{label}"')
    print(f'Limit      : {ts.get_limit()}')
    print(f'Offset     : {ts.get_offset()}')
    print_tree(statement)

STATEMENT_HANDLERS = {
    'assert': execute_assert,
    'close': execute_close,
    'delete': execute_delete,
    'exhibit': execute_exhibit,
    'exit': execute_exit,
    'load_from': execute_load_from,
    'move': execute_move,
    'open': execute_open,
    'print': execute_print,
    'printf': execute_printf,
    'select': execute_select,
    'set': execute_set,
    'zip': execute_zip,
}

def remove_comments(input: str) -> str:
    """Removes full-line comments but preserves blank lines for Lark metadata accuracy."""
    # We do Hash, C-style, and SQL style
    return re.sub(r'^[ \t]*(#|//|--).*(?:\r?\n|\r|$)', '\n', input, flags=re.MULTILINE)

def execute_statements(inp: str) -> None:
    inp = set_source(remove_comments(inp))
    statements: Tree = _PARSER.parse(inp)
    for statement in statements.children:
        handler = STATEMENT_HANDLERS.get(statement.data, None)
        if not handler: raise ValueError(f'No handler established for {statement.data}')
        statement = ConstantsNormalizer().transform(statement)
        statement = OperationBinder().transform(statement)
        statement_text = source_for(statement)
        _DD.set_statement(statement_text)
        # TODO this does not work well...
        # if _DD.is_echo(): print(statement_text)
        if _DD.is_debug(): print_tree(statement)
        handler(statement)

def print_tree(item: Any, indent=2) -> None:
    prefix = ' ' * indent  # Indentation for nested levels
    if isinstance(item, Tree):
        tree: Tree = item
        op = f':{tree.op_name()}' if isinstance(item, Operation) else ''
        print(f'{prefix}({tree.data}{op}', end=('\n' if tree.children else ''), file=sys.stderr)
        for child in tree.children: print_tree(child, indent + 2)
        print(f'{prefix if tree.children else ""})', file=sys.stderr)  # close the rule
    else:
        if isinstance(item, Token):
            token: Token = item
            print(f'{prefix}{token.type}: {token.value} (Pos: {token.line}:{token.column} {type(token.value)})', file=sys.stderr)
        else:
            raise ValueError(item.type()) # What else can there be?

def get_subtree_span(node):
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

def prompt() -> str: return 'vgr> ' # TODO future?

def execute_interactive() -> None:
    print("Type 'exit' to exit")
    while True:
        try:
            inp = input(prompt())
        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            break
        try:
            execute_statements(inp)
        except (FileExistsError, ValueError, NotImplementedError, TypeError, UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken) as e:
            print(f'{type(e).__name__}: {e}', file=sys.stderr)

_PARSER = Lark(_VGR_GRAMMAR, start='statements', parser='lalr', debug=True)
_REDIR = IORedirector()
_DD: DataDictionary = None

def main():
    global _DD
    parser = argparse.ArgumentParser(
        description="Generic Reporting for Hashicorp Vault - prototype"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--execute', type=str, metavar='STATEMENTS', help='Execute the given statements')
    group.add_argument('-f', '--file', nargs='*', metavar='FILE', help='Execute statements stored in a file')
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    parser.add_argument('user_args', nargs='*', metavar='NAME=VALUE', help='Additional arguments')
    parsed = parser.parse_args()

    _DD = DataDictionary()
    _DD.set_grammar(_VGR_GRAMMAR)
    _DD.set_debug(parsed.debug)
    _DD.set_verbose(parsed.verbose)
    # NB: User args can override debug/echo/verbose...
    _DD.parse_user_args(parsed.user_args)

    if parsed.execute:
        # For simple statements directly on the command line
        execute_statements(parsed.execute)
    elif parsed.file:
        for filepath in parsed.file:
            # For statements stored in a file
            statements = None
            try:
                with open(filepath, 'r') as f:
                    statements = f.read()
            except Exception as e:
                print(f"Error reading file {filepath}: {e}", file=sys.stderr)
                break
            if statements: execute_statements(statements)
    else:
        if not sys.stdin.isatty():
            # Read from stdin, most likely from a "here" document
            execute_statements(sys.stdin.read())
        else:
            # Interactive execution of one or more statements
            execute_interactive()

if __name__ == '__main__':
    main()