"""
Defines the Ldap extension
"""

from typing import Dict, Callable

from ..extn import VgrExtension
from ..data_dict import DataDictionary

from .stmts import (
    execute_connect,
    execute_disconnect,
    execute_search,
    ldap_initialize,
)

from .functions import (
    attr_between,
    attr_equals,
    attr_exists,
    attr_greaterthan,
    attr_greaterthaneq,
    attr_lessthan,
    attr_lessthaneq,
    attr_match,
    attr_not_equals,
    attr_not_exists,
    ldap_and,
    ldap_escape,
    ldap_not,
    ldap_or,
    qbe_to_filter,
)

_FUNCTIONS = {
    "LdapAttrBetween"     : attr_between,
    "LdapAttrEquals"      : attr_equals,
    "LdapAttrExists"      : attr_exists,
    "LdapAttrGE"          : attr_greaterthaneq,
    "LdapAttrGreaterThan" : attr_greaterthan,
    "LdapAttrLE"          : attr_lessthaneq,
    "LdapAttrLessThan"    : attr_lessthan,
    "LdapAttrMatches"     : attr_match,
    "LdapAttrNotEqual"    : attr_not_equals,
    "LdapAttrNotExists"   : attr_not_exists,
    "LdapEscape"          : ldap_escape,
    "LdapFilterAnd"       : ldap_and,
    "LdapFilterNot"       : ldap_not,
    "LdapFilterOr"        : ldap_or,
    "ToLdapFilter"        : qbe_to_filter,
}

_HANDLERS = {
    'ldap_connect'    : execute_connect,
    'ldap_disconnect' : execute_disconnect,
    'ldap_search'     : execute_search,
}

class LdapExtension(VgrExtension):
    def initialize(self, dd: DataDictionary) -> None:
        ldap_initialize(dd)

    def adds_statements(self):
        return True

    def grammar(self) -> str:
        return self.read_resource_text(__package__, 'ldap.lark')

    def functions(self) -> Dict[str, Callable]:
        return _FUNCTIONS

    def statement_handlers(self) -> Dict[str, Callable]:
        return _HANDLERS
