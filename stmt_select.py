"""
TODO
"""

from abc import ABC, abstractmethod
from typing import Any

from lark import Tree, Token, Transformer, Visitor, v_args

from data_dict import DataDictionary
from dbg import print_tree
from evaluate import bind_operations, eval_expr, eval_to_bool, eval_to_int, eval_to_str, eval_filename_expr
from output import CSVRecordWriter, JSONRecordWriter, MarkdownRecordWriter, TemplateRecordWriter
from output import RecordWriter, RecordLimiter, RecordCartesianProduct
from redir import stdout, stderr, print_debug
from src_mgr import SSM

VALID_TARGETS = ['ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role']

class SelectAnalyzer(Visitor):

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
        'lineterminator',
        'quotechar',
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
        'include_headers'  : 'Include Headers',
        'include_nulls'    : 'Include Nulls',
        'keep_last_newline': 'Keep Last Newline',
        'lineterminator'   : 'Line Terminator',
        'lstrip_blocks'    : 'Left Strip Blocks',
        'no_array_wrapper' : 'No Array Wrapper',
        'omit_headers'     : 'Omit Headers',
        'quotechar'        : 'Quote Character',
        'sort_keys'        : 'Sort Keys',
        'trim_blocks'      : 'Trim Blocks',
    }

    def __init__(self, dd: DataDictionary, target: str):
        super().__init__()
        self._dd = dd
        self._target = target
        self._predicates = []
        self._output_statements = []
        self._headers = []
        self._output_controls = {}
        self._output_type = None
        self._output_opts = {}

    def analyze(self, tree: Tree):
        self.visit(tree)
        return self

    @property
    def output_type(self) -> str:
        return self._output_type or 'csv'

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

    # TODO add repr

    #--- visitor methods
    def select(self, node: Tree):
        """
        Everything else should have been handled by other visitors
        """
        self.output_opts['debug'] = self._dd.is_debug()
        self.output_opts['verbose'] = self._dd.is_verbose()
        if not self.output_statements:
            self._headers.append(self._target)
        else:
            for i, h in enumerate(self._headers):
                if not h:
                    self._headers[i] = f'col_{i + 1}'
        self.output_opts['headers'] = self._headers

    def output(self, node: Tree):
        expr = node.children[0]
        self.output_statements.append(expr)
        # default label for a variable name
        # note that it will not include anything but the text
        # the user added
        if isinstance(expr, Tree) and expr.data == 'var_ref':
            self._headers.append(SSM.source_for(expr).strip())
        else:
            # If they have some type of constant, we'll use it
            if isinstance(expr, Token) and len(node.children) == 1:
                self._headers.append(str(expr.value).strip())
            else:
                # We'll figure out the default later
                self._headers.append('')

    def output_as(self, node: Tree):
        self.output_statements.append(node.children[0])
        # If it is an output_as, it will have two children:
        # The second child will be either a NAME or a STRING,
        # but all we need is its value regardless of type
        self._headers.append(node.children[1].value.strip())

    def where_clause(self, node: Tree):
        self._predicates.extend(node.children)
        # TODO analyze by usage

    def limit_clause(self, node: Tree):
        children = node.children
        if len(children) >= 1: self._output_controls['limit'] = eval_to_int(self._dd, children[0], 'Limit', True)
        if len(children) >= 2: self._output_controls['offset'] = eval_to_int(self._dd, node.children[1], 'Offset', True)

    def product_clause(self, node: Tree):
        # TODO
        pass

    def for_json(self, node: Tree):
        self._output_type = 'json'
        self._parse_output_ops(node)

    def for_csv(self, node: Tree):
        self._output_type = 'csv'
        self._parse_output_ops(node)

    def for_markdown(self, node: Tree):
        self._output_type = 'markdown'
        self._parse_output_ops(node)

    def for_template(self, node: Tree):
        self._output_type = 'template'
        i: int = 0
        if isinstance(node.children[i], Token) and node.children[i].type == 'TEMPLATE_TYPE':
            self.output_opts['template_type'] = node.children[i].value.lower()
            i += 1
        self.output_opts['template_file'] = eval_filename_expr(self._dd, node.children[i])
        i += 1
        # remainder are options...
        self._parse_output_ops(node, i)

    def _display_name(self, name: str) -> str:
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
            raise NotImplementedError(f'Output option {repr(name)} of type {self.output_type}')

    def _bool_arg(self, node:Tree, name: str) -> bool:
        return eval_to_bool(self._dd, node.children[0], name, True) if node.children else True

    def _int_arg(self, node:Tree, name: str, default: int=0) -> int:
        return eval_to_int(self._dd, node.children[0], name, True) if node.children else default

    def _str_arg(self, node:Tree, name: str, default: str=None) -> str:
        return eval_to_str(self._dd, node.children[0], name, True) if node.children else default

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
            print(repr(target))
            print(repr(valid_contexts))
            self._valid_contexts = valid_contexts
            return super().transform(tree)
        finally:
            self._target = None
            self._valid_contexts = None

    def var_ref(self, tree):
        first_child = tree.children[0]
        if first_child.value not in self._valid_contexts:
            # Add the target as an implied context for the name
            tree.children.insert(0, Token("NAME", self._target))
        return tree

def get_target(statement: Tree) -> str:
    for child in statement.children:
        if isinstance(child, Token) and child.type == 'TARGET':
            return child.value
    raise TypeError('Select statement did not have a TARGET')

import json # TODO for testing

def execute_select(dd: DataDictionary, statement: Tree):
    target: str = get_target(statement)
    print(f'Target     : {target}')
    # If the user has defined something, or it is one of the pre-loaded
    # prefixes or the target types, then it is a known context and
    # not subject to getting the target prefix added to it
    # TODO should only be applied to the outputs and predicates after analysis?
    statement = ImplicitContextAdder().add_contexts(statement, target, VALID_TARGETS + [*dd.keys()])
    statement = bind_operations(statement)
    if dd.is_debug: print_tree(statement)

    select = SelectAnalyzer(dd, target).analyze(statement)

    # TODO
#    print('Predicates :')
 #   for i, p in enumerate(select.predicates):
  #      print(f'\t{i + 1} : {SSM.source_for(p)}')
    print('Outputs    :')
    for i, o in enumerate(select.output_statements):
        print(f'\t{i + 1} : {SSM.source_for(o)}')
        print_tree(o)
    writer = create_writer(select.output_type, select.output_opts, select.output_controls)
    print_debug(dd, repr(writer))
    # TODO "Load people From "people.json"
    with open('people.json', 'r', encoding='utf-8') as f: data = json.load(f)
    # TODO "Select ... Variable var_name As target"
    QueryFilter(dd, select.output_statements, writer).run_extraction(InMemoryExtractor(data, target))

class DataExtractor(ABC):
    @abstractmethod
    def extract(self, qfilter: "QueryFilter") -> None:
        pass

    def finish(self) -> None:
        """Override if your class requires some type of clean up"""

class DataLimitExceededException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class QueryFilter:
    def __init__(self, dd: DataDictionary, outputs: list, writer: RecordWriter):
        self._dd = dd
        self._outputs = outputs
        self._writer = writer

    def run_extraction(self, extractor: DataExtractor) -> None:
        """
        The writer is started up, and if it can proceede, we turn
        the process, essentially, over to the extractor.
        Here we handle clean up, especial on the receipt of
        a DataLimitExceededException: this is the only place where
        this should be caught.
        """
        if self._writer.start():
            try:
                try:
                    extractor.extract(self)
                except DataLimitExceededException:
                    pass
                finally:
                    self._writer.finish()
            finally:
                extractor.finish()

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
        # we return true or false, which the extractor can check,
        # but it is not prescriptive: False does not mean stop...
        # TODO eval all predicates, if no failures...
        record: list = None
        if self._outputs:
            record = [ eval_expr(self._dd, expr) for expr in self._outputs ]
        else:
            # Result of a "Select From ..." so your output is
            # the entirity of the target data
            record = [ data ]
        if  not self._writer.write(record):
            raise DataLimitExceededException()
        return True

    def set_data(self, key: str, data: Any) -> None:
        """
        Used to set intermediate and target data items in the
        data dictionary prior to any filter call.
        The extractor is responsible for calling unset_data()
        on these items once they go out of scope within their
        data model.
        """
        if data is None:
            self.unset_data(key)
        else:
            if not isinstance(data, dict):
                raise ValueError(f'Data for query must be a dictionary, found {type(data).__name__}')
            self._dd.set_var_user(data, key)

    def unset_data(self, key: str) -> None:
        """
        Used to remove intermediate and target data item
        from the data dictionary.
        See set_data().
        """
        # TODO this is where we need our "unset"
        self._dd.set_var_user(None, key)

class InMemoryExtractor(DataExtractor):
    def __init__(self, source: list, target: str):
        super().__init__()
        if not isinstance(source, list):
            raise ValueError(f'Data for in-memory query must be stored in a list, found {type(source).__name__}')
        self._source = source
        self._target = target

    def extract(self, qfilter: QueryFilter) -> None:
        """
        This is simple because we have a flat data model
        We simply iterate over our data as the target
        additing it to the data dictionary then telling
        the query filter to test is as a target.
        """
        for obj in self._source:
            if obj is not None:
                try:
                    qfilter.set_data(self._target, obj)
                    qfilter.filter_target(obj)
                finally:
                    qfilter.unset_data(self._target)

def create_writer(otype: str, opts: dict, controls: dict) -> RecordWriter:
    """Using the params, create and configure a writer instance.
    otype - the type of writer
    opts - options that configure the writer
    controls - used in wrapper creation and configuration
    """
    writer: RecordWriter = None
    if otype == 'csv':
        writer = CSVRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype == 'json':
        writer = JSONRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype == 'markdown':
        writer = MarkdownRecordWriter(stdout(), stderr=stderr(), **opts)
    elif otype == 'template':
        writer = TemplateRecordWriter(stdout(), stderr=stderr(), **opts)
    else:
        raise NotImplementedError(f'Output type {repr(otype)} not implemented')
    # Order is important since projections can generate more than one row
    # It depends upon how you want to interpret the limit/offset, and that is TBD
    # TODO option on "product" like "before or after limit"
    writer = RecordLimiter.wrap(writer, **controls)
    writer = RecordCartesianProduct.wrap(writer, **controls)
    return writer
