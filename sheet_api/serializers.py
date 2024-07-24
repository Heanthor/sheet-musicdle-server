from django.contrib.auth.models import User, Group
from django.db.models import Max
from rest_framework import serializers

from sheet_api.models import Puzzle, Work, Composer, UsageEvent
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
            "difficulty",
            "type",
            "sheet_image_url",
            "sequence_number",
            "is_latest",
        ]
        depth = 2

    def get_sequence_number(self, obj: Puzzle):
        return Puzzle.objects.filter(type=obj.type, date__lte=obj.date).count()

    def get_is_latest(self, obj: Puzzle):
        # get all puzzles with dates greater than this puzzle
        upcoming_puzzles = Puzzle.objects.filter(
            type=obj.type, date__gt=obj.date
        ).order_by("date")
        if HIDE_NEW_PUZZLES:
            tz_date = get_timezone_aware_date()

            # if there are any puzzles which can still be shown (i.e. their date still before the current date),
            # then this is not the fake latest puzzle
            for puzzle in upcoming_puzzles:
                if puzzle.date < tz_date:
                    return False

            return True

        return len(upcoming_puzzles) == 0


class ComposerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Composer
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "catalog_prefix",
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


class UsageEventSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(required=True)
    puzzle = serializers.IntegerField(required=True)
    event_body = serializers.JSONField(required=True)

    class Meta:
        model = UsageEvent
        fields = ["event_type", "puzzle", "event_body", "session_id", "event_time"]
