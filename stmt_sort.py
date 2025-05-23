"""
The Sort statement, based on Cobol with uniqueness extension.
"""

import copy

from lark import Tree, Visitor

from data_dict import DataDictionary
from dd_config import do_set
from evaluate import eval_filename_expr, bind_operations
from mathpak import poly_sort, dsort
from output import CSVRecordWriter, JSONRecordWriter, TextRecordWriter
from redir import print_stderr
from stmt_set import load_file_as, load_data_type

_TYPE = 'type'
_VAR = 'var'
_FILE = 'file'
_DTYPE = 'dtype'
_FIELDS = 'fields'
_SORT_COLS = 'sort_cols'
_SORT_FLAGS = 'sort_flags'
_IN_PLACE = 'in_place'
_UNIQUE = 'unique'
_UNIQUE_COLS = 'unique_cols'

class SortAnalyzer(Visitor):
    def __init__(self, dd: DataDictionary):
        super().__init__()
        self._dd = dd
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
    def dd(self) -> DataDictionary:
        return self._dd

    @property
    def sort_source(self) -> dict:
        return self._source

    @property
    def sort_target(self) -> dict:
        return self._target

    def sort(self, _: Tree):
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
        self._source[_SORT_COLS].append(node.children[-1].value)
        self._source[_SORT_FLAGS].append(node.children[0].data == 'sort_asc' if len(node.children) == 2 else True)

    def unique(self, node: Tree):
        """
        ...unique...
        ...unique on last_name, first_name...
        """
        self._target[_UNIQUE] = True
        if len(node.children) > 0:
            self._target[_UNIQUE_COLS] = [name.value for name in node.children]

    def _ref_to_name(self, var_ref: Tree) -> str:
        return '.'.join(name.value for name in var_ref.children)

    def _store_io(self, node: Tree, io: dict) -> None:
        """
        ...file "data.json"...
        ...file "data.csv" as csv...
        ...var my_var...
        """
        io[_TYPE] = node.data
        if node.data == 'file':
            io[_FILE] = eval_filename_expr(self._dd, bind_operations(node.children[0]))
            io[_DTYPE] = load_data_type(io[_FILE], node.children[1] if len(node.children) == 2 else None)
        elif node.data == 'var':
            io[_VAR] = tuple(name.value for name in node.children[0].children)
        else:
            raise NotImplementedError(f'Sort source/target {repr(node.data)} not implemented') # SNO

def execute_sort(dd: DataDictionary, statement: Tree) -> None:
    sort = SortAnalyzer(dd).analyze(statement)
    source = sort.sort_source
    target = sort.sort_target
    data = _read_data(dd, source)
    # At this point, we write out everything; no per col filtering
    target[_FIELDS] = source[_FIELDS]
    if dd.debug:
        print_stderr("Sort Source =", repr(source))
        print_stderr("Sort Target =", repr(target))
    data = _do_sort(dd, data, source, target)
    _write_data(dd, data, target)

def _do_sort(_: DataDictionary, data: list, source: dict, target: dict) -> list:
    if source[_DTYPE] == 'text_file':
        sort_flags = source[_SORT_FLAGS]
        data = poly_sort(data, target[_UNIQUE], len(sort_flags) == 0 or any(sort_flags))
    else:
        unique_cols = target[_UNIQUE_COLS]
        unique_cols = target[_FIELDS] if len(unique_cols) == 0 else unique_cols
        data = dsort(data, source[_SORT_COLS], source[_SORT_FLAGS], target[_UNIQUE], unique_cols)
    return data

def _read_data(dd: DataDictionary, source: dict) -> list:
    if source[_TYPE] == 'var':
        data = dd.get_var(*source[_VAR])
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
            if len(sort_cols) > 1:
                if dd.verbose: print_stderr(f'Extraneous Sort ordering ignored: {repr(sort_cols[1:])}')
            source[_FIELDS] = source[_SORT_COLS] = ['line']
        else:
            source[_FIELDS] = sorted(data[0].keys())
    else:
        # TODO encoding
        # defaults to utf-8-sig
        with open(source[_FILE], 'r', encoding='utf-8-sig') as f:
            data, fields = load_file_as(f, source[_DTYPE])
        source[_FIELDS] = fields
        data = data if isinstance(data, (list, tuple)) else [] if data is None else [data]
    # The "on" keys must all be known in our fields
    _validate_subset(source[_SORT_COLS], source[_FIELDS])
    # We put our sort fields in the first cols of output
    source[_FIELDS] = _append_unique(source[_SORT_COLS], source[_FIELDS])
    return data

def _write_data(dd: DataDictionary, data: list, target: dict) -> None:
    if target[_TYPE] == 'var':
        # Very simple, just store it
        do_set(dd, data, *target[_VAR])
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
        raise ValueError(f'Unknown file content type {repr(dtype)}') # SNO

def _append_unique(x: list, y: list) -> list:
    return x + [x1 for x1 in y if x1 not in x]

def _validate_subset(sort_keys: list, filed_names: list) -> list:
    missing = [x for x in sort_keys if x not in filed_names]
    if missing:
        raise ValueError(f'Unknown Keys referenced in Sort: {", ".join(missing)}')
    return sort_keys
