import os
import zoneinfo
from textwrap import dedent

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TZ', 'Europe/London').strip()
if TIME_ZONE not in zoneinfo.available_timezones():
    raise ValueError(f'Invalid TIME_ZONE: "{TIME_ZONE}". '
                     'Please set a valid timezone with TZ env variable. '
                     'See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.')
GLOBUS_CLIENT_ID = os.getenv('GLOBUS_CLIENT_ID')
SUBJECT_REQUEST_EMAIL_FROM = os.getenv('APACHE_SERVER_ADMIN', 'alyx@localhost')
DEFAULT_SOURCE = 'IBL'
DEFAULT_PROTOCOL = '1'
SUPERUSERS = ('root',)
STOCK_MANAGERS = ('root',)
WEIGHT_THRESHOLD = 0.75
DEFAULT_LAB_NAME = 'cortexlab'
WATER_RESTRICTIONS_EDITABLE = False  # if set to True, all users can edit water restrictions
DEFAULT_LAB_PK = '4027da48-7be3-43ec-a222-f75dffe36872'
SESSION_REPO_URL = f'https://{os.getenv("APACHE_SERVER_NAME", "localhost")}/'
SESSION_REPO_URL += "{lab}/Subjects/{subject}/{date}/{number:03d}/"
NARRATIVE_TEMPLATES = {
    'Headplate implant': dedent('''
    == General ==

    Start time (hh:mm):   ___:___
    End time (hh:mm):    ___:___

    Bregma-Lambda :   _______  (mm)

    == Drugs == (copy paste as many times as needed; select IV, SC or IP)
    __________________( IV / SC / IP ) Admin. time (hh:mm)  ___:___

    == Coordinates ==  (copy paste as many times as needed; select B or L)
    (B / L) - Region: AP:  _______  ML:  ______  (mm)
    Region: _____________________________

    == Notes ==
    <write your notes here>
        '''),
}

# %% mbox: command-only worker
# Never serves HTTP. It is only `docker exec`'d for manage.py commands: the cortexlab import,
# Globus sync, maintenance and the openalyx release (iblalyx/releases/).


def _database(prefix, name='', host=''):
    """A postgres alias configured from the <prefix>_* environment variables."""
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv(f'{prefix}_NAME', name),
        'USER': os.getenv(f'{prefix}_USER', ''),
        'PASSWORD': os.getenv(f'{prefix}_PASSWORD', ''),
        'HOST': os.getenv(f'{prefix}_HOST', host),
        'PORT': os.getenv(f'{prefix}_PORT', '5432'),
    }


EXTRA_DATABASES = {
    'default': _database('PROD_DB'),  # production alyx
    # UCL import buffer, container cortexlab_buffer_postgres
    'cortexlab': _database('CORTEXLAB_BUFFER_DB', 'cortexlab', 'cortexlab_buffer_postgres'),
    # openalyx release buffer, container openalyx_buffer_postgres
    'public': _database('OPENALYX_BUFFER_DB', 'public', 'openalyx_buffer_postgres'),
    # The live openalyx RDS. NAME comes from the environment so that 02_upload_public_db.sh can
    # point this alias at the staged database by overriding OPENALYX_DB_NAME on the docker exec.
    'openalyx': _database('OPENALYX_DB', 'openalyx'),
}

# Opt-in safeguard for commands that must not write to production; 01a_download_database.sh sets
# it for the buffer migration. Field defaults that query the database are evaluated against
# `default` whatever `migrate --database` names, so a cross-database migrate can otherwise write
# to production unnoticed. With this set, Postgres refuses the write instead.
if os.getenv('ALYX_DEFAULT_READ_ONLY', '').lower() in ('true', '1', 't'):
    EXTRA_DATABASES['default']['OPTIONS'] = {'options': '-c default_transaction_read_only=on'}

# allauth is installed, without SSO_ENABLED, so that `migrate --database public` creates its
# tables in the release buffer: openalyx has single sign-on, production does not. No provider
# credentials are needed and no sign-in policy is active. Needs allauth >= 65.19.3, whose data
# migrations honour --database. AccountMiddleware is required by allauth.account all the same.
EXTRA_INSTALLED_APPS = (
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.orcid',
)
EXTRA_MIDDLEWARE = ('allauth.account.middleware.AccountMiddleware',)


class _AllauthPublicOnlyRouter:
    """Migrates the allauth tables into the release buffer only: neither production nor the
    cortexlab import buffer has single sign-on."""

    app_labels = {'allauth', 'account', 'socialaccount', 'orcid'}

    def allow_migrate(self, db, app_label, **hints):
        return db == 'public' if app_label in self.app_labels else None


DATABASE_ROUTERS = ['alyx.settings_lab._AllauthPublicOnlyRouter']
