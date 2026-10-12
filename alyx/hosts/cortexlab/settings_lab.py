import os
import zoneinfo
from textwrap import dedent

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
GLOBUS_CLIENT_ID = os.getenv('GLOBUS_CLIENT_ID')
SUBJECT_REQUEST_EMAIL_FROM = 'alyxdb@gmail.com'
DEFAULT_SOURCE = 'IBL'
DEFAULT_PROTOCOL = '1'
SUPERUSERS = ('root',)
STOCK_MANAGERS = ('root', 'charu')
WEIGHT_THRESHOLD = 0.8
DEFAULT_LAB_NAME = 'cortexlab'
WATER_RESTRICTIONS_EDITABLE = True  # if set to True, all users can edit water restrictions
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
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-west-2'
AWS_SES_REGION_ENDPOINT = 'email.eu-west-2.amazonaws.com'

