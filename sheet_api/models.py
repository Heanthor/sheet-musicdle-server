import enum

from django.db import models
from django.utils import timezone


# Create your models here.


class PuzzleTypes(enum.Enum):
    Piano = "Piano"
    Violin = "Violin"
    Cello = "Cello"
    Orchestral = "Orchestral"


class Puzzle(models.Model):
    type = models.CharField(
        max_length=20, choices=[(tag, tag.value) for tag in PuzzleTypes]
    )
    date = models.DateField()
    answer = models.ForeignKey("Work", on_delete=models.CASCADE)
    sheet_image_url = models.CharField(max_length=200)


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
