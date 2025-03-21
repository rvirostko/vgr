import mistune
#from mistune.renderers import BaseRenderer
from blessed import Terminal

term = Terminal()

class AnsiRenderer(mistune.Markdown):
    def foo(self):
        return

#    def text(self, text):
#        return text

#    def blank_line(self, token, state, **attrs):
#        #self.render_tokens(token.children, state)# .render_children(token, state)
#        print(repr(token))
#        return "\n"

##    def paragraph(self, token, level, **attrs):
#        print(repr(token))
#        return "\n"

#    def list(self, token, level, **attrs):
#        print(repr(token))
#        return "list\n"

#    def block_quote(self, text, level, **attrs):
#        return "quote\n"

#    def heading(self, text, level, **attrs):
#        #return f"{term.bold}{term.color(level + 1)}{'#' * level} {text}{term.normal}\n"
#        return f"{term.bold}{text}{term.normal}\n"

#    def emphasis(self, text, **attrs):
#        return f"{term.italic}{text}{term.normal}"

#    def strong(self, text, **attrs):
#        return f"{term.bold}{text}{term.normal}"

#    def codespan(self, text, **attrs):
#        return f"{term.reverse}{text}{term.normal}"

#    def block_code(self, code, info=None, **attrs):
#        return f"{term.on_blue}\n{code}\n{term.normal}"

#    def list_item(self, text, **attrs):
#        return f"  {term.green}•{term.normal} {text}"

#    def table(self, header, body, **attrs):
#        rows = [header] + body.strip().split("\n")
#        columns = [row.strip("|").split("|") for row in rows]
#        col_widths = [max(len(col.strip()) for col in col) for col in zip(*columns)]

#        def draw_row(cells):
#            return "│" + "│".join(f" {cell.strip().ljust(width)} " for cell, width in zip(cells, col_widths)) + "│\n"

#        def draw_border(left, sep, right):
#            return left + sep.join("─" * (width + 2) for width in col_widths) + right + "\n"

#        table_str = (
#            draw_border("┌", "┬", "┐") +
#            draw_row(columns[0]) +
#            draw_border("├", "┼", "┤") +
#            "".join(draw_row(row) for row in columns[1:]) +
#            draw_border("└", "┴", "┘")
#        )

#        return f"{term.bold}{table_str}{term.normal}"

# Usage

if __name__ == "__main__":

    md_input = """
# Heading 1
## Heading 2
**Bold Text** and *Italic Text*

- Item 1
And this and that
- Item 2

>
> Indent
>

```Bash
Code block
```

| Column 1 | Column 2 |
|----------|------|
| Value 1  | Value 2   |
| Value 1  |                  Value 2  |

"""

renderer = AnsiRenderer()
markdown = mistune.create_markdown(renderer=renderer)
ansi_output = markdown(md_input)
print(ansi_output)
