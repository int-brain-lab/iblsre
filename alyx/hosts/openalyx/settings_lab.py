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

# %% Public database
# Uncomment on a public, read-only deployment serving released data. This enables the
# self-registration page at /signup and hides lab member records from public users, who may
# then see only redacted users and themselves. See settings.py for the other PUBLIC_SIGNUP_*
# options and their defaults.
PUBLIC_DATABASE = True

# Registration confirmation and password reset both send mail, so a public database needs a
# working email backend. For example, using django_ses (`pip install django-ses`):
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-west-2'
AWS_SES_REGION_ENDPOINT = 'email.eu-west-2.amazonaws.com'
DEFAULT_FROM_EMAIL = 'alyx@example.org'  # must be an SES-verified sender
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
