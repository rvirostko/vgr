
from lark import Tree, Token, Transformer, Visitor

from data_dict import DataDictionary
from evaluate import eval_to_bool, eval_to_int, eval_to_str, eval_filename_expr
from src_mgr import SSM
from dbg import print_tree

VALID_TARGETS = ['ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role']

class SelectAnalyzer(Visitor):

    _BOOL_OPTS = (
        'array_wrapper',
        'auto_escape',
        'compact',
        'debug',
        'include_nulls',
        'omit_headers',
        'sort_keys',
    )

    _NEG_BOOL_OPTS = {
        # The option to what it negates
        'exclude_nulls'   : 'include_nulls',
        'include_headers' : 'omit_headers',
        'no_array_wrapper': 'array_wrapper',
    }

    _STR_OPTS = (
        'delimiter',
        'escapechar',
        'lineterminator',
        'quotechar',
    )

    _OPT_DISPLAY_NAME = {
        # I not present, we just capitalize it
        'array_wrapper'    : 'Array Wrapper',
        'auto_escape'      : 'Auto Escape',
        'escapechar'       : 'Escape Character',
        'exclude_nulls'    : 'Exclude Nulls',
        'include_headers'  : 'Include Headers',
        'include_nulls'    : 'Include Nulls',
        'lineterminator'   : 'Line Terminator',
        'no_array_wrapper' : 'No Array Wrapper',
        'omit_headers'     : 'Omit Headers',
        'quotechar'        : 'Quote Character',
        'sort_keys'        : 'Sort Keys',
    }

    """Used in Select analysis"""
    def __init__(self, dd: DataDictionary):
        super().__init__()
        self._dd = dd
        self._predicates = []
        self._outputs = []
        self._labels = []
        self._output_controls = {}
        self._output_type = None
        self._output_ops = {}

    def split(self, tree: Tree):
        self.visit(tree)
        return self

    @property
    def output_type(self) -> str:
        return self._output_type or 'json'

    @property
    def output_opts(self) -> dict:
        return self._output_ops

    # TODO make properties

    def get_outputs(self) -> list:
        return self._outputs

    def get_label(self, output) -> str:
        # TODO why this way? should we not get all the labels at once?
        # if it is an output_as, it will have two children
        # the second child will be either a NAME or a STRING, but all we need
        # is its value regardless of type
        return output.children[1].value if len(output.children) > 1 else None

    @property
    def predicates(self) -> list:
        return self._predicates if self._predicates else []

    @property
    def output_controls(self) -> dict:
        return self._output_controls

    #----

    # TODO add repr

    #--- visitor methods
    def select(self, node: Tree):
        """
        Just recode the target
        Everything else should have been handled by other visitors
        """
        # TODO should we build things like labels and other defaults here?

    def output(self, node: Tree):
        self._outputs.append(node)

    def output_as(self, node: Tree):
        self.output(node)

    def where_clause(self, node: Tree):
        self._predicates.extend(node.children)

    def limit_clause(self, node: Tree):
        children = node.children
        if len(children) >= 1: self._output_controls['limit'] = eval_to_int(self._dd, children[0], 'Limit')
        if len(children) >= 2: self._output_controls['offset'] = eval_to_int(self._dd, children[1], 'Offset')

    def product_clause(self, node: Tree):
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
        i: int = 0;
        if isinstance(node.children[i], Token):
            self._output_ops['template_type'] = node.children[i].value.lower()
            i += 1
        self._output_ops['template_file'] = eval_filename_expr(self._dd, node.children[i])
        i += 1
        # remainder are options...
        self._parse_output_ops(node, i)

    def _display_name(self, name: str) -> str:
        return self._OPT_DISPLAY_NAME.get(name, name.capitalize())

    def _parse_output_ops(self, node:Tree, start: int=0) -> None:
        """This is a unified set of options"""
        for c in node.children[start:]:
            name: str = c.data
            if name in self._BOOL_OPTS:
                self._output_ops[name] = self._bool_arg(c, self._display_name(name))
                continue
            if name in self._NEG_BOOL_OPTS:
                self._output_ops[self._NEG_BOOL_OPTS[name]] = not self._bool_arg(c, self._display_name(name))
                continue
            if name in self._STR_OPTS:
                self._output_ops[name] = self._str_arg(c, self._display_name(name))
                continue
            # Now the special cases
            if name == 'encode_ascii':
                self._output_ops[name] = self._bool_arg(c, 'Encode ASCII')
                self._output_ops.pop('encode_unicode', None)
                continue
            if name == 'encode_unicode':
                self._output_ops[name] = self._bool_arg(c, 'Encode Unicode')
                self._output_ops.pop('encode_ascii', None)
                continue
            if name == 'root':
                self._output_ops[name] = self._str_arg(c, 'Root', 'result')
                continue
            if name == 'indent':
                self._output_ops[name] = self._int_arg(c, 'Indent', 2)
                continue
            if name == 'quoting':
                self._output_ops[name] = c.children[0].value.lower()
                continue
            raise NotImplementedError(f'Output option {repr(name)} of type {self.output_type}')

    def _bool_arg(self, node:Tree, name: str) -> bool:
        return eval_to_bool(self._dd, node.children[0], name) if node.children else True

    def _int_arg(self, node:Tree, name: str, default: int=0) -> int:
        return eval_to_int(self._dd, node.children[0], name) if node.children else default

    def _str_arg(self, node:Tree, name: str, default: str=None) -> str:
        return eval_to_str(self._dd, node.children[0], name) if node.children else default

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

    def var_ref(self, children):
        first_child = children[0]
        if first_child.value not in self._valid_contexts:
            # Add the target as an implied context for the name
            children.insert(0, Token("NAME", self._target))
            # TODO , first_child.start_pos, first_child.line, first_child.column,
            # first_child.end_line, first_child.end_column, first_child.end_pos))
        return Tree("var_ref", children)

def get_target(statement: Tree) -> str:
    for child in statement.children:
        if isinstance(child, Token) and child.type == 'TARGET':
            return child.value
    raise TypeError('Select statement did not have a TARGET')

def execute_select(dd: DataDictionary, statement: Tree):
    target: str = get_target(statement)
    # If the user has defined something, or it is one of the pre-loaded
    # prefixes or the target types, then it is a known context and
    # not subject to getting the target prefix added to it
    statement = ImplicitContextAdder().add_contexts(statement, target, VALID_TARGETS + [*dd.keys()])
    print_tree(statement) # TODO
    select = SelectAnalyzer(dd).split(statement)
    print(f'Target     : {target}')
    print(f'Predicates : {len(select.predicates)}')
    for i, p in enumerate(select.predicates): print(f'\t{i + 1} : {SSM.source_for(p)}')
    print(f'Outputs    : {len(select.get_outputs())}')
    for i, o in enumerate(select.get_outputs()):
        text = SSM.source_for(o)
        label = select.get_label(o)
        label = '_'.join(text.strip().split()) if label is None else label
        print(f'\t{i + 1} : {text} "{label}"')
    print(f'Output Ctrl: {repr(select.output_controls)}')
    print(f'Output As : {repr(select.output_type)}')
    print(f'Output Opt: {repr(select.output_opts)}')
