from __future__ import annotations

import json
from dataclasses import dataclass
import re

import requests
from bs4 import BeautifulSoup

import argparse

COMPOSERS_FILE = "composers.json"


class InvalidWork(Exception):
    pass


@dataclass
class ScrapedWork:
    composer_firstname: str
    composer_lastname: str
    composer_fullname: str
    work_title: str
    composition_year: int
    opus: str
    opus_number: int

    def __hash__(self) -> int:
        # purposefully omit composition year
        # because sometimes otherwise identical arrangements
        # were composed in different years
        return hash(
            (
                self.composer_firstname,
                self.composer_lastname,
                self.composer_fullname,
                self.work_title,
                self.opus,
                self.opus_number,
            )
        )

    def __eq__(self, __value: object) -> bool:
        # same as above
        if not isinstance(__value, ScrapedWork):
            return NotImplemented
        return (
            self.composer_firstname == __value.composer_firstname
            and self.composer_lastname == __value.composer_lastname
            and self.composer_fullname == __value.composer_fullname
            and self.work_title == __value.work_title
            and self.opus == __value.opus
            and self.opus_number == __value.opus_number
        )


def beethoven_opus(opus_number_str: str):
    if "/" in opus_number_str:
        # opus is the first part, number is the second
        opus, num = opus_number_str.split("/")
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def mozart_opus(opus_number_str: str):
    num = -1
    if "/" in opus_number_str:
        # throw out alternative K numbers
        opus = opus_number_str.split("/")[0].strip()
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def brahms_opus(opus_number_str: str):
    opus_number_str = opus_number_str.replace("Op.", "")
    if "/" in opus_number_str:
        opus, num = opus_number_str.split("/")
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def schubert_opus(opus_number_str: str):
    opus_number_str = opus_number_str.replace("Op.", "").replace("*", "")
    if "/" in opus_number_str:
        opus, num = opus_number_str.split("/")
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def chopin_override(work_title: str) -> ScrapedWork | None:
    if work_title == "E♭ major" or work_title == "G major":
        # rowspan breaks the table for andante spinato
        raise InvalidWork()
    if work_title == "Andante spianato et Grande polonaise brillante":
        return ScrapedWork(
            composer_firstname="Frédéric",
            composer_lastname="Chopin",
            composer_fullname="Frédéric Chopin",
            work_title="Andante spianato et Grande polonaise brillante",
            composition_year=1834,
            opus="22",
            opus_number=-1,
        )

    return None


def tchaikovsky_opus(opus_number_str: str):
    opus_number_str = opus_number_str.replace("//", "/")
    if "/" in opus_number_str:
        opus, num = opus_number_str.split("/")
        int(num)
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def tchaikovsky_name() -> str:
    return "Pyotr Ilyich Tchaikovsky"


def dedupe_postprocess(all_works: list[ScrapedWork]) -> list[ScrapedWork]:
    # there are tons of duplicate opus/titles due to arrangements for orchestra/piano
    seen = set()
    uniq = []
    for work in all_works:
        if work not in seen:
            seen.add(work)
            uniq.append(work)

    return uniq


def debussy_opus_col(header_col: str) -> bool:
    return header_col == "Lesure# (new)"


def debussy_date_col(header_col: str) -> bool:
    return header_col == "Year"


def debussy_opus(opus_number_str: str):
    opus_number_str = opus_number_str.replace("CD", "")
    if "/" in opus_number_str:
        opus, num = opus_number_str.split("/")
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def rach_opus_col(header_col: str) -> bool:
    return header_col == "Op."


def dvorak_opus_col(header_col: str) -> bool:
    return header_col == "Op."


def ravel_opus_col(header_col: str) -> bool:
    return header_col == "M"


def ravel_opus(opus_number_str: str):
    opus_number_str = opus_number_str.replace("M.", "")
    if "/" in opus_number_str:
        opus, num = opus_number_str.split("/")
    else:
        opus = opus_number_str
        num = -1

    return opus.strip(), num


def is_opus_col(composer: str, header_col: str) -> bool:
    # some composers have different catalogs which replace opus numbers, even in the header
    try:
        opus_col_func = config_by_composer[composer]["opus_col_func"]
        return opus_col_func(header_col)
    except KeyError:
        return header_col == "Opus"


def is_date_col(composer: str, header_col: str) -> bool:
    # same goes for year
    try:
        date_col_func = config_by_composer[composer]["date_col_func"]
        return date_col_func(header_col)
    except KeyError:
        return header_col == "Date"


config_by_composer = {
    "Ludwig van Beethoven": {"opus_func": beethoven_opus},
    "Wolfgang Amadeus Mozart": {"opus_func": mozart_opus},
    "Frédéric Chopin": {"work_override": chopin_override},
    "Johannes Brahms": {"opus_func": brahms_opus},
    "Pyotr Tchaikovsky": {
        "opus_func": tchaikovsky_opus,
        "postprocess": dedupe_postprocess,
        "name": tchaikovsky_name,
    },
    "Franz Schubert": {"opus_func": schubert_opus, "postprocess": dedupe_postprocess},
    "Claude Debussy": {
        "opus_col_func": debussy_opus_col,
        "date_col_func": debussy_date_col,
        "opus_func": debussy_opus,
    },
    "Sergei Rachmaninoff": {
        "opus_col_func": rach_opus_col,
        "postprocess": dedupe_postprocess,
    },
    "Antonín Dvořák": {
        "opus_col_func": rach_opus_col,
        "postprocess": dedupe_postprocess,
    },
    "Maurice Ravel": {"opus_col_func": rach_opus_col, "opus_func": ravel_opus},
}


def scrape_imslp_page(composer: str, page_text: str) -> list[ScrapedWork]:
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
            work_override = config_by_composer[composer]["work_override"]
            try:
                work_override_result = work_override(work_title)
                if work_override_result is not None:
                    # replace whatever is in the table with handwritten result, then skip it
                    all_works.append(work_override_result)
                    continue
            except InvalidWork:
                # skip row entirely
                continue
        except KeyError:
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
            opus_func = config_by_composer[composer]["opus_func"]
            opus, num = opus_func(opus_number_str)
            num = int(num)
        except KeyError:
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
            .replace("c.", "")
            .replace("ca.", "")
            .replace("after", "")
            .replace("before", "")
            .replace("post", "")
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
        ):
            key_text = tds[key_col].text.strip()
            work_title += " in " + key_text

        try:
            # name override, in case imslp's name differs from what we want to display
            name_func = config_by_composer[composer]["name"]
            display_name = name_func()
        except KeyError:
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
        postprocess = config_by_composer[composer]["postprocess"]
        all_works = postprocess(all_works)
    except KeyError:
        pass

    return all_works


def parse_composer_imslp(composer: str) -> list[ScrapedWork]:
    url = f"https://imslp.org/wiki/List_of_works_by_{composer.replace(' ', '_')}"
    print("Requesting IMSLP...")
    try_imslp = requests.get(url)
    print("Got response.")
    status = try_imslp.status_code
    if status == 404:
        print(f"Composer not found: {composer}")
        return

    if status != 200:
        raise Exception(f"Status ({status}) loading page: {url}")

    print(f"Scraping IMSLP: {url}")
    return scrape_imslp_page(composer, try_imslp.text)


def parse_composer(composer: str) -> list[ScrapedWork] | None:
    return parse_composer_imslp(composer)


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
            works = parse_composer(composer)
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
