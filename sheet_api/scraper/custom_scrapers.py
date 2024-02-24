from bs4 import BeautifulSoup

from sheet_api.scraper.overrides import SiteOverride
from sheet_api.scraper.page_helpers import get_page_text
from sheet_api.scraper.scraped_work import ScrapedWork


class HandelScraper(SiteOverride):
    def scrape_page(self) -> list[ScrapedWork]:
        url = "https://en.wikipedia.org/wiki/List_of_compositions_by_George_Frideric_Handel"
        text = get_page_text(url)

        return self._parse_page(text)

    def _parse_page(self, text: str) -> list[ScrapedWork]:
        soup = BeautifulSoup(text, "html.parser")

        # find caption tag which contains text List of Operas
        opera_table = soup.find("caption", text="List of operas").findNext("tbody")
        print("parse_page")

        return []
