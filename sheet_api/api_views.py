from django.contrib.auth.models import User, Group
from rest_framework import viewsets, generics
from rest_framework import permissions

from sheet_api.models import Puzzle, Work, Composer
from sheet_api.serializers import (
    UserSerializer,
    GroupSerializer,
    PuzzleSerializer,
    WorkSerializer,
    ComposerSerializer,
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
    serializer_class = WorkSerializer

    def get_queryset(self):
        composer_id = self.kwargs.get("composer_id", None)
        if composer_id:
            queryset = Work.objects.filter(composer_id=composer_id)
        else:
            queryset = Work.objects.all()

        return queryset
