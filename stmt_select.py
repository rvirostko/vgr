"""
TODO
"""

from typing import Any
from copy import deepcopy

from lark import Tree, Token, Transformer, Visitor, v_args

from data_dict import DataDictionary
from data_xtract import QueryFilter, InfoOutput, DataExtractor, EndExtractException
from dbg import print_tree
from dd_config import DEFAULT_FOR_TYPE_PATH, ROWID_PATH, dd_clear_scratch
from evaluate import bind_operations, eval_expr, eval_to_bool, eval_to_int, eval_to_str, eval_filename_expr
from mathpak import poly_bool
from output import CSVRecordWriter, JSONRecordWriter, MarkdownRecordWriter, TemplateRecordWriter, TextRecordWriter
from output import RecordWriter, RecordLimiter, RecordCartesianProduct
from redir import stdout, stderr, print_stderr
from stmt_set import load_data_type, load_file_as
from xtract_memory import InMemoryExtractor
from xtract_vault import VAULT_TARGETS, VaultDataExtractor

class SelectAnalyzer(Visitor):

    _DEFAUL_TARGET_NAME = '_record'

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

    def __init__(self, dd: DataDictionary):
        super().__init__()
        self._dd = dd
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
    def dd(self) -> DataDictionary:
        return self._dd

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
        self.output_opts['debug'] = self._dd.debug
        self.output_opts['verbose'] = self._dd.verbose
        # If there were no output statements (Select From...)
        # we are extracting the entire record and the target
        # name is the name for the columns
        if not self.output_statements:
            self._headers.append(self.from_opts['target'])
        self.output_opts['headers'] = self.make_cols_names_unique(self._headers)
        from_type = self.from_opts['type']
        target = self.from_opts['target']
        self._output_statements = [bind_operations(add_implicit(self._dd, from_type, target, o))
                                   for o in self.output_statements]
        # TODO for predicates, this might be premature...
        self._predicates = [bind_operations(add_implicit(self._dd, from_type, target, p))
                            for p in self.predicates]

    def output(self, node: Tree):
        """
        ... <expr> ...
        Makes a default column name
        """
        # NB: do not bind
        expr = node.children[0]
        self.output_statements.append(expr)
        self._headers.append(self.get_default_col_name(expr))

    @classmethod
    def get_default_col_name(cls, node: Tree) -> str:
        # If they have some type of constant, we'll use it
        if isinstance(node, Token): return str(node.value).strip()
        if isinstance(node, Tree):
            # For variable names, we just make that into a string
            if node.data == 'var_ref': return '.'.join(name.value for name in node.children)
            # We'll inherit the name for <name>.func(), but not other ops
            if node.data == 'function_call': return cls.get_default_col_name(node.children[0])
        # We'll figure out the default later
        return ''

    @classmethod
    def make_cols_names_unique(cls, col_names: list[str]) -> list[str]:
        # Dictionary tracks number of uses of each name
        counter = {}
        rc = []
        for i, name in enumerate(col_names):
            # Assign unamed cols their index
            if name == '': name = f'col_{i + 1}'
            # If name exists append the count to the name
            if name in counter:
                v = counter[name] + 1
                counter[name] = v
                name = f'{name}_{v}'
            else:
                counter[name] = 1
            rc.append(name)
        return rc

    def output_as(self, node: Tree):
        """
        ... <expr> AS [name|string] ...
        Column is explicity named
        """
        # NB: do not bind
        self.output_statements.append(node.children[0])
        # If it is an output_as, it will have two children:
        # The second child will be either a NAME or a STRING,
        # but all we need is its value regardless of type
        # NB: if blank, it will get a default later
        self._headers.append(node.children[1].value.strip())

    def from_var(self, node: Tree):
        """... From Var <name> [As <target>] ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'memory'
        self.from_opts['var'] = tuple(name.value for name in node.children[0].children)
        self.from_opts['target'] = node.children[1].value if len(node.children) > 1 else self._DEFAUL_TARGET_NAME

    def from_file(self, node: Tree):
        """... From File <filename> <opt>? [As <target>] ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'memory'
        filename = eval_filename_expr(self._dd, bind_operations(node.children[0]))
        self.from_opts['file'] = filename
        target_node = None
        opt_node = None
        c = len(node.children)
        if c == 2:
            if isinstance(node.children[1], Token):
                target_node = node.children[1]
            else:
               opt_node = node.children[1]
        elif c == 3:
            opt_node = node.children[1]
            target_node = node.children[2]
        self.from_opts['dtype'] = load_data_type(filename, opt_node)
        self.from_opts['target'] = target_node.value if target_node else self._DEFAUL_TARGET_NAME

    def from_vault(self, node: Tree):
        """... From [Vault] <vault-target> ..."""
        node = bind_operations(node)
        self.from_opts['type'] = 'vault'
        self.from_opts['target'] = node.children[0].value.lower()

    def where_clause(self, node: Tree):
        """... Where expr (, expr)* ..."""
        # NB: do not bind
        self._predicates.extend(node.children)

    def limit_clause(self, node: Tree):
        """... Limit <limit> (Offset <offset>)? ..."""
        node = bind_operations(node)
        children = node.children
        if len(children) >= 1: self.output_controls['limit'] = eval_to_int(self._dd, children[0], 'Limit', True)
        if len(children) >= 2: self.output_controls['offset'] = eval_to_int(self._dd, node.children[1], 'Offset', True)

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
            if self.is_token(child, 'TEMPLATE_TYPE'):
                self.output_opts['template_type'] = child.value.lower()
                continue
            if self.is_tree(child, 'template_filename'):
                self.output_opts['template_filename'] = eval_filename_expr(self._dd, child.children[0])
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
            raise NotImplementedError(f'Output option {repr(name)} of type {self.output_opts["type"]}') #SNO

    def _bool_arg(self, node:Tree, name: str) -> bool:
        return eval_to_bool(self._dd, node.children[0], name, True) if node.children else True

    def _int_arg(self, node:Tree, name: str, default: int=0) -> int:
        return eval_to_int(self._dd, node.children[0], name, True) if node.children else default

    def _str_arg(self, node:Tree, name: str, default: str=None) -> str:
        return eval_to_str(self._dd, node.children[0], name, True) if node.children else default

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
            return super().transform(deepcopy(tree)) # TODO speculative
        finally:
            self._target = None
            self._valid_contexts = None

    def var_ref(self, tree):
        first_child = tree.children[0]
        if first_child.value not in self._valid_contexts:
            # Add the target as an implied context for the name
            tree.children.insert(0, Token("NAME", self._target))
        return tree

def add_implicit(dd, from_type, target, tree) -> Tree:
    """should only be applied to the outputs and predicates after analysis!"""
    valid_contexts = [*dd.keys()]
    if from_type == 'from_vault': valid_contexts += VAULT_TARGETS
    return ImplicitContextAdder().add_contexts(tree, target, valid_contexts)

def execute_select(dd: DataDictionary, statement: Tree):
    select = SelectAnalyzer(dd).analyze(statement)
    # NB: at this point not all operations will show as bound
    # (notably in the outputs and the predicates) and
    # that is by design, so don't panic
    if dd.debug: print_tree(statement)
    output_opts = select.output_opts
    # If the type was not set, we use the default, and if not there, use CSV
    output_opts['type'] = output_opts.get('type', (dd.get_var_user(*DEFAULT_FOR_TYPE_PATH) or 'csv').lower())
    writer = create_writer(output_opts, select.output_controls)
    if dd.debug: print_stderr(repr(writer))
    extractor = create_extractor(dd, select.from_opts)
    if dd.debug: print_stderr(repr(extractor))
    QueryRunner(dd, select, writer).run_extraction(extractor)

class QueryRunner(QueryFilter, InfoOutput):
    def __init__(self, dd: DataDictionary, select: SelectAnalyzer, writer: RecordWriter):
        self._dd = dd
        self._select = select
        self._writer = writer
        self._rowid = 0

    @property
    def rowid(self) -> int:
        return self._rowid

    @rowid.setter
    def rowid(self, value: int) -> int:
        self._rowid = int(value)
        self._dd.set_var_user(self._rowid, *ROWID_PATH)

    def inc_rowid(self):
        self.rowid += 1

    def run_extraction(self, extractor: DataExtractor) -> None:
        """
        The writer is started up, and if it can proceede, we turn
        the process, essentially, over to the extractor.
        Here we handle clean up, especial on the receipt of
        a DataLimitExceededException: this is the only place where
        this should be caught.
        """
        self.rowid = 0
        extractor.start(self)
        if self._writer.start():
            try:
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
                if not poly_bool(eval_expr(self._dd, predicate)): return False
        record: list = None
        outputs = self._select.output_statements
        if outputs:
            record = [ eval_expr(self._dd, expr) for expr in outputs ]
        else:
            # Result of a "Select From ..." so your output is
            # the entirity of the target data.
            # NB: The JSON writer has special handling for this
            record = [ data ]
        try:
            if  not self._writer.write(record):
                raise EndExtractException()
            return True
        finally:
            dd_clear_scratch(self._dd)

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
            self._dd.set_var_user(data, key)

    def unset_data(self, key: str) -> None:
        """
        Used to remove intermediate and target data item
        from the data dictionary.
        See set_data().
        """
        self._dd.unset_var_user(key)

    def print_debug(self, *args, **kwargs):
        if self._dd.debug: print_stderr(*args, **kwargs)

    def print_verbose(self, /, *args, **kwargs):
        if self._dd.verbose: print_stderr(*args, **kwargs)

def create_extractor(dd: DataDictionary, opts: dict) -> DataExtractor:
    """
    Using the options, create an extractor for data.
    """
    xtype = opts['type']
    target = opts['target']
    if xtype == 'vault':
        # TODO Much more complicated in the future...
        return VaultDataExtractor(target)
    if xtype == 'memory':
        path = opts.get('var', None)
        if path:
            return InMemoryExtractor(dd.get_var_user(*path), target)
        filename = opts.get('file', None)
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                data, _ = load_file_as(f, opts['dtype'])
            if not isinstance(data, list):
                data = [data] if isinstance(data, dict) else [{'value' : data}]
            if dd.verbose: print_stderr(dd, 'Read', len(data), 'Records ' if len(data) != 1 else 'Record', 'From', filename)
            return InMemoryExtractor(data, target)
    raise NotImplementedError(f'Extractor type {repr(xtype)}') #SNO

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
