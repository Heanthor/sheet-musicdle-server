from dataclasses import dataclass


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
