"""
Contains the implementation for the Create ZIP statement
"""

from typing import Any
import glob
import os
import fnmatch
import zipfile

from lark import Tree

from app_exceptions import VgrRuntimeError
from data_dict import DataDictionary
from evaluate import eval_expr, eval_filename_expr, eval_to_str
from mathpak import bound_ops, type_str
from output import prepare_path, verify_relative_path
from redir import print_stderr

@bound_ops("Create-ZIP")
def execute_zip(dd: DataDictionary, statement: Tree):
    """
**Create a ZIP Archive**

* Create ZIP [File] _expression_ [_option_ [, _option_]...] [;]

Options are

* Include [= | Is] _expression_...
* Exclude [= | Is] _expression_...
* Comment [= | Is] _expression_

Include and exclude expressions are strings that include files or
directories using _glob_ patterns. Both options can specify multiple file
patterns and can be specify multiple times.
Directories are included recursively and include all file in them.

If the include patterns do not match any files, or the exclude patterns
remove all added files, then an empty archive is created.

Both files and directories must be relative to the current directory.

If a comment is specified multiple times, only the last one is used.
"""
    zip_name = eval_filename_expr(dd, statement.children[0])
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    comment: str = None
    for child in statement.children[1:]:
        arg_type = child.data
        if arg_type == 'include': include_patterns.extend(_eval_to_list_str(dd, child, 'Include'))
        elif arg_type == 'exclude': exclude_patterns.extend(_eval_to_list_str(dd, child, 'Exclude'))
        elif arg_type == 'comment': comment = eval_to_str(dd, child.children[0], 'Comment', True)
        else: raise VgrRuntimeError(child, ValueError(f'Unhandled type {repr(arg_type)}'))
    added_files = set()
    # General follow zip's -r behavior when it comes to subdirs
    for pattern in include_patterns:
        for match in glob.glob(pattern, recursive=True):
            abs_match = verify_relative_path(os.path.abspath(match))
            if os.path.isfile(abs_match):
                added_files.add(abs_match)
            elif os.path.isdir(abs_match):
                # Mimic `zip -r`, adding all files under the directory
                for root, _, files in os.walk(abs_match):
                    for file in files: added_files.add(os.path.abspath(os.path.join(root, file)))
    # Use the excluded patterns to filter what was included
    added_files = {
        f for f in added_files if not any(fnmatch.fnmatch(f, pattern) for pattern in exclude_patterns)
    }
    if dd.verbose: print_stderr('Creating', zip_name)
    with zipfile.ZipFile(prepare_path(zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
        if comment: zf.comment = comment.encode('utf-8')
        if added_files:
            for file in sorted(added_files):
                relpath = os.path.relpath(file)
                if dd.verbose: print_stderr('Adding', relpath)
                zf.write(file, relpath)
        else:
            if dd.verbose: print_stderr('Created an empty archive')
        if dd.verbose:
            print_stderr(f'Wrote {os.path.getsize(zip_name):,} bytes')

def _eval_to_list_str(dd: DataDictionary, clause: Tree, name: str) -> list[str]:
    """Helper that returns a list of strings, recursively handling collections"""
    rc = []
    def add_it(expr: Tree, val: Any) -> None:
        if val is not None:
            if isinstance(val, (str, int, float)):
                # Handle ordinals as strings
                rc.append(str(val))
            elif isinstance(val, (list, tuple)):
                # Recurse into collections
                for v in val: add_it(expr, v)
            else:
                # Ignore others if it "isn't anything", but if it is, it's an error
                if val: raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {type_str(rc)}'))
    for expr in clause.children: add_it(expr, eval_expr(dd, expr))
    return rc
