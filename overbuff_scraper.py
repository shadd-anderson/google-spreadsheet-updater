import os
import time
import urllib.request
from datetime import datetime
from urllib.error import HTTPError

from bs4 import BeautifulSoup
from urllib.parse import quote

from spreadsheet_update import update_cell, grab_column

SPREADSHEET_ID = os.environ.get('SHEET_ID')


class OverbuffScraper:

    @staticmethod
    def sr_fetch(player):
        player_url = player.replace("#", "-")
        player_page = 'https://www.overbuff.com/players/pc/' + quote(player_url)
        req = urllib.request.Request(player_page)
        req.add_header("User-agent", "overbuff-scraper 0.1")
        page = urllib.request.urlopen(req)
        page_contents = BeautifulSoup(page, 'html.parser')
        sr_span = page_contents.find('span', attrs={'class': 'player-skill-rating'})
        ispublic = True
        if page_contents.find('i', attrs={'class': 'fa-lock'}) is not None:
            ispublic = False
        return sr_span.text.strip(), ispublic

    @staticmethod
    def update_srs(playertag, row):
        # Tries to get the sr from Overbuff and logs the SR.
        try:
            player_sr, ispublic = OverbuffScraper.sr_fetch(playertag)
            # print("{}'s SR: {}".format(player_tag, player_sr))

        # Catches incorrect battletags
        except HTTPError:
            print("Error retrieving {}'s page. Debug/update battletag".format(playertag))
            body = {
                'values': [["""Battletag incorrect? (Case-sensitive) - If you see a whole column of these, """
                            """PM swallama NOW!!"""]]
            }
            update_cell(SPREADSHEET_ID, ('Roster!G' + str(row)), body)

        # except UnicodeEncodeError:
        #     """Handles situations with odd-ball battletags"""
        #     # print("{}'s SR: {}".format(player_tag.encode('utf-8').strip(), player_sr))
        #     body = {
        #         'values': [[player_sr]]
        #     }
        #     update_cell(SPREADSHEET_ID, ('Roster!F' + str(row)), body)
        #     update_cell(SPREADSHEET_ID, ('Roster!G' + str(row)), {'values': [[""]]})

        # Handles a un-reported/unranked player
        except AttributeError:
            print("{} has no SR reported".format(playertag))
            body = {
                'values': [[r"**Not current**"]]
            }
            update_cell(SPREADSHEET_ID, ('Roster!G' + str(row)), body)
        # If everything is good to go, updates the spreadsheet
        else:
            body = {
                'values': [[player_sr]]
            }
            update_cell(SPREADSHEET_ID, ('Roster!F' + str(row)), body)
            if ispublic:
                update_cell(SPREADSHEET_ID, ('Roster!G' + str(row)), {'values': [[""]]})
            else:
                update_cell(SPREADSHEET_ID, ('Roster!G' + str(row)), {'values': [["Private profile"]]})
                print("{} has a private profile!".format(playertag))


if __name__ == '__main__':
    battletags = grab_column(SPREADSHEET_ID, "D", sheetname="Roster")
    print("Running scraper on " + datetime.strftime(datetime.now(), "%b %d, %I:%M%p"))
    for index, battletag in enumerate(battletags, start=1):
        """Checks to make sure there's something in the cell. If not, moves on to the next one"""
        try:
            player_tag = battletag[0]
        except IndexError:
            continue

        if player_tag != 'Battletag':
            """Skips past the column headers"""
            OverbuffScraper.update_srs(player_tag, index)
            time.sleep(1)
    print("Scraper successfully completed at " + datetime.strftime(datetime.now(), "%I:%M%p"))
    print("Please see above for errors")
    # OverbuffScraper.update_srs("IMfierypanda#1638", 59)
