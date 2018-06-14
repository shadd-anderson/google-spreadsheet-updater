import datetime
import os
import time

from apiclient import discovery
from httplib2 import Http
from oauth2client import client
from urllib.error import HTTPError

# Sets up the API
from overbuff_scraper import OverbuffScraper


class Scraper:
    pass


credential_json = os.environ.get("CREDENTIALS")
creds = client.OAuth2Credentials.from_json(credential_json)
service = discovery.build('sheets', 'v4', http=creds.authorize(Http()))

# ID of the spreadsheet
spreadsheet_id = os.environ.get('SHEET_ID')

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


# Grabs all the values in the "Battletag" column of the spreadsheet
battletags = grab_column(spreadsheet_id, "D", sheetname="Roster")

print("Running scraper on " + datetime.datetime.strftime(datetime.datetime.now(), "%b %d, %I:%M%p"))
for index, battletag in enumerate(battletags, start=1):
    """Checks to make sure there's something in the cell. If not, moves on to the next one"""
    try:
        player_tag = battletag[0]
    except IndexError:
        continue

    if player_tag != 'Battletag':
        """Skips past the column headers"""

        # Tries to get the sr from Overbuff and logs the SR.
        try:
            player_sr = OverbuffScraper.sr_fetch(player_tag)
            print("{}'s SR: {}".format(player_tag, player_sr))

        # Catches incorrect battletags
        except HTTPError:
            print("Error retrieving {}'s page. Debug/update battletag".format(player_tag))
            # body = {
            #     'values': [["*LOST PAGE"]]
            # }
            # service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!F' + str(index)),
            #                                        valueInputOption='USER_ENTERED', body=body).execute()

        except UnicodeEncodeError:
            """Handles situations with odd-ball battletags"""
            print("{}'s SR: {}".format(player_tag.encode('utf-8').strip(), player_sr))
            body = {
                'values': [[player_sr]]
            }
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!F' + str(index)),
                                                   valueInputOption='USER_ENTERED', body=body).execute()
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!G' + str(index)),
                                                   valueInputOption='USER_ENTERED', body={'values': [[""]]}).execute()

        # Handles a un-reported/unranked player
        except AttributeError:
            print("{} has no SR reported".format(player_tag))
            body = {
                'values': [[r"**Not current**"]]
            }
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!G' + str(index)),
                                                   valueInputOption='USER_ENTERED', body=body).execute()

        # If everything is good to go, updates the spreadsheet
        else:
            body = {
                'values': [[player_sr]]
            }
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!F' + str(index)),
                                                   valueInputOption='USER_ENTERED', body=body).execute()
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=('Roster!G' + str(index)),
                                                   valueInputOption='USER_ENTERED', body={'values': [[""]]}).execute()

        time.sleep(1)
print("Scraper successfully completed at " + datetime.datetime.strftime(datetime.datetime.now(), "%I:%M%p"))
print("Please see above for errors")
