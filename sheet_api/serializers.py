from django.contrib.auth.models import User, Group
from django.db.models import Max
from rest_framework import serializers

from sheet_api.models import Puzzle, Work, Composer
from sheet_api.time_helpers import get_timezone_aware_date
from sheet_musicle_server.settings import HIDE_NEW_PUZZLES


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PuzzleSerializer(serializers.ModelSerializer):
    sequence_number = serializers.SerializerMethodField()
    is_latest = serializers.SerializerMethodField()

    class Meta:
        model = Puzzle
        fields = [
            "id",
            "date",
            "answer",
            "type",
            "sheet_image_url",
            "sequence_number",
            "is_latest",
        ]
        depth = 2

    def get_sequence_number(self, obj: Puzzle):
        return Puzzle.objects.filter(type=obj.type, date__lte=obj.date).count()

    def get_is_latest(self, obj: Puzzle):
        if HIDE_NEW_PUZZLES:
            # lie and say a puzzle with a date equal to today is the latest,
            # even if there are more puzzles in the database
            tz_date = get_timezone_aware_date()

            return obj.date == tz_date

        return (
            obj.date
            == Puzzle.objects.filter(type=obj.type).aggregate(Max("date"))["date__max"]
        )


class ComposerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Composer
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "born_year",
            "died_year",
            "last_scanned",
        ]


class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = [
            "id",
            "work_title",
            "composition_year",
            "opus",
            "opus_number",
            "composer",
            "last_scanned",
        ]


class WorkWithoutComposerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = [
            "id",
            "work_title",
            "composition_year",
            "opus",
            "opus_number",
            "last_scanned",
        ]
