from __future__ import annotations

import json
import os
import re

import requests
from bs4 import BeautifulSoup

import argparse

from django.db import IntegrityError
from django.utils import timezone

from sheet_api.models import Composer, Work
from sheet_api.scraper.custom_scrapers import HandelScraper
from sheet_api.scraper.overrides import (
    SiteOverride,
    OpusOverride,
    WorksOverride,
    NameOverride,
    OpusColOverride,
    DateColOverride,
    PostprocessWorks,
    BeethovenOpus,
    MozartOpus,
    ChopinWorks,
    BrahmsOpus,
    TchaikovskyOpus,
    TchaikovskyName,
    Dedupe,
    SchubertOpus,
    DebussyOpus,
    DebussyOpusCol,
    DebussyDate,
    RachOpusCol,
    DvorakOpusCol,
    RavelOpusCol,
    RavelOpus,
    InvalidWork,
    SchubertOpusCol,
    SchubertWorks,
)
from sheet_api.scraper.page_helpers import get_page_text
from sheet_api.scraper.scraped_work import ScrapedWork

COMPOSERS_FILE = "all_composers.json"


class InvalidComposer(Exception):
    pass


def is_opus_col(composer: str, header_col: str) -> bool:
    # some composers have different catalogs which replace opus numbers, even in the header
    try:
        opus_col_cl = config_by_composer[composer].opus_col_override
        return opus_col_cl.get_opus_col(header_col)
    except (KeyError, NotImplementedError):
        return header_col == "Opus"


def is_date_col(composer: str, header_col: str) -> bool:
    # same goes for year
    try:
        date_col_cl = config_by_composer[composer].date_col_override
        return date_col_cl.get_date_col(header_col)
    except (KeyError, NotImplementedError):
        return header_col == "Date"


class ComposerOptions:
    def __init__(
        self,
        page_override: SiteOverride = SiteOverride(),
        opus_override: OpusOverride = OpusOverride(),
        works_override: WorksOverride = WorksOverride(),
        name_override: NameOverride = NameOverride(),
        opus_col_override: OpusColOverride = OpusColOverride(),
        date_col_override: DateColOverride = DateColOverride(),
        postprocess: PostprocessWorks = PostprocessWorks(),
    ):
        self.page_override = page_override
        self.opus_override = opus_override
        self.works_override = works_override
        self.name_override = name_override
        self.opus_col_override = opus_col_override
        self.date_col_override = date_col_override
        self.postprocess = postprocess


config_by_composer: dict[str, ComposerOptions] = {
    "George Frideric Handel": ComposerOptions(page_override=HandelScraper()),
    "Ludwig van Beethoven": ComposerOptions(opus_override=BeethovenOpus()),
    "Wolfgang Amadeus Mozart": ComposerOptions(opus_override=MozartOpus()),
    "Frédéric Chopin": ComposerOptions(works_override=ChopinWorks()),
    "Johannes Brahms": ComposerOptions(opus_override=BrahmsOpus()),
    "Pyotr Tchaikovsky": ComposerOptions(
        opus_override=TchaikovskyOpus(),
        name_override=TchaikovskyName(),
        postprocess=Dedupe(),
    ),
    "Franz Schubert": ComposerOptions(
        opus_override=SchubertOpus(),
        postprocess=Dedupe(),
        opus_col_override=SchubertOpusCol(),
        works_override=SchubertWorks(),
    ),
    "Claude Debussy": ComposerOptions(
        opus_override=DebussyOpus(),
        opus_col_override=DebussyOpusCol(),
        date_col_override=DebussyDate(),
    ),
    "Sergei Rachmaninoff": ComposerOptions(
        opus_col_override=RachOpusCol(), postprocess=Dedupe()
    ),
    "Antonín Dvořák": ComposerOptions(
        opus_col_override=DvorakOpusCol(), postprocess=Dedupe()
    ),
    "Maurice Ravel": ComposerOptions(
        opus_col_override=RavelOpusCol(),
        opus_override=RavelOpus(),
    ),
}


class Parser:
    DRY_RUN_PREFIX = "[DRY_RUN]"

    def __init__(self, writes_to_db: bool = False):
        self.writes_to_db = writes_to_db
        self.composer_list = []
        self._init_composer_list()

    def _init_composer_list(self):
        with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), COMPOSERS_FILE),
            "r",
        ) as f:
            composer_list = json.loads(f.read())
            self.composer_list = composer_list

    def scrape_imslp_page(self, composer: str, page_text: str) -> list[ScrapedWork]:
        soup = BeautifulSoup(page_text, "html.parser")

        works_table = soup.find("table", {"class": "wikitable sortable"})
        # loop over the tr elements inside the tbody
        first = True
        opus_col = 0
        name_col = -1
        date_col = -1
        key_col = -1
        all_works = []
        for row in works_table.find_all("tr"):
            if first:
                headers = row.find_all("th")
                # first row is header
                # find the index of the header with "Title" as the text
                for i, header in enumerate(headers):
                    if header.text.strip() == "Title":
                        name_col = i
                    elif is_date_col(composer, header.text.strip()):
                        date_col = i
                    elif header.text.strip() == "Key":
                        key_col = i
                    elif is_opus_col(composer, header.text.strip()):
                        opus_col = i
                first = False
                continue

            tds = row.find_all("td")
            # delete display: none span from opus number
            opus_number_td = tds[opus_col]
            if opus_number_td.span:
                opus_number_td.span.decompose()

            opus_number_str = opus_number_td.text.strip()
            if opus_number_str == "":
                # skip empty opus number
                print(f"Skipping empty opus number")
                continue
            if len(tds) < name_col:
                print(f"Skipping empty row")
                continue

            if opus_number_str == "—":
                # skip no opus number
                print(f"Skipping no opus number")
                continue

            work_title = tds[name_col].text.strip()
            # process override if there are any
            try:
                work_override_cl = config_by_composer[composer].works_override
                try:
                    work_override_result = work_override_cl.get_works(
                        work_title, opus_number_str
                    )
                    if work_override_result is not None:
                        # replace whatever is in the table with handwritten result, then skip it
                        all_works.append(work_override_result)
                        continue
                except InvalidWork:
                    # skip row entirely
                    continue
            except (KeyError, NotImplementedError):
                pass

            if work_title == "":
                print(f"Skipping empty work title")
                continue
            if "(" in work_title:
                # grouping of works like Piano Trio (3), which will be scraped in upcoming rows
                if re.search("\(\d+\)", work_title):
                    continue

            try:
                # use custom function to parse opus number
                opus_func_cl = config_by_composer[composer].opus_override
                opus, num = opus_func_cl.get_opus(opus_number_str)
                num = int(num)
            except (KeyError, NotImplementedError):
                # fallback basic opus number handling
                if "/" in opus_number_str:
                    # opus is the first part, number is the second
                    opus, num = opus_number_str.split("/")
                    try:
                        int(num)
                    except ValueError:
                        print(
                            f"Skipping invalid opus number: {work_title} ({opus_number_str})"
                        )
                        continue
                else:
                    opus = opus_number_str
                    num = -1
            except ValueError:
                print(f"Skipping invalid opus number: {work_title} ({opus_number_str})")
                continue

            # clean up date
            date_str = tds[date_col].text.strip()
            if date_str == "" or date_str == "—":
                print(f"Skipping no year: {work_title}")
                continue
            elif "," in date_str:
                date = date_str.split(",")[0]
            elif "/" in date_str:
                date = date_str.split("/")[0]
            else:
                date = date_str

            if "\u2013" in date:
                # take the "start" year of composition rather than the full range
                date = date_str.split("\u2013")[0]
            if "-" in date:
                # some pages use the ascii character rather than unicode
                date = date_str.split("-")[0]

            if "before" in date:
                # same deal
                date = date_str.split("before")[0]
            elif "or" in date:
                # take the first date
                date = date_str.split("or")[0]
            elif "and" in date:
                date = date_str.split("and")[0]

            date = (
                date.replace("?", "")
                .replace("(?)", "")
                .replace("c.", "")
                .replace("ca.", "")
                .replace("after", "")
                .replace("before", "")
                .replace("post", "")
                .replace("ante", "")
                .strip()
            )

            if date == "":
                print(f"Skipping no year: {work_title}")
                continue

            if "No." in work_title:
                # if a work is only denoted by its number or is otherwise super generic, add the key to make distinguishing it a bit easier
                if re.search(".+\s*No\.\s*\d+", work_title):
                    key_text = tds[key_col].text.strip()
                    work_title += " in " + key_text
            elif (
                work_title == "Impromptu"
                or work_title == "Etude-tableau"
                or work_title == "Intermezzo"
                or work_title == "Piano Sonata"
            ):
                key_text = tds[key_col].text.strip()
                work_title += " in " + key_text

            try:
                # name override, in case imslp's name differs from what we want to display
                name_func_cl = config_by_composer[composer].name_override
                display_name = name_func_cl.get_name()
            except (KeyError, NotImplementedError):
                display_name = composer
            # naive first/last split
            firstname = display_name.split(" ")[0]
            lastname = display_name.split(" ")[-1]
            all_works.append(
                ScrapedWork(
                    composer_firstname=firstname,
                    composer_lastname=lastname,
                    composer_fullname=display_name,
                    work_title=work_title,
                    composition_year=int(date),
                    opus=opus,
                    opus_number=int(num),
                )
            )

        try:
            postprocess_cl = config_by_composer[composer].postprocess
            all_works = postprocess_cl.postprocess(all_works)
        except (KeyError, NotImplementedError):
            pass

        return all_works

    def _parse_composer_imslp(self, composer: str) -> list[ScrapedWork]:
        url = f"https://imslp.org/wiki/List_of_works_by_{composer.replace(' ', '_')}"
        text = get_page_text(url)
        print(f"Scraping IMSLP: {url}")
        return self.scrape_imslp_page(composer, text)

    def print_write_status(self):
        if self.writes_to_db:
            print("Writing to database")
        else:
            print("Dry run, not writing to database")

    def scrape_composer(self, composer: str):
        self.print_write_status()

        if composer not in self.composer_list:
            raise InvalidComposer(f"Composer not found: {composer}")

        try:
            page_cl = config_by_composer[composer].page_override
            works = page_cl.scrape_page()
        except (KeyError, NotImplementedError):
            works = self._parse_composer_imslp(composer)

        self.save_composer_works(works)

    def _parse_composer_impl(self, composer: str) -> list[ScrapedWork] | None:
        return self._parse_composer_imslp(composer)

    def scrape_all_composers(self):
        self.print_write_status()

        for composer in self.composer_list:
            print("Scraping composer: " + composer)
            try:
                page_cl = config_by_composer[composer].page_override
                works = page_cl.scrape_page()
            except (KeyError, NotImplementedError):
                works = self._parse_composer_imslp(composer)

            if works is None:
                continue

            self.save_composer_works(works)

    def save_composer_works(self, works: list[ScrapedWork]):
        print("Total works: " + str(len(works)))
        for work in works:
            if self.writes_to_db:
                composer, created = Composer.objects.get_or_create(
                    full_name=work.composer_fullname,
                    first_name=work.composer_firstname,
                    last_name=work.composer_lastname,
                )
                if created:
                    print("Added composer: " + work.composer_fullname)
            else:
                print(f"{Parser.DRY_RUN_PREFIX} Composer: {work.composer_fullname}")

            work_title = work.work_title
            if len(work.work_title) > 200:
                work_title = work.work_title[:197] + "..."
            if self.writes_to_db:
                try:
                    _, created = Work.objects.update_or_create(
                        work_title=work_title,
                        composition_year=work.composition_year,
                        opus=work.opus,
                        opus_number=work.opus_number,
                        composer=composer,
                        defaults={"last_scanned": timezone.now()},
                    )
                    if created:
                        print("Added work: " + work.work_title)
                except IntegrityError as e:
                    print("Found duplicate work, skipping: " + str(e))
            else:
                print(f"{Parser.DRY_RUN_PREFIX} Work: {work.work_title}")
                print(f"{Parser.DRY_RUN_PREFIX}\tYear: {work.composition_year}")
                print(f"{Parser.DRY_RUN_PREFIX}\tOpus: {work.opus}")
                print(f"{Parser.DRY_RUN_PREFIX}\tOpus number: {work.opus_number}")


if __name__ == "__main__":
    with open(COMPOSERS_FILE, "r") as f:
        composer_list = json.loads(f.read())

        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            "--composer",
            help="Only parse one composer",
            default=None,
        )

        argparser.add_argument(
            "--start-at",
            help="Start at this composer in the list",
            default=None,
        )

        args = argparser.parse_args()
        skip_prod_output = False

        # if we use any arg, skip production output, as it should contain all composers
        if args.composer is not None:
            composer_list = [args.composer]
            skip_prod_output = True

        if args.start_at is not None:
            composer_list = composer_list[composer_list.index(args.start_at) :]
            skip_prod_output = True

        j = 0
        all_works = []
        for composer in composer_list:
            p = Parser()
            works = p.scrape_composer(composer)
            if works is None:
                continue

            output = {
                "id": j,
                "firstname": works[0].composer_firstname,
                "lastname": works[0].composer_lastname,
                "fullname": works[0].composer_fullname,
                "works": [
                    {
                        "id": i,
                        "work_title": w.work_title,
                        "composition_year": w.composition_year,
                        "opus": w.opus,
                        "opus_number": w.opus_number,
                    }
                    for i, w in enumerate(works)
                ],
            }

            all_works.append(output)
            j += 1

            composer_filename = (
                composer.lower().replace(" ", "_").replace(".", "").replace(",", "")
            )
            filename = f"../src/assets/composer_data/{composer_filename}.json"
            with open(filename, "w") as f:
                f.write(json.dumps(output, indent=2))

        if skip_prod_output:
            print("Skipping production output")
            exit(0)

        # write version consumed by app, all composers in one file
        with open("../src/assets/parsed_composers.json", "w") as f:
            f.write(json.dumps(all_works, indent=2))
        print("Wrote output")
