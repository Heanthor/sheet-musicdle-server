import enum

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Puzzle(models.Model):
    class PuzzleType(models.TextChoices):
        PIANO = "P", _("Piano")
        VIOLIN = "V", _("Violin")
        CELLO = "C", _("Cello")
        ORCHESTRAL = "O", _("Orchestral")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type", "date"],
                name="unique_type_date",
            )
        ]

    type = models.CharField(max_length=5, choices=PuzzleType.choices)
    date = models.DateField()
    answer = models.ForeignKey("Work", on_delete=models.CASCADE)
    sheet_image_url = models.CharField(max_length=200)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        # TODO
        # get rid of this change
        # instead, make the latest puzzle endpoint return the sequence number for that category
        # when requesting a specific puzzle, calculate the date from the offset number
        # we do not need to save the sequence number in the database

        # when creating a new puzzle, increment the sequence id for puzzles of the same type
        # self.puzzle_sequence_id = (
        #     Puzzle.objects.filter(type=self.type, date__lte=self.date).count() + 1
        # )
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f"{self.date}: {self.answer}"


class Composer(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["full_name", "first_name", "last_name"],
                name="unique_full_name_first_name_last_name",
            )
        ]

    full_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    # TODO: when years are scraped, born_year should not be nullable
    born_year = models.IntegerField(blank=True, null=True)
    died_year = models.IntegerField(blank=True, null=True)

    first_scanned = models.DateTimeField(auto_now_add=True)
    last_scanned = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.full_name}"


class Work(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["work_title", "opus", "opus_number"],
                name="unique_work_title_opus_opus_number",
            )
        ]

    work_title = models.CharField(max_length=200)
    composition_year = models.IntegerField()
    opus = models.CharField(max_length=200)
    opus_number = models.IntegerField(blank=True, null=True)

    composer = models.ForeignKey("Composer", on_delete=models.CASCADE, default=None)

    first_scanned = models.DateTimeField(auto_now_add=True)
    last_scanned = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.composer.last_name}: {self.work_title} ({self.composition_year})"
