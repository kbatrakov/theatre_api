from datetime import datetime
from django.db.models import F
from django.db.models.aggregates import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from theatre.models import Actor, Genre, Play, TheatreHall, Performance, Reservation
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (ActorSerializer, GenreSerializer, PlaySerializer, TheatreHallSerializer, \
    PerformanceSerializer, ReservationSerializer, PlayListSerializer, PlayDetailSerializer, \
    PerformanceListSerializer, PerformanceDetailSerializer, ReservationListSerializer, ReservationDetailSerializer)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = [IsAdminOrReadOnly]


class GenresViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("title", OpenApiTypes.STR,
                                    description="Filtering plays by 'title' parameter (case insensitive)"),
            OpenApiParameter(
                       "actors",
                             type={"type": "array", "items": {"type": "integer"}},
                             explode=False,
                             description="Actors IDs split by a comma: 1, 2, 3 etc,",
                             ),
            OpenApiParameter(
                       "genres",
                             type={"type": "array", "items": {"type": "integer"}},
                             explode=False,
                             description="Genres IDs split by a comma: 1, 2, 3 etc.",
            ),
        ]
    )
)
class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.all().prefetch_related("actors", "genres")
    serializer_class = PlaySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        elif self.action == "retrieve":
            return PlayDetailSerializer
        else:
            return PlaySerializer

    @staticmethod
    def params_to_ints(qs):
        return [int(element) for element in qs.split(",")]

    def get_queryset(self):
        queryset = self.queryset

        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        if title:
            queryset = queryset.filter(title__icontains=title)

        if actors:
            actors_ids = self.params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actors_ids)

        if genres:
            genres_ids = self.params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genres_ids)

        return queryset


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset
        return queryset.annotate(
        hall_capacity=F("rows") * F("seats_in_row"))


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("play_title", OpenApiTypes.STR,
                             description="Filtering by play title."),
            OpenApiParameter("theatre_hall_name", OpenApiTypes.STR,
                             description="Filtering by name of a theatre hall."),
            OpenApiParameter("date", OpenApiTypes.DATE,
                             description="Show date, format YYYY-MM-DD"),
        ]
    )
)
class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all().select_related("play", "theatre_hall")
    serializer_class = PerformanceSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset.annotate(
            hall_capacity=F("theatre_hall__rows") * F("theatre_hall__seats_in_row"),
            occupied_seats_count=Count("tickets"),
            available_seats_count=(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row") - Count("tickets")
            )
        )

        play_title = self.request.query_params.get("play_title")
        theatre_hall_name = self.request.query_params.get("theatre_hall_name")
        date = self.request.query_params.get("date")

        if play_title:
            queryset = queryset.filter(play__title__icontains=play_title)

        if theatre_hall_name:
            queryset = queryset.filter(theatre_hall__name__icontains=theatre_hall_name)

        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError("date must be in YYYY-MM-DD format")
            queryset = queryset.filter(show_time__date=date)

        return queryset


    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        elif self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceSerializer


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReservationPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            return queryset.select_related("user").annotate(
                tickets_count=Count("tickets")
            )
        if self.action == "retrieve":
            return queryset.select_related("user").prefetch_related(
                "tickets__performance__play",
                "tickets__performance__theatre_hall",
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        if self.action == "retrieve":
            return ReservationDetailSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
