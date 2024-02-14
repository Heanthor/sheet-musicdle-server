from django.contrib.auth.models import User, Group
from rest_framework import serializers

from sheet_api.models import Puzzle, Work, Composer


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

    class Meta:
        model = Puzzle
        fields = ["id", "date", "answer", "sheet_image_url", "sequence_number"]
        depth = 2

    def get_sequence_number(self, obj: Puzzle):
        return Puzzle.objects.filter(type=obj.type, date__lte=obj.date).count()


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
