import datetime
import re

from bs4 import BeautifulSoup, NavigableString

from sheet_api.scraper.overrides import SiteOverride
from sheet_api.scraper.page_helpers import get_page_text
from sheet_api.scraper.scraped_work import ScrapedWork

# class ScrapedWork:
#     composer_firstname: str
#     composer_lastname: str
#     composer_fullname: str
#     work_title: str
#     composition_year: int
#     opus: str
#     opus_number: int
#


class HandelScraper(SiteOverride):
    def scrape_page(self) -> list[ScrapedWork]:
        url = "https://en.wikipedia.org/wiki/List_of_compositions_by_George_Frideric_Handel"
        text = get_page_text(url)

        return self._parse_page(text)

    def _parse_page(self, text: str) -> list[ScrapedWork]:
        soup = BeautifulSoup(text, "html.parser")
        works = []
        # find the first tbody in the document
        opera_soup = soup.find("tbody")
        works += self._scrape_simple_table(opera_soup)
        # get the second tbody from the soup
        incidental_soup = opera_soup.find_next("tbody")
        works += self._scrape_simple_table(incidental_soup)

        oratorio_soup = incidental_soup.find_next("tbody")
        works += self._scrape_simple_table(oratorio_soup)

        odes_soup = oratorio_soup.find_next("tbody")
        works += self._scrape_simple_table(odes_soup)

        cantatas_soup = odes_soup.find_next("tbody")
        works += self._scrape_simple_table(cantatas_soup)

        italian_duets_soup = cantatas_soup.find_next("tbody")
        works += self._scrape_simple_table(italian_duets_soup)

        italian_trios_soup = italian_duets_soup.find_next("tbody")
        works += self._scrape_simple_table(italian_trios_soup)

        hymns_soup = italian_trios_soup.find_next("tbody")
        works += self._scrape_simple_table(hymns_soup, voice_tables=True)

        italian_arias_soup = hymns_soup.find_next("tbody")
        works += self._scrape_simple_table(italian_arias_soup, voice_tables=True)

        english_songs_soup = italian_arias_soup.find_next("tbody")
        works += self._scrape_simple_table(english_songs_soup, voice_tables=True)

        german_cantatas_soup = english_songs_soup.find_next("tbody")
        works += self._scrape_simple_table(german_cantatas_soup)

        italian_sacred_cantatas_soup = german_cantatas_soup.find_next("tbody")
        works += self._scrape_simple_table(
            italian_sacred_cantatas_soup, voice_tables=True
        )
        # skip latin church music
        anthems_soup = italian_sacred_cantatas_soup.find_next("tbody").find_next(
            "tbody"
        )
        works += self._scrape_simple_table(anthems_soup)

        canticles_soup = anthems_soup.find_next("tbody")
        works += self._scrape_simple_table(canticles_soup, voice_tables=True)

        concertos_soup = canticles_soup.find_next("tbody")
        works += self._scrape_simple_table(
            concertos_soup, tds_func=self._extract_concerto_tds
        )

        concerto_grosso_soup = concertos_soup.find_next("tbody")
        works += self._scrape_simple_table(
            concerto_grosso_soup, tds_func=self._extract_concerto_grosso_tds
        )

        orchestral_soup = concerto_grosso_soup.find_next("tbody")
        works += self._scrape_simple_table(
            orchestral_soup, tds_func=self._extract_orchestral_tds
        )

        solo_sonatas_soup = orchestral_soup.find_next("tbody")
        works += self._scrape_simple_table(
            solo_sonatas_soup, tds_func=self._extract_solo_sonatas_tds
        )

        trio_sonatas_soup = solo_sonatas_soup.find_next("tbody")
        works += self._scrape_simple_table(
            trio_sonatas_soup, tds_func=self._extract_trio_sonatas_tds
        )

        wind_ensemble_soup = trio_sonatas_soup.find_next("tbody")
        works += self._scrape_simple_table(
            wind_ensemble_soup, tds_func=self._extract_wind_ensemble_tds
        )

        keyboard_soup = wind_ensemble_soup.find_next("tbody")
        works += self._scrape_simple_table(
            keyboard_soup, tds_func=self._extract_keyboard_tds
        )

        return works

    def _parse_date(self, date: str) -> int:
        cleaned_date = date.strip().replace("?", "")
        # parse using strptime for dates such as 25 February 1705
        try:
            t = datetime.datetime.strptime(cleaned_date, "%d %B %Y")
        except ValueError:
            # parse using strptime for dates such as 1705
            try:
                t = datetime.datetime.strptime(cleaned_date, "%Y")
            except ValueError:
                # extract a year with regular expression
                s = re.findall(r"\d{4}", cleaned_date)
                if len(s) == 0:
                    return -1
                else:
                    last = s[-1]
                    return int(last)

        return t.year

    def _scrape_simple_table(
        self, soup: BeautifulSoup | NavigableString, voice_tables=False, tds_func=None
    ) -> list[ScrapedWork]:
        works = []

        first = True
        for row in soup.find_all("tr"):
            if first:
                first = False
                continue

            tds = row.find_all("td")
            if tds_func:
                w = tds_func(tds)
            else:
                col_index_override = 2
                if voice_tables:
                    col_index_override = 3
                w = self._extract_works_from_tds(tds, date_col_index=col_index_override)
            if w is not None:
                works.append(w)

        return works

    def _extract_works_from_tds(
        self, tds: BeautifulSoup | NavigableString, date_col_index: int = 2
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        title = tds[1].text.strip()
        date = tds[date_col_index].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_concerto_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        instrument = tds[1].text.strip()
        key = tds[2].text.strip()
        date = tds[3].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"{instrument} Concerto in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_concerto_grosso_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        key = tds[1].text.strip()
        date = tds[2].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"Concerto Grosso in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_orchestral_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        type = tds[1].text.strip()
        key = tds[2].text.strip()
        date = tds[3].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"{type} in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_solo_sonatas_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        instrument = tds[1].text.strip()
        key = tds[2].text.strip()
        date = tds[3].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        if instrument == "Unspecified":
            title = f"Sonata in {key}"
        else:
            title = f"{instrument} Sonata in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_trio_sonatas_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        key = tds[1].text.strip()
        date = tds[2].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"Trio Sonata in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_wind_ensemble_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        type = tds[1].text.strip()
        key = tds[2].text.strip()
        date = tds[3].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"Wind Ensemble {type} in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )

    def _extract_keyboard_tds(
        self, tds: BeautifulSoup | NavigableString
    ) -> ScrapedWork | None:
        hwv = tds[0].text.strip()
        type = tds[1].text.strip()
        key = tds[2].text.strip()
        date = tds[3].text.strip()

        d = self._parse_date(date)
        if d == -1:
            return None

        title = f"{type} for Keyboard in {key}"

        return ScrapedWork(
            composer_firstname="George Frideric",
            composer_lastname="Handel",
            composer_fullname="George Frideric Handel",
            work_title=title.strip(),
            composition_year=d,
            opus=hwv.strip(),
            opus_number=-1,
        )
