"""
The Sort statement, based on Cobol with uniqueness extension.
"""

import copy

from lark import Tree, Visitor

from app_exceptions import VgrRuntimeError
from data_dict import DataDictionary
from evaluate import bind_operations, do_set
from exec_context import ExecContext
from mathpak import poly_sort, dsort, bound_ops, type_str
from output import CSVRecordWriter, JSONRecordWriter, TextRecordWriter
from stmt_set import load_file_as, load_data_type

_TYPE = 'type'     # will be _VAR or _FILE
_VAR = 'var'       # read from/write to a varialbe
_FILE = 'file'     # read from/write to a file
_DTYPE = 'dtype'   # data type (CSV, JSON, et al)
_FIELDS = 'fields'
_SORT_COLS = 'sort_cols'     # list of columns used in sorting
_SORT_FLAGS = 'sort_flags'   # matching list of sort order bools (T -> asc)
_IN_PLACE = 'in_place'       # boolean
_UNIQUE = 'unique'           # boolean
_UNIQUE_COLS = 'unique_cols' # columns that determine uniqueness

class SortAnalyzer(Visitor):
    def __init__(self, ctx: ExecContext):
        super().__init__()
        self._ctx = ctx
        self._source = {
            _SORT_COLS: [],
            _SORT_FLAGS: [],
            _IN_PLACE: False,
        }
        self._target = {
            _UNIQUE: False,
            _UNIQUE_COLS: [],
        }

    def analyze(self, tree: Tree):
        self.visit(tree)
        return self

    @property
    def ctx(self) -> ExecContext:
        return self._ctx

    @property
    def sort_source(self) -> dict:
        return self._source

    @property
    def sort_target(self) -> dict:
        return self._target

    def sort(self, _: Tree):
        # If no target was specified, this is an in-place sort
        # Copy over relevant attrs from _source to _target
        if _TYPE not in self._target:
            self._source[_IN_PLACE] = True
            for a in [_TYPE, _VAR, _FILE, _DTYPE]:
                if a in self._source: self._target[a] = self._source[a]
        # if input is text
        #   if we don't have any cols, add [row/asc]
        #   else we prune to 1, we'll use that as the "name" if we write to CSV/JSON

    def source(self, node: Tree):
        """
        ...file "data.json"...
        ...file "data.csv" as csv...
        ...var my_in...
        """
        self._store_io(node.children[0], self._source)

    def target(self, node: Tree):
        """
        ...giving file "data.json"...
        ...giving file "data.csv" as csv...
        ...into var my_out...
        """
        self._store_io(node.children[0], self._target)

    def key(self, node: Tree):
        """
        ...on key id_num...
        ...on ascending key id_num...
        ...on descending key id_num...
        """
        self._source[_SORT_COLS].append(self._get_key("Sort key", node.children[-1]))
        self._source[_SORT_FLAGS].append(node.children[0].data == 'sort_asc' if len(node.children) == 2 else True)

    def unique(self, node: Tree):
        """
        ...unique...
        ...unique on last_name, first_name...
        """
        self._target[_UNIQUE] = True
        if len(node.children) > 0:
            self._target[_UNIQUE_COLS] = [self._get_key("Uniqueness key", child) for child in node.children]

    def _get_key(self, name: str, arg) -> str:
        """
        **Reads in a key name**

        The key can be a simple unquoted name _if_ it is undefined in the data dictionary.
        The key can be an expression, in which case it must be a string.
        While underlying code also supports a variable reference, the grammar does not support this.
        """
        rc = self.ctx.eval_expr_or_const(arg)
        if rc is None or isinstance(rc, (str, int, float)): return rc
        raise VgrRuntimeError(arg, TypeError(f'{name} must be a simple type; found {type_str(rc)}'))

    def _store_io(self, node: Tree, io: dict) -> None:
        """
        ...file "data.json"...
        ...file "data.csv" as csv...
        ...var my_var...
        """
        io[_TYPE] = node.data
        if node.data == 'file':
            io[_FILE] = self.ctx.eval_filename_expr(bind_operations(node.children[0]))
            io[_DTYPE] = load_data_type(io[_FILE], node.children[1] if len(node.children) == 2 else None)
        elif node.data == 'var':
            io[_VAR] = tuple(name.value for name in node.children[0].children)
        else:
            raise NotImplementedError(f'Sort source/target {node.data!r} not implemented') # SNO

@bound_ops("Sort")
def execute_sort(ctx: ExecContext, statement: Tree) -> None:
    """
**Sort the contents of a list or a file**

* Sort [Variable | Var] _variable_ _keys_ [_unique_] [_target_] [;]
* Sort File _file_name_ [_file_type_] _keys_ [_unique_] [_target_] [;]

The _keys_ option
* ... [On | By] _key_spec_ [, _key_spec_ ...] ...
* _key_spec_ : [Ascending | Descending] [Key] _expression_
* Ascending and Descending may be abbreviated as Asc or Des
* Ascending is the default ordering
* When sorting non-dictionary items, no keys are required.
  The only available key is _line_.

The _unique_ option
* ... Unique ...
* ... Unique On _expression_ [, _expression ...] ...
* Without a list of keys, uniqueness performed on keys used to perform the sort
* When sorting non-dictionary items, no keys are required.
  The only available key is _line_.

The _target_ option
* ... [Into | Giving] [Variable | Var] _variable_ ...
* ... [Into | Giving] File _file_name_ ...
* ... [Into | Giving] File _file_name_ [_file_type_] ...
* If omitted, sort is performed in-place

The _file_type_ option
* ... As _type_ ... where _type_ is : JSON or JSON Object (an array of objects),
    JSON Object Per Line (each line is an object),
    CSV (CSV data),
    Text Lines (each item a line of text) or
    Text (entire object as text)
* If no file type is given it is guessed from the extension

**Examples**

```
# Sort the contents of a variable and write to a file
Sort persons On Key fname, lname Into File "persons.sorted" As Json

# Sort a CSV file in place
Sort File export + ".dat" As CSV On Asc Key id, Des env

# Sort/unique
Sort accts On acct_nbr Unique
```

"""
    sort = SortAnalyzer(ctx).analyze(statement)
    source = sort.sort_source
    target = sort.sort_target
    data = _read_data(ctx, source)
    # At this point, we write out everything; no per col filtering
    target[_FIELDS] = source[_FIELDS]
    if ctx.verbose:
        ctx.print_verbose("Sort Source =", repr(source))
        ctx.print_verbose("Sort Target =", repr(target))
    data = _do_sort(ctx.dd, data, source, target)
    _write_data(ctx, data, target)

def _do_sort(_: DataDictionary, data: list, source: dict, target: dict) -> list:
    if source[_DTYPE] == 'text_file':
        sort_flags = source[_SORT_FLAGS]
        data = poly_sort(data, target[_UNIQUE], len(sort_flags) != 0 and not any(sort_flags))
    else:
        unique_cols = target[_UNIQUE_COLS]
        unique_cols = target[_FIELDS] if len(unique_cols) == 0 else unique_cols
        data = dsort(data, source[_SORT_COLS], source[_SORT_FLAGS], target[_UNIQUE], unique_cols)
    return data

def _read_data(ctx: ExecContext, source: dict) -> list:
    if source[_TYPE] == 'var':
        data = ctx.get_var(*source[_VAR])
        if not source[_IN_PLACE]:
            data = copy.deepcopy(data)
        # Make sure we have something iterable
        data = data if isinstance(data, (list, tuple)) else [] if data is None else [data]
        # Guess at a data type
        source[_DTYPE] = 'text_file' if len(data) == 0 or not isinstance(data[0], dict) else 'json_object'
        if source[_DTYPE] == 'text_file':
            # text files only have one "column" which we call "line"
            # no matter what was used with "on"
            sort_cols = source[_SORT_COLS]
            if len(sort_cols) > 1 and ctx.verbose:
                ctx.print_verbose('Extraneous Sort ordering ignored:', repr(sort_cols[1:]))
            source[_FIELDS] = source[_SORT_COLS] = ['line']
        else:
            # while unlikely (maybe?) we need to support non-string ordinals as keys
            source[_FIELDS] = sorted(data[0].keys(), key=lambda x: '' if x is None else str(x))
    else:
        # TODO encoding
        # defaults to utf-8-sig
        try:
            with open(source[_FILE], 'r', encoding='utf-8-sig') as f:
                data, fields = load_file_as(f, source[_DTYPE])
            source[_FIELDS] = fields
            data = data if isinstance(data, (list, tuple)) else [] if data is None else [data]
        except Exception as e:
            raise ValueError(f'While reading {source[_FILE]!r}: {str(e)}') from e
    # The "on" keys must all be known in our fields
    _validate_subset(source[_SORT_COLS], source[_FIELDS])
    # We put our sort fields in the first cols of output
    source[_FIELDS] = _append_unique(source[_SORT_COLS], source[_FIELDS])
    return data

def _write_data(ctx: ExecContext, data: list, target: dict) -> None:
    if target[_TYPE] == 'var':
        # Very simple, just store it
        do_set(ctx, data, *target[_VAR])
        return
    # TODO encoding option
    with open(target[_FILE], 'w', encoding='utf-8-sig') as f:
        # build a writer and send the data to it
        dtype = target[_DTYPE]
        headers = target[_FIELDS]
        if dtype == 'text_file':
            rw = TextRecordWriter(f, headers=headers)
            rw.start()
            for row in data:
                rw.write([row.get(p, None) for p in headers] if isinstance(row, dict) else [row])
            rw.finish()
            return
        if dtype in ('json_object', 'json_objects'):
            rw = JSONRecordWriter(f, headers=headers, array_wrapper=dtype=='json_object')
            rw.start()
            for row in data:
                rw.write([row])
            rw.finish()
            return
        if dtype == 'csv_file':
            rw = CSVRecordWriter(f, headers=headers, quoting='minimal')
            rw.start()
            for row in data:
                rw.write([row.get(p, None) for p in headers] if isinstance(row, dict) else [row])
            rw.finish()
            return
        raise ValueError(f'Unknown file content type {dtype!r}') # SNO

def _append_unique(x: list, y: list) -> list:
    return x + [x1 for x1 in y if x1 not in x]

def _validate_subset(sort_keys: list, filed_names: list) -> list:
    missing = [x for x in sort_keys if x not in filed_names]
    if missing:
        raise ValueError(f'Unknown Keys referenced in Sort: {", ".join(missing)}')
    return sort_keys
