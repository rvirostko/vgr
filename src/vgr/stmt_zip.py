"""
Contains the implementation for the Create Zip statement
"""

from re import Pattern
from typing import Any
import glob
import os
import fnmatch
import zipfile

from lark import Tree

from .app_exceptions import VgrRuntimeError
from .builtins import bound_ops, poly_type, verify_relative_path
from .exec_context import ExecContext
from .redir import prepare_path

@bound_ops("Create ZIP")
def execute_zip(ctx: ExecContext, statement: Tree):
    """
**Create a ZIP Archive**

* Create-Zip [File] *zip-file*\\
  &emsp;&emsp;[*option*[, *option*]&hellip;]

Options are

* Include *file_pattern* : file name or *glob* pattern
* Exclude *file_pattern* : file name or *glob* pattern
* Comment [Is] *comment*
* Paths : store files with relative path, which is the default
* Junk Paths : store files with just their name
* `Append` or `Extend` : files added to the end of an existing archive.
  Can be abbreviated as `A`.
* `Overwrite` : overwrite existing archive, which is the default.
  Can be abbreviated as `W`.
* `No Overwrite` : operation fails if the archive already exists.
  Can be abbreviated as `X`.

The *file_pattern* used with `Include` and `Exclude` are strings that select files or
directories using *glob* patterns, not regular expressions. Both options can specify multiple file
patterns using a list and can be used multiple times.

Directories are included recursively and include all file in them.

If the `Include` patterns do not match any files, or the `Exclude` patterns
remove all added files, then an empty archive is created.

Both files and directories must be relative to the current directory.

If `Comment` is specified multiple times, only the last one is used.

```vgr
Create-Zip File "reports.zip"
  Include "out",
  Include ["*.csv", "*.json"],
  Exclude ["*.log", "*.err"],
  Comment "Report created by " + os.login;
```
In the above example, assuming that *out* is a directory,
the first `Include` recursively adds all files in it to the archive list.
CSV and JSON files from the current directory are added with the `Include`.
The `Exclude` option, which can be used in any order, removes files added
by an `Include` that match those given patterns.

> **Windows Note**\\
> If you hard code paths, please use the slash as a universal
> directory separator. Since the backslash is an escape character, if you use
> it in a string, you will either need to double it or use a *raw string*.
"""
    zip_name = ctx.eval_filename_expr(statement.children[0])
    include_patterns: list[str] = []
    exclude_patterns: list[str] = []
    mode = 'w' # mode: w, x, or a
    junk_paths = False
    comment: str = None
    for child in statement.children[1:]:
        arg_type = child.data
        if arg_type == 'include': include_patterns.extend(_eval_to_list_str(ctx, child, 'Include'))   # zip -i/--include
        elif arg_type == 'exclude': exclude_patterns.extend(_eval_to_list_str(ctx, child, 'Exclude')) # zip -x/--exclude
        elif arg_type == 'comment': comment = ctx.eval_to_str(child.children[0], 'Comment', True)     # zip -c/--entry-comments
        elif arg_type == 'junk_paths': junk_paths = True                                              # zip -j/--junk-paths
        elif arg_type == 'keep_paths': junk_paths = False                                             # zip -p/--paths/-p
        elif arg_type in ('a', 'w', 'x'): mode = arg_type
        elif arg_type == 'r': raise VgrRuntimeError(child, ValueError('Invalid mode for writing'))
        else:
            # SNO
            raise VgrRuntimeError(child, ValueError(f'Unhandled type {arg_type!r}')) # pragma no cover
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
    ctx.print_verbose('Creating', zip_name)
    # NB: the path is always for writing, but the file itself may have a
    #    different mode (but never read)
    with zipfile.ZipFile(prepare_path(zip_name, 'w'), mode, zipfile.ZIP_DEFLATED) as zf:
        if comment: zf.comment = comment.encode('utf-8')
        if added_files:
            for file in sorted(added_files):
                relpath = os.path.relpath(file)
                if junk_paths:
                    filename = os.path.split(relpath)[1]
                    ctx.print_verbose('Adding', relpath, 'as', filename)
                    zf.write(file, filename)
                else:
                    ctx.print_verbose('Adding', relpath)
                    zf.write(file, relpath)
        else:
            ctx.print_verbose('Created an empty archive')
        if ctx.verbose: ctx.print_verbose(f'Wrote {os.path.getsize(zip_name):,} bytes')

def _eval_to_list_str(ctx: ExecContext, clause: Tree, name: str) -> list[str]:
    """Helper that returns a list of strings, recursively handling collections"""
    rc = []
    def add_it(expr: Tree, val: Any) -> None:
        if val is not None:
            if isinstance(val, (str, int, float)):
                # Handle ordinals as strings
                rc.append(str(val))
            elif isinstance(val, Pattern):
                rc.append(val.pattern)
            elif isinstance(val, list):
                # Recurse into collections
                for v in val: add_it(expr, v)
            else:
                # Ignore others if it "isn't anything", but if it is, it's an error
                if val: raise VgrRuntimeError(expr, TypeError(f'{name} must be a string; found {poly_type(rc)!r}'))
    for expr in clause.children: add_it(expr, ctx.eval_expr(expr))
    return rc
