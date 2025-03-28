"""
Vault DataExtractor
"""

from data_xtract import DataExtractor, InfoOutput, QueryFilter

VAULT_TARGETS = ('ns', 'mount', 'aws', 'kv', 'ldap', 'db', 'db_role')

class VaultDataExtractor(DataExtractor):
    def __init__(self, target: str):
        super().__init__()
        self._target = target.lower()
        # TODO validate

    def start(self, io: InfoOutput):
        """Nothing yet"""

    def finish(self, io: InfoOutput):
        """Nothing yet"""

    def extract(self, qfilter: QueryFilter, io: InfoOutput):
        """Nothing yet"""
        # TODO should "clear a path" at start and finish
        qfilter.unset_data(self._target)
