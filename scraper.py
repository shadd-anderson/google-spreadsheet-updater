import os

from apiclient import discovery
from httplib2 import Http
from oauth2client import client


class Scraper:
    pass


credential_json = os.environ.get("CREDENTIALS")
creds = client.OAuth2Credentials.from_json(credential_json)
service = discovery.build('sheets', 'v4', http=creds.authorize(Http()))

# print(OverbuffScraper.sr_fetch("swallama#1813"))
# ^ For debugging ^


def grab_column(spreadsheetid, column, sheetname=""):
    if sheetname != "":
        sheetname = sheetname + "!"

    column_values = service\
        .spreadsheets()\
        .values()\
        .get(spreadsheetId=spreadsheetid, range='{}{}'.format(sheetname, column + ":" + column))\
        .execute()

    return column_values.get('values')


def update_cell(spreadsheetid, cell, body):
    service.spreadsheets().values().update(spreadsheetId=spreadsheetid, range=cell,
                                           valueInputOption='USER_ENTERED', body=body).execute()
