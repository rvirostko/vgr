#! /usr/bin/env python3

import sys
from io import FileIO
from .base import FileRecordWriter

import django
from django.conf import settings
from django.template import Engine, Context

class TemplateRecordWriter(FileRecordWriter):

    __DEFAULT_TEMPLATE = """
    {% for key, value in data.items %}{{ key }}: {{ value|escape }}
    {% endfor %}"""

    def __init__(self, file: FileIO=sys.stdout.buffer):
        super().__init__(file)
        if not settings.configured:
            # 'DIRS': ['templates']
            settings.configure(
                TEMPLATES=[ {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                } ])
            django.setup()
        self.set_template(self.__DEFAULT_TEMPLATE)
        self.set_auto_escape(False)
        self.set_debug(False)
        self.set_include_null()
        self._tags = []

    def set_auto_escape(self, enable: bool=True):
        self._auto_escape = enable
        return self

    def set_debug(self, enable: bool=True):
        self._debug = enable
        return self

    def set_include_null(self, enable: bool=True):
        self._include_null = enable
        return self

    def add_tags(self, tag_module: str):
        if tag_module: self._tags.append(tag_module)
        return self

    def set_template(self, template: str):
        self._template_text = template
        self._template = None
        return self

    def read_template(self, file_name: str):
        with open(file_name, 'r') as file: self.set_template(file.read())
        return self

    def start(self) -> bool:
        engine = Engine(
            debug=self._debug,             # Enable for better error messages
            autoescape=self._auto_escape,  # Auto-escapes variables
            builtins=self._tags,           # Additional built-in template tags/filters
        )
        self._template = engine.from_string(self._template_text or self.__DEFAULT_TEMPLATE)
        return super().start()

    def finish(self):
        self._template = None
        return super().finish()

    def write_headers(self) -> bool:
        return super().write_headers()

    def write(self, record: list[any]) -> bool:
        context = Context({
            "headers": self._headers,
            "data": self.objectify(record, self._include_null)
        })
        self.print(self._template.render(context))
        #self.flush()
        return True

# TODO - need different modes in the same way we have for JSON
# - "per_record" : the template applies to a single record, handle as we get them
# - "default" : save up all records doing a copy.deepcopy() then when we finish,
#   render the template with an array of the records