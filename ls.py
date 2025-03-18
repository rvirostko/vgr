#! /usr/bin/env python3

import sys
import pwd
import grp
from pathlib import Path
from datetime import datetime
from stat import filemode

def list_files(path=".", long_format=False, human_readable=False, recursive=False, all_files=False):
    orig_path = path
    path = Path(path).expanduser().resolve()
    if not path.exists():
        print(f"ls: cannot access '{path}': No such file or directory", file=sys.stderr)
    else:
        _list_files(path, orig_path, long_format, human_readable, recursive, all_files)

def _list_files(path, orig_path, long_format=False, human_readable=False, recursive=False, all_files=False):
    entries = sorted(get_items(path), key=unix_ls_sort_key)
    if not all_files: entries = [e for e in entries if not e.name.startswith(".")]
    size_width = max((len(str(e.stat().st_size)) for e in entries), default=0) if long_format else 0

    def format_entry(e):
        if long_format:
            stat = e.stat()
            size = human_readable_size(stat.st_size) if human_readable else f"{stat.st_size:>{size_width}}"
            return f"{filemode(stat.st_mode)} {pwd.getpwuid(stat.st_uid).pw_name} {grp.getgrgid(stat.st_gid).gr_name} {size} {format_date(datetime.fromtimestamp(stat.st_mtime))} {e.name}"
        return e.name

    if recursive:
        for f in [e for e in entries if e.is_file()]:
            print(format_entry(f))
        for d in [e for e in entries if e.is_dir()]:
            if recursive:
                # TODO wrong : needs to be relative to orig_path (or not...)
                print(f"\n{d}:")
                _list_files(d, orig_path, long_format, human_readable, recursive, all_files)
    else:
        for entry in entries: print(format_entry(entry))

def get_items(path: str):
    path = Path(path).expanduser().resolve()
    return [path] if path.is_file() else path.iterdir()

def format_date(date: datetime) -> str:
    now = datetime.now()
    # If the date is within the last year, show Month, Day, Time
    if (now - date).days < 365:
        return date.strftime("%b %d %H:%M")
    else:
        return date.strftime("%b %d  %Y")

def unix_ls_sort_key(p):
    """Sorts with uppercase letters before lowercase in file/directory names."""
    name = p.name
    return [(c.islower(), c) for c in name]

def human_readable_size(size, decimal_places=1):
    for unit in ['B', 'K', 'M', 'G', 'T']:
        if size < 1024.0: return f"{size:.{decimal_places}f}{unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f}P"
