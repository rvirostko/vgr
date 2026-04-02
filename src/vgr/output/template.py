"""
A RecordWriter that uses Jinja2 to produce output.
It can operate in either in record-by-record or batch mode.
"""

from io import FileIO
from typing import Any
import traceback
import inspect
import sys

from jinja2 import Environment, FileSystemLoader, Template, ChainableUndefined, DebugUndefined, StrictUndefined

from .base import FileRecordWriter

class TemplateRecordWriter(FileRecordWriter):

    def __init__(self, file: FileIO=sys.stdout, **kwargs):
        super().__init__(file)
        self._env: Environment = None
        self._is_batch = False
        self._batch_data = []
        self._template_filename = None
        self._template: Template = None
        self._auto_escape = False
        self._trim_blocks = False
        self._lstrip_blocks = False
        self._keep_last_newline = False
        self._chain_undefined = False
        self._setattrs(**kwargs)

    def _attrs(self) -> list:
        # We intentionally skip the template itself
        return super()._attrs() + ['template_type', 'template_filename', 'auto_escape', 'trim_blocks', 'lstrip_blocks', 'keep_last_newline', 'chain_undefined']

    @property
    def template_type(self) -> str:
        return 'batch' if self._is_batch else 'record'

    @template_type.setter
    def template_type(self, ttype: str) -> None:
        self._is_batch = ttype and ttype.lower() == 'batch'

    @property
    def auto_escape(self) -> bool:
        return self._auto_escape

    @auto_escape.setter
    def auto_escape(self, enable: bool):
        self._auto_escape = bool(enable)

    @property
    def trim_blocks(self) -> bool:
        return self._trim_blocks

    @trim_blocks.setter
    def trim_blocks(self, enable: bool):
        self._trim_blocks = bool(enable)

    @property
    def lstrip_blocks(self) -> bool:
        return self._lstrip_blocks

    @lstrip_blocks.setter
    def lstrip_blocks(self, enable: bool):
        self._lstrip_blocks = bool(enable)

    @property
    def keep_last_newline(self) -> bool:
        return self._keep_last_newline

    @keep_last_newline.setter
    def keep_last_newline(self, enable: bool):
        self._keep_last_newline = bool(enable)

    @property
    def chain_undefined(self) -> bool:
        return self._chain_undefined

    @chain_undefined.setter
    def chain_undefined(self, enable: bool):
        self._chain_undefined = bool(enable)

    @property
    def template_filename(self) -> str:
        return self._template_filename or ''

    @template_filename.setter
    def template_filename(self, filename: str) -> str:
        self._template_filename = filename or ''

    _BATCH_DEFAULT_TEMPLATE = """{%- if record_keys and record_data -%}
{%- set ns = namespace(fmt="",col_widths=[],bar="") -%}
{%- set box = namespace(H="\u2500", V="\u2502", DR="\u250C", DL="\u2510", UR="\u2514", UL="\u2518", X="\u253C", T="\u252C", B="\u2534", L="\u251C", R="\u2524" ) -%}
{%- set ns.col_widths = record_keys | map("string") | map("length") | list -%}
{%- for row in record_data -%}
    {% set data_widths = row | map("string") | map("length") | list -%}
    {%- set t = [] %}{% for x, y in ns.col_widths | zip(data_widths) %}{% set _ = t.append([x, y] | max) %}{% endfor -%}
    {%- set ns.col_widths = t -%}
{%- endfor -%}
{%- for w in ns.col_widths -%}
    {%- set ns.fmt = ns.fmt ~ " " ~ box.V ~ " " ~ "{:<" ~ w ~ "." ~ w ~ "}" -%}
{%- endfor -%}
{%- set ns.fmt = (ns.fmt | trim) ~ " " ~ box.V -%}
{%- set ns.bar = box.H * (ns.col_widths | max) -%}
{%- set divider = record_keys | map("string") | map("truncate", 0, True, "", 0) | map("replace", "", ns.bar) | list -%}
{%- set ns.bar = ns.fmt.format(*divider) | replace(" ", box.H) -%}
{%- set st = box.V ~ box.H -%}
{%- set md = box.H ~ box.V ~ box.H -%}
{%- set ed = box.H ~ box.V  -%}
{{ ns.bar | replace(md, box.H ~ box.T ~ box.H) | replace(st, box.DR ~ box.H) | replace(ed, box.H ~ box.DL) }}
{%- if include_headers %}
{{ ns.fmt.format(*record_keys | map("string")) }}
{{ ns.bar | replace(md, box.H ~ box.X ~ box.H) | replace(st, box.L ~ box.H) | replace(ed, box.H ~ box.R) }}
{%- endif %}
{% for row in record_data -%}
    {{ ns.fmt.format(*row | map("string")) }}
{% endfor -%}
{{ ns.bar | replace(md, box.H ~ box.B ~ box.H) | replace(st, box.UR ~ box.H) | replace(ed, box.H ~ box.UL) }}
{% endif %}"""

    _DEFAULT_TEMPLATE = """{%- if record_keys and record_data %}
{%- set ns = namespace(fmt="",key_width=0,data_width=0,bar="") -%}
{%- set box = namespace(H="\u2500", V="\u2502", DR="\u250C", DL="\u2510", UR="\u2514", UL="\u2518", X="\u253C", T="\u252C", B="\u2534", L="\u251C", R="\u2524" ) -%}
{% set key_width = record_keys | map("string") | map("length") | max -%}
{% set data_width = record_data | map("string") | map("length") | max -%}
{%- set ns.fmt = box.V ~ " {:<" ~ key_width ~ "." ~ key_width ~ "} " ~ box.V ~ " {:<" ~ data_width ~ "." ~ data_width ~ "} " ~ box.V -%}
{%- set ns.bar = ns.fmt.format(box.H * key_width, box.H * data_width) | replace(" ", box.H) -%}
{%- set st = box.V ~ box.H -%}
{%- set md = box.H ~ box.V ~ box.H -%}
{%- set ed = box.H ~ box.V  -%}
{{ ns.bar | replace(md, box.H ~ box.T ~ box.H) | replace(st, box.DR ~ box.H) | replace(ed, box.H ~ box.DL) }}
{% for key, data in record_keys | zip(record_data) -%}
{{ ns.fmt.format(key | string , data | string) }}
{% endfor -%}
{{ ns.bar | replace(md, box.H ~ box.B ~ box.H) | replace(st, box.UR ~ box.H) | replace(ed, box.H ~ box.UL) }}
{% endif %}"""

    def start(self) -> bool:
        self._env = Environment(loader=FileSystemLoader('.'),
                                autoescape=self.auto_escape,
                                trim_blocks=self.trim_blocks,
                                lstrip_blocks=self.lstrip_blocks,
                                keep_trailing_newline=self.keep_last_newline,
                                undefined=ChainableUndefined if self.chain_undefined else DebugUndefined if self.debug else StrictUndefined,
                                )
        auto_register_filters(self._env, type(self))
        t = None
        if self._template_filename:
            t = self._env.get_template(self._template_filename)
        else:
            t = self._env.from_string(self._BATCH_DEFAULT_TEMPLATE if self._is_batch else self._DEFAULT_TEMPLATE)
        self._template = t
        return super().start()

    def finish(self):
        try:
            if self._is_batch:
                # finally render all the records
                try:
                    self._render(self._batch_data)
                finally:
                    self._batch_data = []
        finally:
            self._template = None
        return super().finish()

    def write(self, record: list[any]) -> bool:
        # Save up in batch mode: the template must handle data as a list
        if self._is_batch:
            self._batch_data.append(record)
        else:
            self._render(record)
        return True

    def _render(self, data: Any) -> None:
        try:
            self.print(
                self._template.render(
                    debug=self.debug,
                    verbose=self.verbose,
                    is_batch=self._is_batch,
                    include_headers=self.include_headers,
                    record_keys=self.headers,
                    record_data=data
            ))
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            raise e

    @staticmethod
    def filter_zip(seq1, seq2):
        return zip(seq1 or [], seq2 or [])

_FILTER_PREFIX = 'filter_'
def auto_register_filters(env: Environment, cls):
    for method_name in dir(cls):
        if method_name.startswith(_FILTER_PREFIX):
            method = getattr(cls, method_name)
            if callable(method):
                signature = inspect.signature(method)
                if 0 < len(signature.parameters) <= 3:
                    env.filters[method_name.removeprefix(_FILTER_PREFIX)] = method
