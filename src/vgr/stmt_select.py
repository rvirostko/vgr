"""
Implementation of the SELECT statement
"""

from typing import Any
from copy import deepcopy
import re

from lark import Tree, Token, Transformer, Visitor, v_args

from .app_exceptions import VgrRuntimeError
from .data_xtract import QueryFilter, InfoOutput, DataExtractor, EndExtractException
from .evaluate import bind_operations
from .exec_context import ExecContext
from .mathpak import poly_false, bound_ops, type_str
from .output import (
    CSVRecordWriter,
    JSONRecordWriter,
    MarkdownRecordWriter,
    TemplateRecordWriter,
    TextRecordWriter,
)
from .output import RecordWriter, RecordLimiter, RecordCartesianProduct
from .redir import stdout, stderr
from .stmt_set import load_data_type, load_file_as
from .tags import control_statement
from .xtract_memory import InMemoryExtractor
from .xtract_vault import VAULT_TARGETS, VaultDataExtractor

_ROWID_PATH = ('$rowid', ) # NB: zero based
_DEFAULT_TARGET_NAME = '$record'

_DATA = 'data'
_FILE = 'file'
_TARGET = 'target'

class SelectAnalyzer(Visitor):

    # NB: Need to keep in sync with grammar
    # TODO it is out of sync...
    _VAR_NAME = re.compile(r'[A-Za-z_](?:[A-Za-z0-9_]|-+[A-Za-z])*(?:\u2032+|[\u2033\u2034\u2057\u2080-\u2089])?')

    _BOOL_OPTS = (
        'array_wrapper',
        'auto_escape',
        'chain_undefined',
        'compact',
        'encode_ascii',
        'include_headers',
        'include_nulls',
        'keep_last_newline',
        'lstrip_blocks',
        'sort_keys',
        'trim_blocks',
    )

    _NEG_BOOL_OPTS = {
        # The option to what it negates
        'encode_unicode'  : 'encode_ascii',
        'exclude_nulls'   : 'include_nulls',
        'no_array_wrapper': 'array_wrapper',
        'omit_headers'    : 'include_headers',
    }

    _STR_OPTS = (
        'delimiter',
        'escapechar',
        'field_sep',
        'header_sep',
        'lineterminator',
        'quotechar',
        'record_sep',
    )

    _OPT_DISPLAY_NAME = {
        # If not present, we just capitalize it
        'array_wrapper'    : 'Array Wrapper',
        'auto_escape'      : 'Auto Escape',
        'chain_undefined'  : 'Chain Undefined Variables',
        'encode_ascii'     : 'Encode ASCII',
        'encode_unicode'   : 'Encode Unicode',
        'escapechar'       : 'Escape Character',
        'exclude_nulls'    : 'Exclude Nulls',
        'field_sep'        : 'Field Separator',
        'header_sep'       : 'Header Separator',
        'include_headers'  : 'Include Headers',
        'include_nulls'    : 'Include Nulls',
        'keep_last_newline': 'Keep Last Newline',
        'lineterminator'   : 'Line Terminator',
        'lstrip_blocks'    : 'Left Strip Blocks',
        'no_array_wrapper' : 'No Array Wrapper',
        'omit_headers'     : 'Omit Headers',
        'quotechar'        : 'Quote Character',
        'record_sep'       : 'Record Separator',
        'sort_keys'        : 'Sort Keys',
        'trim_blocks'      : 'Trim Blocks',
    }

    def __init__(self, ctx: ExecContext):
        super().__init__()
        self._ctx = ctx
        self._predicates = []
        self._from_opts = {}
        self._output_statements = []
        self._output_controls = {}
        self._output_opts = {}
        self._headers = [] # TODO why a sep item here?

    def analyze(self, tree: Tree):
        self.visit(tree)
        return self

    @property
    def ctx(self) -> ExecContext:
        return self._ctx

    @property
    def from_opts(self) -> dict:
        return self._from_opts

    @property
    def output_opts(self) -> dict:
        return self._output_opts

    @property
    def output_statements(self) -> list:
        return self._output_statements

    @property
    def predicates(self) -> list:
        return self._predicates

    @property
    def output_controls(self) -> dict:
        return self._output_controls

    #----
    # visitor methods
    #----
    def select(self, _: Tree):
        """
        Everything else should have been handled by other visitors
        """
        # We add these here because they get passed to down to
        # writers et al for possible extra output (mostly Templates)
        self.output_opts['debug'] = self.ctx.debug
        self.output_opts['verbose'] = self.ctx.verbose
        # If there were no output statements (Select From...)
        # we are extracting the entire record and the target
        # name is the name for the columns
        if not self.output_statements:
            self._headers.append(self.from_opts[_TARGET])
        self.output_opts['headers'] = self.make_cols_names_unique(self._headers)
        self._output_statements = [bind_operations(self.add_implicit(o)) for o in self.output_statements]
        self._predicates = [bind_operations(self.add_implicit(p)) for p in self.predicates]

    def add_implicit(self, tree: Tree) -> Tree:
        """Should only be applied to the outputs and predicates after analysis!"""
        from_type = self.from_opts['type']
        target = self.from_opts[_TARGET]
        # Expected contents: top level keys for current frame all the way to global
        valid_contexts = self.ctx.dd.keys()
        if from_type == 'from_vault': valid_contexts += VAULT_TARGETS
        return ImplicitContextAdder().add_contexts(tree, target, valid_contexts)

    def output(self, node: Tree):
        """
        ... <expr> ...
        A column with a default name
        """
        # NB: do not bind
        expr = node.children[0]
        self.output_statements.append(expr)
        self._headers.append(self.get_default_col_name(expr))

    def output_as(self, node: Tree):
        """
        ... <expr> AS <expr> ...
        Column is explicity named
        """
        # NB: do not bind
        self.output_statements.append(node.children[0])
        # If it is an output_as, it will have two children:
        # The second child is the "as"
        # NB: if blank, it will get a default later
        #     Also note that we don't trim string values
        #     as spaces are legal in dictionaries and csv files
        as_node = node.children[1]
        as_value = self.ctx.eval_expr_or_const(bind_operations(as_node))
        if as_value is None or isinstance(as_value, (str, int, float)):
            self._headers.append(as_value)
        else:
            raise VgrRuntimeError(as_node, TypeError(f"Value for 'As' must be a simple type; found {type_str(as_value)}"))

    @classmethod
    def get_default_col_name(cls, node: Tree) -> str:
        # If they have some type of constant, we'll use it if it is a simple type
        if isinstance(node, Token):
            value = node.value
            return str(value).strip() if isinstance(value, (str, int, float)) else ''
        if isinstance(node, Tree):
            # For variable names, we just make that into a string
            if node.data == 'var_ref': return '.'.join(name.value for name in node.children)
            # We'll inherit the name for function calls, but not other ops
            if node.data in ['function_call', 'dotfunction_call']: return cls.get_default_col_name(node.children[0])
        # We'll figure out the default later
        return None

    @classmethod
    def make_cols_names_unique(cls, col_names: list[str]) -> list[str]:
        # Dictionary tracks number of uses of each name
        counter = {}
        rc = []
        for i, name in enumerate(col_names):
            # Assign unamed cols their index
            if name is None: name = f'col_{i + 1}'
            # If name exists append the count to the name
            if name in counter:
                v = counter[name] + 1
                counter[name] = v
                name = f'{name}_{v}'
            else:
                counter[name] = 1
            rc.append(name)
        return rc

    def expr_from(self, node: Tree):
        """... From <expr> [As <target>] ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'memory'
        self.from_opts[_DATA] = node.children[0]
        self.from_opts[_TARGET] = self._get_target_name(node.children[1]) if len(node.children) > 1 else _DEFAULT_TARGET_NAME

    def file_from(self, node: Tree):
        """... From File <filename> [As <target>] ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'memory'
        filename = self.ctx.eval_filename_expr(bind_operations(node.children[0]))
        self.from_opts[_FILE] = filename
        self.from_opts['dtype'] = load_data_type(filename, None)
        self.from_opts[_TARGET] = self._get_target_name(node.children[1]) if len(node.children) > 1 else _DEFAULT_TARGET_NAME

    def file_from_typed(self, node: Tree):
        """... From File <filename> <source_type> [As <target>] ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'memory'
        filename = self.ctx.eval_filename_expr(bind_operations(node.children[0]))
        self.from_opts[_FILE] = filename
        self.from_opts['dtype'] = load_data_type(filename, node.children[1])
        self.from_opts[_TARGET] = self._get_target_name(node.children[2]) if len(node.children) > 2 else _DEFAULT_TARGET_NAME

    def _get_target_name(self, node: Tree) -> str:
        target = self.ctx.eval_expr_or_const(bind_operations(node))
        if target is None: return _DEFAULT_TARGET_NAME
        if not isinstance(target, str):
            raise VgrRuntimeError(node, TypeError(f"Value for 'As' must be a string; found {type_str(target)}"))
        target = target.strip()
        if self._VAR_NAME.fullmatch(target) is None:
            raise VgrRuntimeError(node, TypeError(f"Value for 'As' must be a valid simple variable name; {target!r}"))
        try:
            # This makes sure you can do something like "... As 'math'"
            self.ctx.dd.validate_user_set_path(target)
            return target
        except ValueError as e:
            raise VgrRuntimeError(node, e) from e

    def from_vault(self, node: Tree):
        """... From Vault <vault-target> ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'vault'
        self.from_opts[_TARGET] = node.children[0].value.lower()

    def where_clause(self, node: Tree):
        """... Where expr (, expr)* ..."""
        # NB: do not bind
        self._predicates.extend(node.children)

    def limit_clause(self, node: Tree):
        """... Limit <limit> (Offset <offset>)? ..."""
        node = bind_operations(node)
        children = node.children
        if len(children) >= 1: self.output_controls['limit'] = self.ctx.eval_to_int(children[0], 'Limit', True)
        if len(children) >= 2: self.output_controls['offset'] = self.ctx.eval_to_int(node.children[1], 'Offset', True)

    def product_clause(self, node: Tree):
        node = bind_operations(node)
        # TODO

    def for_text(self, node: Tree):
        """... For Text <opts>* ..."""
        node = bind_operations(node)
        self.output_opts['type'] = 'text'
        self._parse_output_ops(node)

    def for_json(self, node: Tree):
        """... For JSON <opts>* ..."""
        node = bind_operations(node)
        self.output_opts['type'] = 'json'
        self._parse_output_ops(node)

    def for_csv(self, node: Tree):
        """... For CSV <opts>* ..."""
        node = bind_operations(node)
        self.output_opts['type'] = 'csv'
        self._parse_output_ops(node)

    def for_markdown(self, node: Tree):
        """... For Markdown <opts>* ..."""
        node = bind_operations(node)
        self.output_opts['type'] = 'markdown'
        self._parse_output_ops(node)

    def for_template(self, node: Tree):
        """... For [Record|Batch]? Template <template_filename> <opts>* ..."""
        node = bind_operations(node)
        self.output_opts['type'] = 'template'
        for i, child in enumerate(node.children):
            if self.is_tree(child, 'batch') or self.is_tree(child, 'record'):
                self.output_opts['template_type'] = child.data.lower()
                continue
            if self.is_tree(child, 'template_filename'):
                self.output_opts['template_filename'] = self.ctx.eval_filename_expr(child.children[0])
                continue
            # remainder are options...
            self._parse_output_ops(node, i)
            break

    def _display_name(self, name: str) -> str:
        """Util to print nice looking error msgs"""
        return self._OPT_DISPLAY_NAME.get(name, name.capitalize())

    def _parse_output_ops(self, node:Tree, start: int=0) -> None:
        """This is a unified set of options"""
        for c in node.children[start:]:
            name: str = c.data
            # First generic options
            if name in self._BOOL_OPTS:
                self.output_opts[name] = self._bool_arg(c, self._display_name(name))
                continue
            if name in self._NEG_BOOL_OPTS:
                self.output_opts[self._NEG_BOOL_OPTS[name]] = not self._bool_arg(c, self._display_name(name))
                continue
            if name in self._STR_OPTS:
                self.output_opts[name] = self._str_arg(c, self._display_name(name))
                continue
            # Now the special cases
            if name == 'root':
                self.output_opts[name] = self._str_arg(c, 'Root', 'result')
                continue
            if name == 'indent':
                self.output_opts[name] = self._int_arg(c, 'Indent', 2)
                continue
            if name == 'quoting':
                self.output_opts[name] = c.children[0].value.lower()
                continue
            raise NotImplementedError(f'Output option {name!r} of type {self.output_opts["type"]}') #SNO

    def _bool_arg(self, node:Tree, name: str) -> bool:
        return self.ctx.eval_to_bool(node.children[0], name, True) if node.children else True

    def _int_arg(self, node:Tree, name: str, default: int=0) -> int:
        return self.ctx.eval_to_int(node.children[0], name, True) if node.children else default

    def _str_arg(self, node:Tree, name: str, default: str=None) -> str:
        return self.ctx.eval_to_str(node.children[0], name, True) if node.children else default

    @staticmethod
    def is_token(child, token_type: str) -> bool:
        return isinstance(child, Token) and child.type == token_type

    @staticmethod
    def is_tree(child, tree_data: str) -> bool:
        return isinstance(child, Tree) and child.data == tree_data

@v_args(tree=True)
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
            self._valid_contexts = list(valid_contexts)
            self._valid_contexts.append(target)
            return super().transform(deepcopy(tree))
        finally:
            self._target = None
            self._valid_contexts = None

    def var_ref(self, tree):
        first_child = tree.children[0]
        if first_child.value not in self._valid_contexts:
            # Add the target as an implied context for the name
            tree.children.insert(0, Token("NAME", self._target))
        return tree

@control_statement
@bound_ops("Select")
def execute_select(ctx: ExecContext, statement: Tree):
    """
** A Select statement for lists, files, and data sources**

TODO
"""
    ctx.dd.push_frame([(_ROWID_PATH, 0)])
    try:
        select = SelectAnalyzer(ctx).analyze(statement)
        # NB: at this point not all operations will show as bound
        # (notably in the outputs and the predicates) and
        # that is by design, so don't panic
        ctx.print_tree(statement)
        output_opts = select.output_opts
        from_opts = select.from_opts
        ctx.dd.declare_var(True, (from_opts[_TARGET],))
        # If the type was not set, we use the default
        output_opts['type'] = output_opts.get('type', 'csv')
        writer = create_writer(output_opts, select.output_controls)
        if ctx.debug: ctx.print_debug(repr(writer))
        extractor = create_extractor(ctx, from_opts)
        if ctx.debug: ctx.print_debug(repr(extractor))
        QueryRunner(ctx, select, writer).run_extraction(extractor)
    finally:
        ctx.dd.pop_frame()

class QueryRunner(QueryFilter, InfoOutput):
    def __init__(self, ctx: ExecContext, select: SelectAnalyzer, writer: RecordWriter):
        self._ctx = ctx
        self._select = select
        self._writer = writer
        self._rowid = -1

    @property
    def ctx(self) -> ExecContext:
        return self._ctx

    @property
    def rowid(self) -> int:
        return self._rowid

    @rowid.setter
    def rowid(self, value: int) -> int:
        self._rowid = int(value)
        self.ctx.set_var(self._rowid, *_ROWID_PATH)

    def inc_rowid(self):
        self.rowid += 1

    def run_extraction(self, extractor: DataExtractor) -> None:
        """
        The writer started up, and if it can proceede, we turn
        the process, essentialy, over to the extractor.
        Here we handle clean up, especial on the receipt of
        a DataLimitExceededException: this is the only place where
        this should be caught.
        """
        extractor.start(self)
        if self._writer.start():
            try:
                self.rowid = -1
                try:
                    extractor.extract(self, self)
                except EndExtractException:
                    pass
                finally:
                    self._writer.finish()
            finally:
                extractor.finish(self)

    # An "applicable" predicate is one that has either no var refs ("True" or "5 < 7")
    # or whose top-level var ref step is "satisfied" by being present in the
    # data dictionary (the entry could be None, but that is a value)

    # Intermediate means we are checking if we should proceed down some object
    # tree of data. Intermediates are not sent to the output, but if any
    # applicable predicate returns False, we'll return that to the extractor
    # so it knows it should not pursue that path

    # For target output, we check all predicates and they all must return true
    # before we output any data

    # And of course, if there are no predicates, both intermediate and target
    # checks pass without anything being tested.

    def filter_intermediate(self) -> bool:
        # TODO eval applicable predicates until you get a failure
        return True

    def filter_target(self, data: Any) -> bool:
        # Always incremented, even if the row ends up
        # not being selected for output
        self.inc_rowid()
        # We return true or false, which the extractor can check,
        # but it is not prescriptive: False does not mean stop...
        # Evaluate all predicates: first failure causes the
        # record to be skipped.
        predicates = self._select.predicates
        if predicates:
            for predicate in predicates:
                if poly_false(self.ctx.eval_expr(predicate)): return False
        record: list = None
        outputs = self._select.output_statements
        if outputs:
            record = [ self.ctx.eval_expr(expr) for expr in outputs ]
        else:
            # Result of a "Select From ..." so your output is
            # the entirty of the target data.
            # NB: The JSON writer has special handling for this
            record = [ data ]
        try:
            if not self._writer.write(record):
                raise EndExtractException()
            return True
        finally:
            pass

    def set_data(self, key: str, data: Any) -> None:
        """
        Used to set intermediate and target data items in the
        data dictionary prior to any filter call.
        The extractor is responsible for calling unset_data()
        on these items once they go out of scope within their
        data model.
        """
        if data is None:
            # It is important that we clear this out
            # since the presence of items in the DD can
            # affect filter_intermediate behavior.
            self.unset_data(key)
        else:
            self.ctx.set_var_user(data, key)

    def unset_data(self, key: str) -> None:
        """
        Used to remove intermediate and target data item
        from the data dictionary.
        See set_data().
        """
        self.ctx.dd.unset_var(key)

    def print_debug(self, *args, **kwargs):
        self.ctx.print_debug(*args, **kwargs)

    def print_verbose(self, /, *args, **kwargs):
        self.ctx.print_verbose(*args, **kwargs)

def create_extractor(ctx: ExecContext, opts: dict) -> DataExtractor:
    """
    Using the options, create an extractor for data.
    """
    xtype = opts['type']
    target = opts[_TARGET]
    if xtype == 'vault':
        # TODO Much more complicated in the future...
        return VaultDataExtractor(target)
    if xtype == 'memory':
        data = opts.get(_DATA, None)
        if data:
            return InMemoryExtractor(ctx.eval_expr(data), target)
        filename = opts.get(_FILE, None)
        if filename:
            # TODO need input encoding opt, default to utf-8-sig
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    data, _ = load_file_as(f, opts['dtype'])
            except Exception as e:
                raise ValueError(f'While reading {filename!r}: {str(e)}') from e
            if not isinstance(data, list):
                data = [data] if isinstance(data, dict) else [{'value' : data}]
            if ctx.verbose: ctx.print_verbose('Read', len(data), 'Records ' if len(data) != 1 else 'Record', 'From', filename)
            return InMemoryExtractor(data, target)
        raise NotImplementedError(f'Extractor type {xtype!r} : no data and no file') #SNO
    raise NotImplementedError(f'Extractor type {xtype!r}') #SNO

def create_writer(opts: dict, controls: dict) -> RecordWriter:
    """
    Using the options, create and configure a writer instance.
    opts - options that define the type and configure the writer
    controls - used in wrapper creation and configuration
    """
    writer: RecordWriter = None
    otype = opts['type']
    if otype == 'json':
        writer = JSONRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype == 'markdown':
        writer = MarkdownRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype in ('template', 'template-batch'):
        if otype == 'template-batch': opts['template_type'] = 'batch'
        writer = TemplateRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype == 'text':
        writer = TextRecordWriter(stdout(), stderr=stderr(), **opts)
    else:
        # CSV is the ultimate fallback
        writer = CSVRecordWriter(stdout(), stderr=stderr(), **opts)
    # Order is important since projections can generate more than one row
    # It depends upon how you want to interpret the limit/offset, and that is TBD
    # TODO option on "product" like "before or after limit"
    writer = RecordLimiter.wrap(writer, **controls)
    writer = RecordCartesianProduct.wrap(writer, **controls)
    return writer
