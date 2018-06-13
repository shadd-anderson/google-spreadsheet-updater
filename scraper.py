import datetime
import os
import time
import urllib.request

from bs4 import BeautifulSoup
from apiclient import discovery
from httplib2 import Http
from oauth2client import client
from urllib.error import HTTPError
from urllib.parse import quote

# Sets up the API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
json_string = os.environ.get("CREDENTIALS")
creds = client.OAuth2Credentials.from_json(json_string)
service = discovery.build('sheets', 'v4', http=creds.authorize(Http()))

# ID of the spreadsheet
spreadsheet_id = os.environ.get('SHEET_ID')


# fetches player SR from overbuff based on battletag
def sr_fetch(player):
    player_url = player.replace("#", "-")
    player_page = 'https://www.overbuff.com/players/pc/' + quote(player_url)
    req = urllib.request.Request(player_page)
    req.add_header("User-agent", "overbuff-scraper 0.1")
    page = urllib.request.urlopen(req)
    page_contents = BeautifulSoup(page, 'html.parser')
    sr_span = page_contents.find('span', attrs={'class': 'player-skill-rating'})
    return sr_span.text.strip()


# print(sr_fetch("swallama#1813"))
# ^ For debugging ^

# Grabs all the values in the "Battletag" column of the spreadsheet
battletag_column = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range='Roster!D:D').execute()
battletags = battletag_column.get('values')

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
            player_sr = sr_fetch(player_tag)
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
