from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
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


SEATS_TAKEN_MESSAGE = "One or more selected seats are already taken."


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

    def validate(self, attrs):
        instance = Performance(**attrs)

        try:
            instance.clean()
        except ValidationError as e:
            if hasattr(e, "message_dict"):
                raise serializers.ValidationError(e.message_dict)

            raise serializers.ValidationError({"non_field_errors": e.messages})

        return attrs


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

    @staticmethod
    def _validate_availability(tickets_data, performances):
        requested = [
            (ticket["performance"].id, ticket["row"], ticket["seat"])
            for ticket in tickets_data
        ]
        if len(requested) != len(set(requested)):
            raise serializers.ValidationError(
                {"tickets": "Duplicated seats in the request."}
            )

        sold_count = dict(
            Ticket.objects.filter(performance_id__in=performances.keys())
            .order_by()
            .values("performance_id")
            .annotate(total=Count("id"))
            .values_list("performance_id", "total")

        )

        for perf_id, performance in performances.items():
            if sold_count.get(perf_id, 0) >= performance.theatre_hall.capacity:
                raise serializers.ValidationError(
                    {"tickets": f"Performance {perf_id} is fully booked."}
                )

        query = Q()
        for perf_id, row, seat in requested:
            query |= Q(performance_id=perf_id, row=row, seat=seat)

        unavailable = list(
            Ticket.objects.filter(query)
            .order_by("performance_id", "row", "seat")
            .values_list("performance_id", "row", "seat")
        )

        if unavailable:
            seats = ", ".join(
                f"row {row}, seat {seat} (performance {perf})"
                for perf, row, seat in unavailable
            )

            raise serializers.ValidationError(
                {"tickets": f"Seats already taken: {seats}."}
            )

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets")
        performance_ids = sorted({ticket["performance"].id for ticket in tickets_data})

        try:
            with transaction.atomic():
                performances = {
                    p.id: p
                    for p in Performance.objects.select_for_update(of=("self", ))
                    .select_related("theatre_hall")
                    .filter(id__in=performance_ids)
                    .order_by("id")
                }
                self._validate_availability(tickets_data, performances=performances)

                reservation = Reservation.objects.create(**validated_data)
                Ticket.objects.bulk_create(
                    [Ticket(reservation=reservation, **ticket)
                     for ticket in tickets_data]
                )
        except IntegrityError:
            raise serializers.ValidationError({"tickets": SEATS_TAKEN_MESSAGE})

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
