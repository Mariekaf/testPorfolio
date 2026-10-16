from django.conf import settings
from django.test.runner import DiscoverRunner

from config.database_checks import check_test_maintenance_access


class PostgreSQLTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        # Fail before creation rather than allowing Django to fall back to the
        # application/test database when maintenance access is unavailable.
        check_test_maintenance_access(settings.CONFIG['database'])
        return super().setup_databases(**kwargs)
