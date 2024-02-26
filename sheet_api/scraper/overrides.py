from sheet_api.scraper.scraped_work import ScrapedWork


class InvalidWork(Exception):
    pass


class SiteOverride:
    def scrape_page(self) -> list[ScrapedWork]:
        raise NotImplementedError


class OpusOverride:
    pass

    def get_opus(self, opus_number_str: str) -> tuple[str, int]:
        raise NotImplementedError


class BeethovenOpus(OpusOverride):
    def get_opus(self, opus_number_str: str):
        if "/" in opus_number_str:
            # opus is the first part, number is the second
            opus, num = opus_number_str.split("/")
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class MozartOpus(OpusOverride):
    def get_opus(self, opus_number_str: str):
        num = -1
        if "/" in opus_number_str:
            # throw out alternative K numbers
            opus = opus_number_str.split("/")[0].strip()
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class BrahmsOpus(OpusOverride):
    def get_opus(self, opus_number_str: str):
        opus_number_str = opus_number_str.replace("Op.", "")
        if "/" in opus_number_str:
            opus, num = opus_number_str.split("/")
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class SchubertOpus(OpusOverride):
    def get_opus(self, opus_number_str: str):
        opus_number_str = opus_number_str.replace("D.", "").replace("*", "")
        if "/" in opus_number_str:
            opus, num = opus_number_str.split("/")
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class TchaikovskyOpus(OpusOverride):
    def get_opus(self, opus_number_str: str):
        opus_number_str = opus_number_str.replace("//", "/")
        if "/" in opus_number_str:
            opus, num = opus_number_str.split("/")
            int(num)
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class DebussyOpus(OpusOverride):
    def get_opus(self, opus_number_str: str) -> tuple[str, int]:
        opus_number_str = opus_number_str.replace("CD", "")
        if "/" in opus_number_str:
            opus, num = opus_number_str.split("/")
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class WorksOverride:
    def get_works(self, work_title: str, opus: str) -> ScrapedWork | None:
        raise NotImplementedError


class ChopinWorks(WorksOverride):
    def get_works(self, work_title: str, opus: str) -> ScrapedWork | None:
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


class SchubertWorks(WorksOverride):
    def get_works(self, work_title: str, opus: str) -> ScrapedWork | None:
        # skip posthumous stuff
        if "Anh." in opus:
            raise InvalidWork()
        if "deest" in opus:
            raise InvalidWork()


class NameOverride:
    def get_name(self) -> str:
        raise NotImplementedError


class TchaikovskyName(NameOverride):
    def get_name(self) -> str:
        return "Pyotr Ilyich Tchaikovsky"


class DateColOverride:
    def get_date_col(self, header_col: str) -> bool:
        raise NotImplementedError


class DebussyDate(DateColOverride):
    def get_date_col(self, header_col: str) -> bool:
        return header_col == "Year"


class OpusColOverride:
    def get_opus_col(self, header_col: str) -> bool:
        raise NotImplementedError


class SchubertOpusCol(OpusColOverride):
    def get_opus_col(self, header_col: str) -> bool:
        return header_col == "D."


class DebussyOpusCol(OpusColOverride):
    def get_opus_col(self, header_col: str) -> bool:
        return header_col == "Lesure# (new)"


class RachOpusCol(OpusColOverride):
    def get_opus_col(self, header_col: str) -> bool:
        return header_col == "Op."


class DvorakOpusCol(OpusColOverride):
    def get_opus_col(self, header_col: str) -> bool:
        return header_col == "Op."


class RavelOpusCol(OpusColOverride):
    def get_opus_col(self, header_col: str) -> bool:
        return header_col == "M"


class RavelOpus(OpusOverride):
    def get_opus(self, opus_number_str: str) -> tuple[str, int]:
        opus_number_str = opus_number_str.replace("M.", "")
        if "/" in opus_number_str:
            opus, num = opus_number_str.split("/")
        else:
            opus = opus_number_str
            num = -1

        return opus.strip(), num


class PostprocessWorks:
    def postprocess(self, all_works: list[ScrapedWork]) -> list[ScrapedWork]:
        raise NotImplementedError


class Dedupe(PostprocessWorks):
    def postprocess(self, all_works: list[ScrapedWork]) -> list[ScrapedWork]:
        # there are tons of duplicate opus/titles due to arrangements for orchestra/piano
        seen = set()
        uniq = []
        for work in all_works:
            if work not in seen:
                seen.add(work)
                uniq.append(work)

        return uniq
