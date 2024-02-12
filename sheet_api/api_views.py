from django.contrib.auth.models import User, Group
from rest_framework import viewsets, generics, status
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Max, Min

from sheet_api.models import Puzzle, Work, Composer
from sheet_api.serializers import (
    UserSerializer,
    GroupSerializer,
    PuzzleSerializer,
    WorkSerializer,
    ComposerSerializer,
    WorkWithoutComposerSerializer,
)


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

    def get(self, request, **kwargs):
        try:
            category = self.kwargs.get("category", None)
            try:
                choice = Puzzle.PuzzleType[category.upper()]
            except KeyError:
                return Response(
                    {"detail": "Puzzle category not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            puzzle = Puzzle.objects.filter(type=choice).latest("date")

            serializer = PuzzleSerializer(puzzle, context={"request": request})

            # Return the serialized data
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Puzzle.DoesNotExist:
            return Response(
                {"detail": "Puzzle not found."}, status=status.HTTP_404_NOT_FOUND
            )
