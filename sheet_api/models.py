import enum

from django.db import models

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
    answer = models.ForeignKey("ComposerWork", on_delete=models.CASCADE)
    sheet_image_url = models.CharField(max_length=200)


class ComposerWork(models.Model):
    composer = models.ForeignKey("Composer", on_delete=models.CASCADE)
    work = models.ForeignKey("Work", on_delete=models.CASCADE)


class Composer(models.Model):
    full_name = models.CharField(max_length=200)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    born_year = models.IntegerField()
    died_year = models.IntegerField(blank=True, null=True)


class Work(models.Model):
    work_title = models.CharField(max_length=200)
    composition_year = models.IntegerField()
    opus = models.CharField(max_length=200)
    opus_number = models.IntegerField(blank=True, null=True)
