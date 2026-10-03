from theatre_app.models import (
    Play, Performance, TheatreHall,
    Actor, Genre, Ticket, Reservation
    )
from rest_framework import serializers


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["first_name", "last_name"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        mode = Genre
        fields = ["name"]


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = [
            "title",
            "description",
            "actors",
            "genres"
        ]


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = [
            "name",
            "rows",
            "seats_in_row"
        ]


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = [
            "play",
            "theatre_hall",
            "show_time"
        ]


class Reservation(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "created_at",
            "user"
        ]


class Ticket(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "row",
            "seat",
            "performance",
            "reservation"
        ]
