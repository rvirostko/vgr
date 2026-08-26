"""
The Sort statement
"""

import copy

from lark import Tree, Visitor

from .app_exceptions import VgrRuntimeError
from .builtins import (
    bound_ops,
    dsort,
    poly_get_keys,
    poly_join,
    poly_repr,
    poly_sort,
    poly_type,
)

from .encoding import parse_encoding
from .evaluate import bind_operations, do_set
from .exec_context import ExecContext
from .output import CSVRecordWriter, JSONRecordWriter, TextRecordWriter
from .stmt_set import load_file_as, load_data_type

_TYPE = 'type'         # will be _VAR or _FILE
_VAR = 'var'           # read from/write to a varialbe
_FILE = 'file'         # read from/write to a file
_DTYPE = 'dtype'       # data type for file (CSV, JSON, et al)
_ENCODING = 'encoding' # encoding used by file
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
        # TODO what does this mean? Actionable or just an NB?
        # if input is text
        #   if we don't have any cols, add [row/asc]
        #   else we prune to 1, we'll use that as the "name" if we write to CSV/JSON

    def source(self, node: Tree):
        """
        ...File "data.json"...
        ...File "data.csv" Type CSV...
        ...my_var...
        """
        self._store_io(node.children[0], self._source)

    def target(self, node: Tree):
        """
        ...Giving File "data.json"...
        ...Giving File "data.csv" Type CSV...
        ...Giving my_var...
        """
        self._store_io(node.children[0], self._target)

    def key(self, node: Tree):
        """
        ...On Key id_num...
        ...On Ascending Key id_num...
        ...On Descending Key id_num...
        """
        self._source[_SORT_COLS].append(self._get_key("Sort key", node.children[-1]))
        self._source[_SORT_FLAGS].append(node.children[0].data == 'sort_asc' if len(node.children) == 2 else True)

    def unique(self, node: Tree):
        """
        ...Unique...
        ...Unique On last_name, first_name...
        """
        self._target[_UNIQUE] = True
        if len(node.children) > 0:
            self._target[_UNIQUE_COLS] = [self._get_key("Uniqueness key", child) for child in node.children]

    def _get_key(self, name: str, arg) -> str:
        """
        **Reads in a key name**

        The key can be a simple unquoted name _if_ it is undefined in the data dictionary.
        The key can be an expression, in which case it must be a number or a string.
        """
        rc = self.ctx.eval_expr_or_const(arg)
        if rc is None or isinstance(rc, (str, int, float)): return rc
        raise VgrRuntimeError(arg, TypeError(f'{name} must be a number or string; found {poly_type(rc)!r}'))

    def _store_io(self, node: Tree, io: dict) -> None:
        """
        ...File "data.json"...
        ...File "data.csv" Type Is CSV [Encoding Is "Ascii"]...
        ...my_var...
        """
        iotype = node.data
        if iotype == _FILE:
            io[_TYPE] = iotype
            io[iotype] = self.ctx.eval_filename_expr(bind_operations(node.children[0]))
            ftype = None
            for child in node.children[1:]:
                name = child.data.lower()
                if name == "encoding":
                    io[_ENCODING] = parse_encoding(self._ctx, bind_operations(child))
                else:
                    ftype = name
            io[_DTYPE] = load_data_type(io[iotype], ftype)
        elif iotype == _VAR:
            io[_TYPE] = iotype
            # Extract the path (which seems risky...)
            io[iotype] = list(name.value for name in node.children[0].children)
        else:
            # SNO
            raise VgrRuntimeError(node, NotImplementedError('Sort type not implemented')) # pragma no cover

@bound_ops("Sort")
def execute_sort(ctx: ExecContext, statement: Tree) -> None:
    """
**Sort the contents of a list or a file**

* Sort *variable* *keys* [*unique*] [*target*]
* Sort File *file_name* [*file_type*] *keys* [*unique*] [*target*]

**The *keys* option**

* &hellip; [On | By] *key_spec*[, *key_spec* &hellip;] &hellip;
* *key_spec* : [Ascending | Descending] [Key] *expression*
* Ascending and Descending may be abbreviated as Asc or Des
* Ascending is the default ordering
* When sorting non-dictionary items, no keys are required.
  The only available key is *line*.

**The *unique* option**

* &hellip; Unique &hellip;
* &hellip; Unique On *expression*[, *expression* &hellip;] &hellip;
* Without a list of keys, uniqueness performed on keys used to perform the sort
* When sorting non-dictionary items, no keys are required.
  The only available key is *line*.

**The *target* option**

* &hellip; Giving *variable* &hellip;
* &hellip; Giving File *file_name* &hellip;
* &hellip; Giving File *file_name* [*file_type*] &hellip;
* If omitted, sort is performed in-place

**The *file_type* option**

* &hellip; Type [Is] *file_type* [Encoding [Is] *encoding*] &hellip;
* *file_type* is one of:\\
  &emsp;JSON or JSON Object (an array of objects)\\
  &emsp;JSON Object Per Line (each line is an object)\\
  &emsp;CSV (CSV data)\\
  &emsp;Text Lines (each item a line of text)\\
  &emsp;Text (entire object as text)
* If no file type is given it is determined from *file_name*'s extension
* *encoding* is a valid file type encoding with *UTF-8* as the default

```vgr
# Sort the contents of a variable and write to a file
Sort persons On Key fname, lname Giving File "persons.sorted" Type Is JSON

# Sort a CSV file in place
Sort File export + ".dat" Type Is CSV On Asc Key id, Des env

# Sort with unique
Sort accts On acct_nbr Unique
```

Also see `Sort()` and `Unique()`

"""
    sort = SortAnalyzer(ctx).analyze(statement)
    source = sort.sort_source
    target = sort.sort_target
    data = _read_data(ctx, source)
    # At this point, we write out everything; no per col filtering
    target[_FIELDS] = source[_FIELDS]
    if ctx.verbose:
        ctx.print_verbose("Sort Source =", poly_repr(source))
        ctx.print_verbose("Sort Target =", poly_repr(target))
    data = _do_sort(ctx, data, source, target)
    _write_data(ctx, data, target, source.get(_ENCODING, None))

def _do_sort(_ctx: ExecContext, data: list, source: dict, target: dict) -> list:
    if source[_DTYPE] == 'text_file':
        sort_flags = source[_SORT_FLAGS]
        data = poly_sort(data, target[_UNIQUE], len(sort_flags) != 0 and not any(sort_flags))
    else:
        unique_cols = target[_UNIQUE_COLS]
        unique_cols = target[_FIELDS] if len(unique_cols) == 0 else unique_cols
        data = dsort(data, source[_SORT_COLS], source[_SORT_FLAGS], target[_UNIQUE], unique_cols)
    return data

def _read_data(ctx: ExecContext, source: dict) -> list:
    if source[_TYPE] == _VAR:
        data = ctx.get_var(*source[_VAR])
        if not source[_IN_PLACE]:
            data = copy.deepcopy(data)
        # Make sure we have something iterable
        data = data if isinstance(data, list) else [] if data is None else [data]
        # Guess at a data type
        source[_DTYPE] = 'text_file' if len(data) == 0 or not isinstance(data[0], dict) else 'json_object'
        if source[_DTYPE] == 'text_file':
            # text files only have one "column" which we call "line"
            # no matter what was used with "on"
            sort_cols = source[_SORT_COLS]
            if len(sort_cols) > 1 and ctx.verbose:
                ctx.print_verbose('Extraneous Sort ordering ignored:', poly_repr(sort_cols[1:]))
            source[_FIELDS] = source[_SORT_COLS] = ['line']
        else:
            # Get all the keys from the data
            source[_FIELDS] = sorted(poly_get_keys(data))
    else:
        try:
            filename = source[_FILE]
            with open(filename, 'r', encoding=source.get(_ENCODING, 'utf-8-sig'), errors='backslashreplace' if ctx.debug else 'replace') as f:
                data, metadata = load_file_as(filename, f, source[_DTYPE])
            source[_FIELDS] = metadata['keys']
            data = data if isinstance(data, list) else [] if data is None else [data]
        except Exception as e:
            raise ValueError(f'While reading {source[_FILE]!r}: {str(e)}') from e
    # The sort keys must be in the input's fields
    _validate_subset(source[_SORT_COLS], source[_FIELDS])
    # We put our sort fields in the first columns of output when working with columnar data
    source[_FIELDS] = _append_unique(source[_SORT_COLS], source[_FIELDS])
    return data

def _write_data(ctx: ExecContext, data: list, target: dict, input_encoding: str) -> None:
    if target[_TYPE] == 'var':
        # Very simple, just store it
        do_set(ctx, data, *target[_VAR])
        return
    # The user can either change the encoding or we can use the input's or default to UTF-8
    encoding = target.get(_ENCODING, input_encoding or 'utf-8') # NB: We down write BOMs by default
    with open(target[_FILE], 'w', encoding=encoding, errors='backslashreplace' if ctx.debug else 'replace') as f:
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
        raise ValueError(f'Sort: {dtype!r} not supported for writing')

def _append_unique(x: list, y: list) -> list:
    return x + [x1 for x1 in y if x1 not in x]

def _validate_subset(sort_keys: list, filed_names: list) -> list:
    missing = [x for x in sort_keys if x not in filed_names]
    if missing:
        raise ValueError(f'Unknown Keys referenced in Sort: {poly_join(poly_repr(*missing), ", ")}')
    return sort_keys
