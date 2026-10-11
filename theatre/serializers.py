from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import ValidationError
from theatre.models import (
    Play,
    Performance,
    TheatreHall,
    Actor,
    Genre,
    Ticket,
    Reservation,
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
        fields = ["id", "title", "description", "actors", "genres", "image"]


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(
        slug_field="full_name", many=True, read_only=True
    )
    genres = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)


class PlayDetailSerializer(PlaySerializer):
    actors = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ["id", "title", "description", "actors", "genres", "image"]


class TheatreHallSerializer(serializers.ModelSerializer):
    hall_capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = TheatreHall
        fields = ["id", "name", "rows", "seats_in_row", "hall_capacity"]


class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = ["id", "play", "theatre_hall", "show_time"]


class PerformanceListSerializer(PerformanceSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
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
            "available_seats_count",
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
            "available_seats_count",
        ]


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email"]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "performance"]

    def validate(self, attrs):
        data = super().validate(attrs)
        hall = attrs["performance"].theatre_hall
        if not 1 <= attrs["row"] <= hall.rows:
            raise ValidationError({"row": f"row must be in range 1..{hall.rows}"})
        if not 1 <= attrs["seat"] <= hall.seats_in_row:
            raise ValidationError(
                {"seat": f"seat must be in range 1..{hall.seats_in_row}"}
            )
        return data


class TicketListSerializer(serializers.ModelSerializer):
    performance = PerformanceListSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "performance"]


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "tickets"]
        read_only_fields = ["created_at"]

    def validate_tickets(self, tickets):
        seen = set()
        for t in tickets:
            key = (t["performance"].id, t["row"], t["seat"])
            if key in seen:
                raise ValidationError("Duplicate seats in one reservation")
            seen.add(key)
        return tickets

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        with transaction.atomic():
            reservation = Reservation.objects.create(**validated_data)
            Ticket.objects.bulk_create(
                [Ticket(reservation=reservation, **t) for t in tickets_data]
            )
        return reservation


class ReservationListSerializer(serializers.ModelSerializer):
    reserved_by = serializers.CharField(source="user.get_full_name", read_only=True)
    tickets_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "reserved_by", "tickets_count"]


class ReservationDetailSerializer(serializers.ModelSerializer):
    reserved_by_user = UserInfoSerializer(source="user", read_only=True)
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "created_at", "reserved_by_user", "tickets"]
