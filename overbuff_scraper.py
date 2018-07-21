import os
import time
import urllib.request
from datetime import datetime
from urllib.error import HTTPError

from bs4 import BeautifulSoup
from urllib.parse import quote

from spreadsheet_update import update_cell, grab_column

sr_column = 'Roster!F'
career_high_column = 'Roster!G'
last_updated_column = 'Roster!H'
notes_column = 'Roster!I'

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
    def update_srs(playertag, row, date):
        """Tries to get the sr from Overbuff and logs the SR."""
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
            update_cell(SPREADSHEET_ID, (notes_column + str(row)), body)

        # except UnicodeEncodeError:
        #     """Handles situations with odd-ball battletags"""
        #     # print("{}'s SR: {}".format(player_tag.encode('utf-8').strip(), player_sr))
        #     body = {
        #         'values': [[player_sr]]
        #     }
        #     update_cell(SPREADSHEET_ID, ('Roster!F' + str(row)), body)
        #     update_cell(SPREADSHEET_ID, ('Roster!H' + str(row)), {'values': [[""]]})

        # Handles a un-reported/unranked player
        except AttributeError:
            print("{} has no SR reported".format(playertag))
            body = {
                'values': [[r"**Not current**"]]
            }
            update_cell(SPREADSHEET_ID, (notes_column + str(row)), body)
        # If everything is good to go, updates the spreadsheet
        else:
            body = {
                'values': [[player_sr]]
            }
            update_cell(SPREADSHEET_ID, (sr_column + str(row)), body)
            if ispublic:
                update_cell(SPREADSHEET_ID, (notes_column + str(row)), {'values': [[""]]})
                update_cell(SPREADSHEET_ID, (last_updated_column + str(row)), {'values': [[date]]})
            else:
                update_cell(SPREADSHEET_ID, (notes_column + str(row)), {'values': [["Private profile"]]})
                print("{} has a private profile!".format(playertag))


if __name__ == '__main__':
    current_time = datetime.now()
    battletags = grab_column(SPREADSHEET_ID, "D", sheetname="Roster")
    srs = grab_column(SPREADSHEET_ID, "F", sheetname="Roster")
    career_highs = grab_column(SPREADSHEET_ID, "G", sheetname="Roster")
    print("Running scraper on " + datetime.strftime(current_time, "%b %d, %I:%M%p"))
    for index, battletag in enumerate(battletags, start=1):
        """Checks to make sure there's something in the cell. If not, moves on to the next one"""
        try:
            player_tag = battletag[0]
        except IndexError:
            continue

        if player_tag != 'Battletag':
            """Skips past the column headers"""
            OverbuffScraper.update_srs(playertag=player_tag,
                                       row=index,
                                       date=datetime.strftime(current_time, "%d/%m/%y"))
            if len(career_highs[index-1]) == 0 or srs[index-1][0] > career_highs[index-1][0]:
                update_cell(SPREADSHEET_ID, (career_high_column + str(index)), {'values': [[srs[index-1][0]]]})
            time.sleep(2)
    print("Scraper successfully completed at " + datetime.strftime(datetime.now(), "%I:%M%p"))
    print("Please see above for errors")
    # OverbuffScraper.update_srs("SolusPrime42#1304",
    #                            188,
    #                            datetime.strftime(current_time, "%d/%m/%y"))
