"""
A RecordWriter that uses Jinja2 to produce output.
It can operate in either in record-by-record or batch mode.
"""

from importlib import resources as impresources
from io import FileIO
from typing import Any
import inspect
import sys

from jinja2 import Environment, FileSystemLoader, Template, ChainableUndefined, DebugUndefined, StrictUndefined

from .base import FileRecordWriter
from . import templates

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

    def start(self) -> None:
        self._env = Environment(loader=FileSystemLoader(['.', str(impresources.files(templates))]),
                                autoescape=self.auto_escape,
                                trim_blocks=self.trim_blocks,
                                lstrip_blocks=self.lstrip_blocks,
                                keep_trailing_newline=self.keep_last_newline,
                                undefined=ChainableUndefined if self.chain_undefined else StrictUndefined,
                                )
        auto_register_filters(self._env, type(self))
        if not self.template_filename: self.template_filename = 'batch.j2' if self._is_batch else 'record.j2'
        self._template = self._env.get_template(self.template_filename)
        super().start()

    def finish(self):
        try:
            if self._is_batch:
                # finally render the accumulated records
                try:
                    self._render(self._batch_data)
                finally:
                    self._batch_data = []
        finally:
            self._template = None
        super().finish()

    def write(self, record: list[any]) -> bool:
        # Save up in batch mode: the template must handle data as a list
        if self._is_batch:
            self._batch_data.append(record)
        else:
            self._render(record)
        return True

    def write_headers(self) -> bool:
        """Nothing here: rendering of headers must be done in the template itself"""
        return True

    def _render(self, data: Any) -> None:
        self.print(
            self._template.render(
                is_batch=self._is_batch,
                include_headers=self.include_headers,
                record_keys=self.headers,
                record_data=data
        ))

    @staticmethod
    def filter_zip(seq1, seq2):
        return zip(seq1 or [], seq2 or [])

    @staticmethod
    def filter_stringify(obj: Any) -> str:
        return TemplateRecordWriter.stringify(obj)

_FILTER_PREFIX = 'filter_'
def auto_register_filters(env: Environment, cls):
    for method_name in dir(cls):
        if method_name.startswith(_FILTER_PREFIX):
            method = getattr(cls, method_name)
            if callable(method):
                signature = inspect.signature(method)
                if 0 < len(signature.parameters) <= 3:
                    env.filters[method_name.removeprefix(_FILTER_PREFIX)] = method
