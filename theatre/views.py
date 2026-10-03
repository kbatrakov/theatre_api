from django.db.models import F
from django.db.models.aggregates import Count
from rest_framework import viewsets
from theatre.models import Actor, Genre, Play, TheatreHall, Performance, Reservation, Ticket
from theatre.serializers import ActorSerializer, GenreSerializer, PlaySerializer, TheatreHallSerializer, \
    PerformanceSerializer, ReservationSerializer, TicketSerializer, PlayListSerializer, PlayDetailSerializer, \
    PerformanceListSerializer, PerformanceDetailSerializer, ReservationListSerializer, ReservationDetailSerializer, \
    TicketListSerializer, TicketDetailSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class GenresViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.all()
    serializer_class = PlaySerializer

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        elif self.action == "retrieve":
            return PlayDetailSerializer
        else:
            return PlaySerializer


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer

    def get_queryset(self):
        return TheatreHall.objects.all().annotate(
        hall_capacity=F("rows") * F("seats_in_row"))


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.all()
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        return (
            Performance.objects
            .select_related("play", "theatre_hall")
            .annotate(
                hall_capacity=F("theatre_hall__rows") * F("theatre_hall__seats_in_row"),
                occupied_seats_count=Count("tickets"),
                available_seats_count=(
                    F("theatre_hall__rows") * F("theatre_hall__seats_in_row") - Count("tickets")
                )
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        elif self.action == "retrieve":
            return PerformanceDetailSerializer
        return PerformanceSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        elif self.action == "retrieve":
            return ReservationDetailSerializer
        return ReservationSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        elif self.action == "retrieve":
            return TicketDetailSerializer
        return TicketSerializer
