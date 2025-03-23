
from lark import Tree, Token, Transformer, Visitor

from data_dict import DataDictionary
from evaluate import eval_to_int
from src_mgr import SSM

VALID_TARGETS = ['ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role']

class TreeSplitter(Visitor):
    """Used in Select analysis"""
    def __init__(self, dd: DataDictionary):
        super().__init__()
        self._dd = dd
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
        if len(children) >= 1: self._limit = eval_to_int(self._dd, children[0], 'Limit')
        if len(children) >= 2: self._offset = eval_to_int(self._dd, children[1], 'Offset')

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

def execute_select(dd: DataDictionary, statement: Tree):
    ts = TreeSplitter(dd).split(statement)
    # If the user has defined something, or it is one of the pre-loaded
    # prefixes or the target types, then it is a known context and
    # not subject to getting the target prefix added to it
    statement = ImplicitContextAdder().add_contexts(statement, ts.get_target(), VALID_TARGETS + dd.keys())
    ts.split(statement)
    print(f'Target     : {ts.get_target()}')
    print(f'Predicates : {len(ts.get_predicates())}')
    for i, p in enumerate(ts.get_predicates()): print(f'\t{i + 1} : {SSM.source_for(p)}')
    print(f'Outputs    : {len(ts.get_outputs())}')
    for i, o in enumerate(ts.get_outputs()):
        text = SSM.source_for(o)
        label = ts.get_label(o)
        label = '_'.join(text.strip().split()) if label is None else label
        print(f'\t{i + 1} : {text} "{label}"')
    print(f'Limit      : {ts.get_limit()}')
    print(f'Offset     : {ts.get_offset()}')
