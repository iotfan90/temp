import os

from django.test.runner import DiscoverRunner

from .test_settings_local import *



IS_TEST = False


class UnManagedModelTestRunner(DiscoverRunner):
    """
    Test runner that automatically makes all unmanaged models in your Django
    project managed for the duration of the test run.
    Many thanks to the Caktus Group: http://bit.ly/1N8TcHW
    """
    def __init__(self, *args, **kwargs):
        super(UnManagedModelTestRunner, self).__init__(*args, **kwargs)
        self.unmanaged_models = None
        self.test_connection = None
        self.live_connection = None
        self.old_names = None

    def setup_databases(self, **kwargs):
        # override keepdb so that we don't accidentally blow away our existing magento database
        self.keepdb = True
        # set the Test DB name to the current DB name, which makes this more of an
        # integration test, but HEY, at least it's a start
        result = super(UnManagedModelTestRunner, self).setup_databases(**kwargs)

        return result


print('=========================')
print('In TEST Mode - ')


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"

print("  + SQLite dbs for default, disable magento db")

if not DATABASES:
    DATABASES = {}

project_dir = '%s/../../' % os.path.dirname(__file__)
print('  + Creating in %s' % project_dir)


DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': '%s.sqlite-test-db-default' % project_dir,
}

if not DATABASES.get('magento'):
    DATABASES['magento'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': project_dir+'.sqlite-test-db-magento',
    }


print("  + MD5 password hasher")
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
if os.environ.get('REUSE_DB', '') == '1':
    print("  + Disabling migrations")
    MIGRATION_MODULES = DisableMigrations()


DEBUG = TEMPLATE_DEBUG = False


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", '8_mz5vt-d^db=t*vbgs6^%h)1qjud)8w_k2au1_^0&k#_t2x!7')

DATABASE_ROUTERS = (
    # 'django_crate.routers.ModelMetaOptionRouter',
    'mobovidata_dj.routers.MagentoRouter',
)
# The custom routers we're using to route certain ORM queries
# to the remote host conflict with our overridden db settings.
# Set DATABASE_ROUTERS to an empty list to return to the defaults
# during the test run.

# DATABASE_ROUTERS = []

# Set Django's test runner to the custom class defined above
print('=========================')
