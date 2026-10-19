import os
import zoneinfo
from textwrap import dedent

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TZ', 'Europe/Paris').strip()
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
WEIGHT_THRESHOLD = 0.85
DEFAULT_LAB_NAME = 'cazetteslab'
WATER_RESTRICTIONS_EDITABLE = False  # if set to True, all users can edit water restrictions
DEFAULT_LAB_PK = '63983e4e-6065-482e-9c23-81d654c7a79d'
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

# Admin colors for this deployment (reseaumed palette), see the ADMIN_THEME setting in alyx's
# docs/03_deployment.md.
ADMIN_THEME = {
    '--primary': '#afaafa',
    '--secondary': '#afaafa',
    '--link-fg': '#606060',
    '--link-selected-fg': '#3c3c3c',
    '--breadcrumbs-bg': '#d2e65a',
    '--breadcrumbs-fg': '#606060',
    '--breadcrumbs-link-fg': '#3c3c3c',
    '--button-fg': '#fff',
    '--button-bg': '#6e6a5a',
    '--button-hover-bg': '#ff8c6e',
    '--default-button-bg': '#6e6a5a',
    '--default-button-hover-bg': '#ff8c6e',
}
