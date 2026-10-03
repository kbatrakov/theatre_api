from django.contrib.auth import get_user_model

from theatre.models import (
    Play, Performance, TheatreHall,
    Actor, Genre, Ticket, Reservation
    )
from rest_framework import serializers


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "first_name", "last_name"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = [
            "id",
            "title",
            "description",
            "actors",
            "genres"
        ]


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(slug_field="full_name", many=True, read_only=True)
    genres = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)


class PlayDetailSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = [
            "id",
            "title",
            "description",
            "actors",
            "genres"
        ]


class TheatreHallSerializer(serializers.ModelSerializer):
    hall_capacity = serializers.IntegerField(read_only=True)
    class Meta:
        model = TheatreHall
        fields = [
            "id",
            "name",
            "rows",
            "seats_in_row",
            "hall_capacity"
        ]


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = [
            "id",
            "play",
            "theatre_hall",
            "show_time"
        ]


class PerformanceListSerializer(PerformanceSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    hall_capacity = serializers.IntegerField(read_only=True)
    occupied_seats_count = serializers.IntegerField(read_only=True)
    available_seats_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Performance
        fields = [
            "id",
            "play_title",
            "theatre_hall_name",
            "hall_capacity",
            "show_time",
            "occupied_seats_count",
            "available_seats_count"
        ]


class PerformanceDetailSerializer(PerformanceSerializer):
    play = PlayDetailSerializer(many=False, read_only=True)
    theatre_hall = TheatreHallSerializer(many=False, read_only=True)
    hall_capacity = serializers.IntegerField(read_only=True)
    occupied_seats_count = serializers.IntegerField(read_only=True)
    available_seats_count = serializers.IntegerField(read_only=True)


    class Meta:
        model = Performance
        fields = [
            "id",
            "play",
            "theatre_hall",
            "hall_capacity",
            "show_time",
            "occupied_seats_count",
            "available_seats_count"
        ]


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "full_name",
            "email"
        ]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "created_at",
            "user"
        ]


class ReservationListSerializer(ReservationSerializer):
    reserved_by = serializers.CharField(source="user.full_name")
    class Meta:
        model = Reservation
        fields = [
            "id",
            "created_at",
            "reserved_by"
        ]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "row",
            "seat",
            "performance",
            "reservation"
        ]


class TicketListSerializer(serializers.ModelSerializer):
    performance = PerformanceListSerializer(read_only=True)
    reservation = ReservationListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "row",
            "seat",
            "performance",
            "reservation"
        ]


class ReservationDetailSerializer(serializers.ModelSerializer):
    reserved_by_user = UserInfoSerializer(source="user", read_only=True)
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "created_at",
            "reserved_by_user",
            "tickets"
        ]


class TicketDetailSerializer(serializers.ModelSerializer):
    performance = PerformanceDetailSerializer(read_only=True)
    reservation = ReservationListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "row",
            "seat",
            "performance",
            "reservation"
        ]
