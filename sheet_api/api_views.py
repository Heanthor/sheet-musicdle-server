import datetime

import pytz
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, generics, status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Max, Min
from silk.profiling.profiler import silk_profile

from sheet_api.models import Puzzle, Work, Composer, UsageEvent
from sheet_api.serializers import (
    UserSerializer,
    GroupSerializer,
    PuzzleSerializer,
    WorkSerializer,
    ComposerSerializer,
    WorkWithoutComposerSerializer,
    UsageEventSerializer,
)
from sheet_api.time_helpers import get_timezone_aware_date
from sheet_musicle_server.settings import HIDE_NEW_PUZZLES, SKIP_USAGE_EVENT_WRITE


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class PuzzleViewSet(viewsets.ReadOnlyModelViewSet):
    """ """

    queryset = Puzzle.objects.all()
    serializer_class = PuzzleSerializer
    permission_classes = []


class ComposerViewSet(viewsets.ReadOnlyModelViewSet):
    """ """

    queryset = Composer.objects.all()
    serializer_class = ComposerSerializer
    permission_classes = []


class WorkViewSet(viewsets.ReadOnlyModelViewSet):
    """ """

    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    permission_classes = []


class WorkFilterView(generics.ListAPIView):
    serializer_class = WorkWithoutComposerSerializer
    permission_classes = []
    authentication_classes = []

    def get_queryset(self):
        composer_id = self.kwargs.get("composer_id", None)
        if composer_id:
            queryset = Work.objects.filter(composer_id=composer_id)
        else:
            queryset = Work.objects.all()

        return queryset


class ComposerWorkRangeView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request, **kwargs):
        composer_id = kwargs.get("composer_id", None)
        works_agg = Work.objects.filter(composer_id=composer_id).aggregate(
            Min("composition_year"), Max("composition_year")
        )

        return Response(
            {
                "min": works_agg["composition_year__min"],
                "max": works_agg["composition_year__max"],
            }
        )


class LatestPuzzleByCategoryView(APIView):
    permission_classes = []
    authentication_classes = []

    # @silk_profile(name="LatestPuzzleByCategoryView")
    def get(self, request, **kwargs):
        try:
            category = self.kwargs.get("category", None)
            try:
                choice = Puzzle.PuzzleType[category.upper()]
            except KeyError:
                return Response(
                    {"detail": "Invalid puzzle category"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # use user-supplied timezone if valid, otherwise use US eastern time
            timezone = self.request.query_params.get("timezone", None)
            now_date = get_timezone_aware_date(timezone)

            # get the latest puzzle with a date before or equal to today
            puzzle = Puzzle.objects.filter(type=choice, date__lte=now_date).latest(
                "date"
            )

            serializer = PuzzleSerializer(puzzle, context={"request": request})

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Puzzle.DoesNotExist:
            return Response(
                {"detail": "Puzzle not found."}, status=status.HTTP_404_NOT_FOUND
            )


class PuzzleBySequenceNumberView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request, **kwargs):
        try:
            category = self.kwargs.get("category", None)
            sequence_number = self.kwargs.get("sequence_number", None)
            if not sequence_number:
                return Response(
                    {"detail": "Sequence number is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                choice = Puzzle.PuzzleType[category.upper()]
            except KeyError:
                return Response(
                    {"detail": "Invalid puzzle category"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            no_puzzle_found_response = Response(
                {"detail": "No puzzle found for sequence number"},
                status=status.HTTP_404_NOT_FOUND,
            )
            try:
                puzzle = Puzzle.objects.filter(type=choice).order_by("date")[
                    int(sequence_number) - 1
                ]
            except IndexError:
                return no_puzzle_found_response

            if HIDE_NEW_PUZZLES:
                # do not allow puzzles for dates after today to be returned
                timezone = self.request.query_params.get("timezone", None)
                now_date = get_timezone_aware_date(timezone)

                if puzzle.date > now_date:
                    return no_puzzle_found_response

            serializer = PuzzleSerializer(puzzle, context={"request": request})

            data = serializer.data
            # Return the serialized data
            return Response(data, status=status.HTTP_200_OK)
        except Puzzle.DoesNotExist:
            return Response(
                {"detail": "Puzzle not found."}, status=status.HTTP_404_NOT_FOUND
            )


class UsageEventView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = UsageEventSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            event_type = data["event_type"]
            event_body = data["event_body"]
            puzzle = data["puzzle"]
            session_id = data.get("session_id", None)

            try:
                event_type_choice = UsageEvent.EventType[event_type.upper()]
            except KeyError:
                return Response(
                    {"detail": "Invalid event type"}, status=status.HTTP_400_BAD_REQUEST
                )

            if not Puzzle.objects.filter(id=puzzle).exists():
                return Response(
                    {"detail": "Puzzle not found"}, status=status.HTTP_404_NOT_FOUND
                )

            if SKIP_USAGE_EVENT_WRITE:
                print(
                    f"Got usage event: {event_type_choice} for puzzle {puzzle}: {session_id} - {event_body}"
                )
            else:
                UsageEvent.objects.create(
                    event_type=event_type_choice,
                    puzzle_id=puzzle,
                    event_body=event_body,
                    session_id=session_id,
                )

            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
