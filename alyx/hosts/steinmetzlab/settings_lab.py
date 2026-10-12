import os
from textwrap import dedent

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TZ', 'America/Los_Angeles').strip()
GLOBUS_CLIENT_ID = os.getenv('GLOBUS_CLIENT_ID')
SUBJECT_REQUEST_EMAIL_FROM = 'alyx@steinmetzlab.net'
DEFAULT_SOURCE = 'Foege 060'
DEFAULT_PROTOCOL = '1'
SUPERUSERS = ('nick',)
STOCK_MANAGERS = ('nick',)
WEIGHT_THRESHOLD = 0.8
DEFAULT_LAB_NAME = 'steinmetzlab'
WATER_RESTRICTIONS_EDITABLE = False  # if set to True, all users can edit water restrictions
DEFAULT_LAB_PK = '60aebacf-6a14-4e0f-985c-2324160e8721'
#SESSION_REPO_URL = \
#    "http://ibl.flatironinstitute.org/{lab}/Subjects/{subject}/{date}/{number:03d}/"
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

