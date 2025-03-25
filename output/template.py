import os
import sys

from io import FileIO
from typing import Any

import django
from django.conf import settings
from django.template import Engine, Context

from .base import FileRecordWriter

class TemplateRecordWriter(FileRecordWriter):

    _BATCH_DEFAULT_TEMPLATE="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: .25rem;
            text-align: left;
            border: 1pt solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Data</h1>
    <table>
        <thead>
            <tr>
                {% for header in headers %}
                    <th>{{ header }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
                <tr>
                    {% for header in headers %}
                        <td>{{ get_attr(row, header) }}</td>
                    {% endfor %}
                </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

    __DEFAULT_TEMPLATE = """
{% for key, value in data.items %}{{ key }}: {{ value|escape }}
{% endfor %}"""

    def __init__(self, file: FileIO=sys.stdout.buffer, **kwargs):
        super().__init__(file)
        self._x()
        if not settings.configured:
            settings.configure(
                TEMPLATES=[ {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                } ])
            django.setup()
        self._is_batch = False
        self._batch_data = []
        self._template_text = None
        self._template_filename = None
        self._template = None # the actual template
        self._auto_escape = False
        self._debug = False
        self._include_nulls = True
        self._setattrs(**kwargs)

    def _attrs(self) -> list:
        # We intentionally skip template_text and the template itself
        return super()._attrs() + ['template_type', 'debug', 'auto_escape', 'include_nulls', 'template_filename']

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
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, enable: bool):
        self._debug = bool(enable)

    @property
    def include_nulls(self) -> bool:
        return self._include_nulls

    @include_nulls.setter
    def include_nulls(self, enable: bool):
        self._include_nulls = bool(enable)

    @property
    def template_text(self) -> str:
        return self._template_text or ''

    @template_text.setter
    def template_text(self, text: str):
        self._template_text = text or ''
        self._template = None

    @property
    def template_filename(self) -> str:
        return self._template_filename or ''

    @template_filename.setter
    def template_filename(self, filename: str) -> str:
        self._template_filename = filename or ''
        if self._template_filename:
            with open(self._template_filename, 'r', encoding='utf-8') as file:
                self.template_text = file.read()

    @staticmethod
    def get_attr(d, k):
        return None if d is None or k is None else getattr(d, k, None)

    def start(self) -> bool:
        engine = Engine(
            debug=self.debug,             # Enable for better error messages
            autoescape=self.auto_escape,  # Auto-escapes variables
        #    builtins=['.TemplateRecordWriter.get_attr'],
        )
        self._template = engine.from_string(self._template_text or self._BATCH_DEFAULT_TEMPLATE
                                            if self._is_batch else self.__DEFAULT_TEMPLATE)
        return super().start()

    # Your custom method that you want to use in templates
    def custom_method(self, value):
        return f"Processed: {value}"

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
            self._batch_data.append(self.objectify(record, self.include_nulls))
        else:
            self._render(self.objectify(record, self.include_nulls))
        return True

    def _render(self, data: Any) -> None:
        context = Context({
            "headers": self.headers,
            "data": data
        })
        self.print(self._to_ascii(self._template.render(context)))

    def _x(self):
        # Get the absolute path of the current file
        current_file_path = os.path.abspath(__file__)

        # Get the directory of the current file
        current_dir = os.path.dirname(current_file_path)

        # Assuming your file is in a package, you can derive the module path from the directory
        # For example, if your file is in my_project/my_app/custom_filters.py,
        # the module path would be 'my_app.custom_filters'

        # Modify sys.path if necessary to include the base project directory
        # if your module isn't already discoverable
        sys.path.insert(0, current_dir)

        # Now you can use the module path in `add_to_builtins`
        module_path = os.path.splitext(os.path.relpath(current_file_path, current_dir))[0].replace(os.sep, '.')

        print(module_path)  # This will give you something like 'my_app.custom_filters'
