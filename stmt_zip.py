"""
Contains the implementation for the CREATE ZIP statement
"""

import glob
import os
import fnmatch
import zipfile

from lark import Tree

from data_dict import DataDictionary
from evaluate import eval_filename_expr, eval_to_str, eval_to_list_str
from redir import print_verbose
from output import prepare_path, verify_relative_path

def execute_zip(dd: DataDictionary, statement: Tree):
    """Create a ZIP Archive

* CREATE ZIP [FILE] _expression_ [_option_ [, _option_]...]

Options are

* INCLUDE _expression_...
* EXCLUDE _expression_...
* COMMENT _expression_
* PASSWORD _expression_

Include and exclude expressions are strings that include files or
directories. Directories are included recursively. Files and directories must
be relative to the current directory.

_Password is not currently implemented but may be specified_

"""
    zip_name = eval_filename_expr(dd, statement.children.pop(0))
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    comment: str = None
    password: str = None
    for child in statement.children:
        arg_type = child.data
        if arg_type == 'include': include_patterns.extend(eval_to_list_str(dd, child, 'Include'))
        elif arg_type == 'exclude': exclude_patterns.extend(eval_to_list_str(dd, child, 'Exclude'))
        elif arg_type == 'comment': comment = eval_to_str(dd, child.children[0], 'Comment', True)
        elif arg_type == 'password': password = eval_to_str(dd, child.children[0], 'Password', True)
        else: raise ValueError(f'Unhandled type {repr(arg_type)}')
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
    print_verbose(dd, 'Creating', zip_name)
    with zipfile.ZipFile(prepare_path(zip_name), 'w', zipfile.ZIP_DEFLATED) as zf:
        # TODO this is only used for reading, so we need to switch libraries
        if password: zf.setpassword(password.encode())
        if comment: zf.comment = comment.encode('utf-8')
        if added_files:
            for file in sorted(added_files):
                relpath = os.path.relpath(file)
                print_verbose(dd, 'Adding', relpath)
                zf.write(file, relpath)
        else:
            print_verbose(dd, 'Created an empty archive')
