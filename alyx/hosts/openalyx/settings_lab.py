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

# %% Public database
PUBLIC_DATABASE = True
PUBLIC_SIGNUP_RESERVED_USERNAMES = (
    "root", "admin", "administrator", "alyx", "test", "public", "anonymous", "intbrainlab")
# Mailing preferences offered at sign-up; empty elsewhere, as consent to be emailed is specific
# to a public database.
EMAIL_PREFERENCES = {
    "Data-release updates": "I agree that IBL may use my email address to send me updates about data releases. I can unsubscribe at any time by unchecking this box.",
    "Follow-up about my research": "I agree that IBL may contact me occasionally by email, beginning six months after I receive access to the database, to ask whether and how I used the data, including what studies I conducted. I may choose whether to respond and can withdraw my consent at any time.",
}
# Email via Amazon SES (`pip install django-ses`)
EMAIL_BACKEND = "django_ses.SESBackend"
AWS_SES_REGION_NAME = "eu-west-2"
AWS_SES_REGION_ENDPOINT = "email.eu-west-2.amazonaws.com"
# Must be an address at a verified SES identity, or SES rejects the message.
DEFAULT_FROM_EMAIL = os.getenv("ALYX_FROM_EMAIL", "alyx@internationalbrainlab.org")
_orcid_id = os.getenv("ORCID_CLIENT_ID")
_orcid_secret = os.getenv("ORCID_CLIENT_SECRET")
if _orcid_id and _orcid_secret:
    SSO_ENABLED = True
    SSO_PROVIDER = "orcid"
    SSO_PROVIDER_NAME = "ORCiD"
    SSO_CREATE_USER = True
    ACCOUNT_USERNAME_BLACKLIST = PUBLIC_SIGNUP_RESERVED_USERNAMES
    SOCIALACCOUNT_PROVIDERS = {
        "orcid": {
            "APP": {"client_id": _orcid_id, "secret": _orcid_secret},
            # sandbox.orcid.org for the ORCID sandbox, orcid.org for the real thing
            "BASE_DOMAIN": os.getenv("ORCID_BASE_DOMAIN", "orcid.org"),
        },
    }
    LOGIN_REDIRECT_URL = "/admin"
    LOGOUT_REDIRECT_URL = "/admin/login/"

