"""
Implementation of the SELECT statement
"""

from copy import deepcopy
from io import StringIO
from typing import Any
import re

from lark import (
    Tree,
    Token,
    Transformer,
    Visitor,
    v_args,
)
from lark.tree import Meta

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    poly_false,
    poly_plural,
    poly_type,
)
from .data_xtract import (
    DataExtractor,
    EndExtractException,
    InfoOutput,
    QueryFilter,
)
from .encoding import parse_encoding
from .evaluate import bind_operations
from .exec_context import ExecContext
from .output import (
    CSVRecordWriter,
    JSONRecordWriter,
    MarkdownRecordWriter,
    TemplateRecordWriter,
    TextRecordWriter,
)
from .output import RecordWriter, RecordLimiter, RecordCartesianProduct
from .redir import (
    prepare_path,
    stderr,
    stdout,
)
from .stmt_set import (
    get_writable_var_path,
    load_data_type,
    load_file_as,
)
from .tags import control_statement
from .var_name import VAR_NAME
from .xtract_memory import InMemoryExtractor

_ROWID_PATH = ('$rowid', ) # NB: zero based
_DEFAULT_TARGET_NAME = '$record'

_TYPE = 'type'
_TARGET = 'target' # the "From .. As" name
_FILE = 'file' # the data file's name
_VAR = 'var'
_DTYPE = 'dtype' # the data file's type
_ENCODING = 'encoding'# encoding used to read data file
_DATA = 'data' # what we'll iterate over

def create_var_ref(statement, *names):
    # Extract metadata from source statement
    src_meta = statement.meta
    # Create tokens with position info
    tokens = [
        Token('NAME', name,
              line=src_meta.line,
              column=src_meta.column,
              end_line=src_meta.end_line,
              end_column=src_meta.end_column,
              start_pos=src_meta.start_pos,
              end_pos=src_meta.end_pos)
        for name in names
    ]
    # Create meta object
    meta = Meta()
    meta.line = src_meta.line
    meta.column = src_meta.column
    meta.end_line = src_meta.end_line
    meta.end_column = src_meta.end_column
    meta.start_pos = src_meta.start_pos
    meta.end_pos = src_meta.end_pos
    return Tree('var_ref', tokens, meta=meta)

class SelectAnalyzer(Visitor):

    # Unique object to mark "*" in columns
    _ALL_COLS = object()

    _VAR_NAME = re.compile(VAR_NAME)

    _BOOL_OPTS = (
        'array_wrapper',
        'auto_escape',
        'chain_undefined',
        'compact',
        'include_headers',
        'include_nulls',
        'keep_last_newline',
        'lstrip_blocks',
        'sort_keys',
        'trim_blocks',
    )

    _NEG_BOOL_OPTS = {
        # The option to what it negates
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
        self._predicates_bound = False
        self._from_opts = {}
        self._into_opts = {}
        self._output_statements = []
        self._output_statements_bound = False
        self._output_controls = {}
        self._output_opts = {}
        self._headers = []
        # set in analyze()
        self._select_statement = None

    def analyze(self, tree: Tree):
        self._select_statement = tree
        self.visit(tree)
        return self

    @property
    def ctx(self) -> ExecContext:
        return self._ctx

    @property
    def from_opts(self) -> dict:
        return self._from_opts

    @property
    def into_opts(self) -> dict:
        return self._into_opts

    def create_output_opts(self, attrs: list[str]) -> dict:
        # We add these here because they get passed to down to
        # writers et al for possible extra output (mostly Templates)
        self._output_opts['debug'] = self.ctx.debug
        self._output_opts['verbose'] = self.ctx.verbose
        # We need to expand the "*"s in headers and output statements
        if self._ALL_COLS in self._headers:
            attr_statement = []
            target = self._from_opts[_TARGET]
            if not attrs:
                # The the only attr is the value associated with the "For ... As <target>"
                attrs = [target]
                attr_statement = [ create_var_ref(self._select_statement, target) ]
            else:
                attr_statement = [ create_var_ref(self._select_statement, target, attr) for attr in attrs ]
            headers = []
            outputs_statements = []
            i = 0
            while i < len(self._headers):
                header = self._headers[i]
                if header == self._ALL_COLS:
                    headers.extend(attrs)
                    outputs_statements.extend(attr_statement)
                else:
                    headers.append(header)
                    outputs_statements.append(self._output_statements[i])
                i += 1
            self._headers = headers
            self._output_statements = outputs_statements
        self._output_opts['headers'] = self.make_cols_names_unique(self._headers)
        return self._output_opts

    def get_output_statements(self) -> list:
        if not self._output_statements_bound:
            self._output_statements = [bind_operations(self.add_implicit(o)) for o in self._output_statements]
            self._output_statements_bound = True
        return self._output_statements

    def get_predicates(self) -> list:
        if not self._predicates_bound:
            self._predicates = [bind_operations(self.add_implicit(p)) for p in self._predicates]
            self._predicates_bound = True
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

    def add_implicit(self, tree: Tree) -> Tree:
        """Should only be applied to the outputs and predicates after analysis and "*" expansion!"""
        target = self._from_opts[_TARGET]
        # Expected contents: top level keys for current frame all the way to global
        valid_contexts = self.ctx.dd.keys()
        return ImplicitContextAdder().add_contexts(tree, target, valid_contexts)

    def output(self, node: Tree):
        """
        ... <expr> ...
        A column with a default name
        """
        # NB: do not bind
        expr = node.children[0]
        self._output_statements.append(expr)
        self._headers.append(self.get_default_col_name(expr))

    def output_all(self, _node: Tree):
        """
        ... * ...
        An entry that represents all input columns
        """
        # Add place holders we'll expand later
        self._output_statements.append(None)
        self._headers.append(self._ALL_COLS)

    def output_as(self, node: Tree):
        """
        ... <expr> AS <expr> ...
        Column is explicity named
        """
        # NB: do not bind
        self._output_statements.append(node.children[0])
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
            raise VgrRuntimeError(as_node, TypeError(f"Value for 'As' must be a simple type; found {poly_type(as_value)!r}"))

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
        self._from_opts[_TYPE] = 'memory'
        self._from_opts[_DATA] = node.children[0]
        self._from_opts[_TARGET] = self._get_target_name(node.children[1]) if len(node.children) > 1 else _DEFAULT_TARGET_NAME

    def file_from(self, node: Tree):
        """... From File <filename> [<source_type>] [Encoding Is <expr>] [As <target>] ..."""
        node = bind_operations(node)
        self._from_opts[_TYPE] = 'memory'
        filename = self.ctx.eval_filename_expr(bind_operations(node.children[0]))
        self._from_opts[_FILE] = filename
        encoding = None
        target = None
        dtype = None
        for child in node.children[1:]:
            name = child.data.lower()
            if name == 'encoding':
                encoding = parse_encoding(self._ctx, bind_operations(child))
            elif name == 'var_ref':
                target = self._get_target_name(child)
            else:
                dtype = load_data_type(filename, name)
        self._from_opts[_DTYPE] = dtype or load_data_type(filename, None)
        self._from_opts[_ENCODING] = encoding or 'utf-8-sig'
        self._from_opts[_TARGET] = target or _DEFAULT_TARGET_NAME

    def _get_target_name(self, node: Tree) -> str:
        target = self.ctx.eval_expr_or_const(bind_operations(node))
        if target is None: return _DEFAULT_TARGET_NAME
        if not isinstance(target, str):
            raise VgrRuntimeError(node, TypeError(f"Value for 'As' must be a string; found {poly_type(target)!r}"))
        target = target.strip()
        if self._VAR_NAME.fullmatch(target) is None:
            raise VgrRuntimeError(node, TypeError(f"Value for 'As' must be a valid simple variable name; {target!r}"))
        try:
            # This makes sure you can do something like "... As 'math'"
            self.ctx.dd.validate_user_set_path(target)
            return target
        except ValueError as e:
            raise VgrRuntimeError(node, e) from e

    def where_clause(self, node: Tree):
        """... Where expr (, expr)* ..."""
        # NB: do not bind
        self._predicates.extend(node.children)

    def limit_clause(self, node: Tree):
        """... Limit <limit> (Offset <offset>)? ..."""
        node = bind_operations(node)
        children = node.children
        if len(children) >= 1: self._output_controls['limit'] = self.ctx.eval_to_int(children[0], 'Limit', True)
        if len(children) >= 2: self._output_controls['offset'] = self.ctx.eval_to_int(node.children[1], 'Offset', True)

    def product_clause(self, node: Tree):
        node = bind_operations(node)
        # TODO

    def for_text(self, node: Tree):
        """... For Text <opts>* ..."""
        node = bind_operations(node)
        self._output_opts[_TYPE] = 'text'
        self._parse_output_ops(node)

    def for_json(self, node: Tree):
        """... For JSON <opts>* ..."""
        node = bind_operations(node)
        self._output_opts[_TYPE] = 'json'
        self._parse_output_ops(node)

    def for_csv(self, node: Tree):
        """... For CSV <opts>* ..."""
        node = bind_operations(node)
        self._output_opts[_TYPE] = 'csv'
        self._parse_output_ops(node)

    def for_markdown(self, node: Tree):
        """... For Markdown <opts>* ..."""
        node = bind_operations(node)
        self._output_opts[_TYPE] = 'markdown'
        self._parse_output_ops(node)

    def for_template(self, node: Tree):
        """... For [Record|Batch]? Template <template_filename> <opts>* ..."""
        node = bind_operations(node)
        self._output_opts[_TYPE] = 'template'
        for i, child in enumerate(node.children):
            if self.is_tree(child, 'batch') or self.is_tree(child, 'record'):
                self._output_opts['template_type'] = child.data.lower()
                continue
            if self.is_tree(child, 'template_filename'):
                self._output_opts['template_filename'] = self.ctx.eval_filename_expr(child.children[0])
                continue
            # remainder are options...
            self._parse_output_ops(node, i)
            break

    def into_clause(self, node: Tree):
        """... into_clause: "Into"i (var_name | "File"i (stdout | stderr | expr (_COMMA? encoding)?))"""
        first_child = node.children[0]
        into_type = first_child.data if isinstance(first_child, Tree) else ""
        if into_type in ('stdout', 'stderr'):
            self._into_opts[_TYPE] = into_type
        elif into_type == 'var_name':
            self._into_opts[_TYPE] = _VAR
            self._into_opts[_VAR] = get_writable_var_path(self.ctx, first_child)
        else:
            filename = self.ctx.eval_filename_expr(bind_operations(first_child))
            self._into_opts[_TYPE] = _FILE
            self._into_opts[_FILE] = filename
            for child in node.children[1:]:
                name = child.data.lower()
                if name == 'encoding':
                    self._into_opts[_ENCODING] = parse_encoding(self._ctx, bind_operations(child))
                    continue
                raise NotImplementedError(f'Into option {name!r}') #SNO

    def _display_name(self, name: str) -> str:
        """Util to print nice looking error msgs"""
        return self._OPT_DISPLAY_NAME.get(name, name.capitalize())

    def _parse_output_ops(self, node:Tree, start: int=0) -> None:
        """This is a unified set of options"""
        for c in node.children[start:]:
            name: str = c.data
            # First generic options
            if name in self._BOOL_OPTS:
                self._output_opts[name] = self._bool_arg(c, self._display_name(name))
                continue
            if name in self._NEG_BOOL_OPTS:
                self._output_opts[self._NEG_BOOL_OPTS[name]] = not self._bool_arg(c, self._display_name(name))
                continue
            if name in self._STR_OPTS:
                self._output_opts[name] = self._str_arg(c, self._display_name(name))
                continue
            # Now the special cases
            if name == 'root':
                self._output_opts[name] = self._str_arg(c, 'Root', 'result')
                continue
            if name == 'indent':
                self._output_opts[name] = self._int_arg(c, 'Indent', 2)
                continue
            if name == 'quoting':
                self._output_opts[name] = c.children[0].value.lower()
                continue
            raise NotImplementedError(f'Output option {name!r} of type {self._output_opts["type"]}') #SNO

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
**A Select statement to compose, filter, and output data**

```vgr
**TODO**
```
"""
    into_opts = {}
    buffer_data = None
    dest = None
    ctx.dd.push_frame([(_ROWID_PATH, 0)])
    try:
        select = SelectAnalyzer(ctx).analyze(statement)
        # NB: at this point not all operations will show as bound
        # (notably in the outputs and the predicates) and
        # that is by design, so don't panic
        ctx.print_tree(statement)
        from_opts = select.from_opts
        ctx.dd.declare_var(True, (from_opts[_TARGET],))
        extractor = create_extractor(ctx, from_opts)
        if ctx.debug: ctx.print_debug(repr(extractor))
        # create the final outputs
        output_opts = select.create_output_opts(extractor.attrs)
        # If the type was not set, we use the default
        output_opts[_TYPE] = output_opts.get(_TYPE, 'csv')
        def exec_query(dest):
            writer = create_writer(output_opts, select.output_controls, dest)
            if ctx.debug: ctx.print_debug(repr(writer))
            QueryRunner(ctx, select, writer).run_extraction(extractor)
        into_opts = select.into_opts
        dest = into_opts.get(_TYPE, 'stdout')
        if dest == 'stdout':
            exec_query(stdout())
        elif dest == 'stderr':
            exec_query(stderr())
        elif dest == _FILE:
            mode = 'w'
            with open(prepare_path(into_opts[_FILE], mode),
                      mode,
                      encoding=into_opts.get(_ENCODING, 'utf-8'),
                      errors='backslashreplace' if ctx.debug else 'replace') as f:
                exec_query(f)
        elif dest == _VAR:
            with StringIO() as buffer:
                exec_query(buffer)
                buffer_data = buffer.getvalue()
        else:
            raise TypeError(f"Destination type {dest!r} not handled") # SNO
    finally:
        ctx.dd.pop_frame()
    # Now that we are out of the local frame for the select
    # we can set a value the user can access
    if dest == _VAR:
        ctx.set_var(buffer_data, *into_opts[_VAR])

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
        predicates = self._select.get_predicates()
        if predicates:
            for predicate in predicates:
                if poly_false(self.ctx.eval_expr(predicate)): return False
        record: list = None
        outputs = self._select.get_output_statements()
        # TODO this likely no longer applies
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
    xtype = opts[_TYPE]
    target = opts[_TARGET]
    if xtype == 'memory':
        data = opts.get(_DATA, None)
        if data:
            return InMemoryExtractor(target, ctx.eval_expr(data))
        filename = opts.get(_FILE, None)
        if filename:
            metadata = None
            try:
                with open(filename, 'r', encoding=opts.get(_ENCODING, 'utf-8-sig'), errors='backslashreplace' if ctx.debug else 'replace') as f:
                    data, metadata = load_file_as(filename, f, opts[_DTYPE])
            except Exception as e:
                raise ValueError(f'While reading {filename!r}: {str(e)}') from e
            if not isinstance(data, (list, dict)): data = [data]
            if ctx.verbose:
                records = metadata['records']
                ctx.print_verbose('Read', records, poly_plural(records,'Records', 'Record'), 'From', metadata['filename'])
            return InMemoryExtractor(target, data)
        raise NotImplementedError(f'Extractor type {xtype!r} : no data and no file') #SNO
    raise NotImplementedError(f'Extractor type {xtype!r}') #SNO

def create_writer(opts: dict, controls: dict, dest) -> RecordWriter:
    """
    Using the options, create and configure a writer instance.
    opts - options that define the type and configure the writer
    controls - used in wrapper creation and configuration
    """
    writer: RecordWriter = None
    otype = opts[_TYPE]
    if otype == 'json':
        writer = JSONRecordWriter(dest, stderr=stderr(), **opts)
    elif otype == 'markdown':
        writer = MarkdownRecordWriter(dest, stderr=stderr(), **opts)
    elif otype in ('template', 'template-batch'):
        if otype == 'template-batch': opts['template_type'] = 'batch'
        writer = TemplateRecordWriter(dest, stderr=stderr(), **opts)
    elif otype == 'text':
        writer = TextRecordWriter(dest, stderr=stderr(), **opts)
    else:
        # CSV is the ultimate fallback
        writer = CSVRecordWriter(dest, stderr=stderr(), **opts)
    # Order is important since projections can generate more than one row
    # It depends upon how you want to interpret the limit/offset, and that is TBD
    # TODO option on "product" like "before or after limit"
    writer = RecordLimiter.wrap(writer, **controls)
    writer = RecordCartesianProduct.wrap(writer, **controls)
    return writer
