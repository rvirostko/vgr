import sys

_MD_BAR = '|'
_MD_ESC_BAR = '\\|'
_MD_TAB = '\t'
_MD_LF = '\n'
_MD_CR = '\r'

def md_clean_text(value: any) -> str:
    """Strips leading/trailing whitespace, escapes '|', deals with embedded tabs/line breaks"""
    if value is None: return ''
    if not isinstance(value, str): value = str(value)
    value = value.strip()
    if not value: return value
    for c in [_MD_TAB, _MD_CR, _MD_LF]: value = value.replace(c, ' ')
    return value.replace(_MD_BAR, _MD_ESC_BAR)

def md_write_row(row: list[any], file=sys.stdout):
    """Writes a single Markdown table row efficiently."""
    for item in row:
        print(_MD_BAR, end="", file=file)
        print(md_clean_text(item), end="", file=file)
    print(_MD_BAR, file=file)

def md_write_header(headers: list[any], file=sys.stdout):
    """Writes headers and separator"""
    md_write_row(headers, file)
    for _ in headers:  print("|-", end="", file=file)
    print(_MD_BAR, file=file)

def write_table(data, headers, file=sys.stdout):
    """Writes a complete Markdown table with minimal processing."""
    md_write_header(headers, file)
    for row in data: md_write_row(row, file)

# Example Usage
headers = ["name", "age", "pos"]
data = [
    ["Alice", 25, "Engineer"],
    ["Bob", 30, "Doctor"],
    ["Carol", 28, "Data || Analyst"],
    ["Dave", 35, "Data | Engineer"],
    ["Jimbo", 22, "\Hobo"],
    ["Limbo", None, "\Hobo"]
]

write_table(data, headers)
