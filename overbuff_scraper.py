import urllib.request

from bs4 import BeautifulSoup
from urllib.parse import quote


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
        return sr_span.text.strip()
