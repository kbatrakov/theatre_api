from django.db import models
from theatre_api_service import settings


class Actor(models.Model):
    first_name = models.CharField(max_length=128, blank=False)
    last_name = models.CharField(max_length=128, blank=False)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=128, blank=False, unique=True)

    def __str__(self):
        return self.name


class Play(models.Model):
    title = models.CharField(max_length=128, blank=False)
    description = models.TextField(blank=True)
    actors = models.ManyToManyField(Actor, related_name="plays")
    genres = models.ManyToManyField(Genre, related_name="plays")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class TheatreHall(models.Model):
    name = models.CharField(max_length=128, blank=False)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


    @property
    def capacity(self):
        return self.rows * self.seats_in_row


class Performance(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE, related_name="performances", blank=False)
    theatre_hall = models.ForeignKey(TheatreHall, on_delete=models.CASCADE, related_name="performances", blank=False)
    show_time = models.DateTimeField()

    class Meta:
        ordering = ["-show_time"]

    def __str__(self):
        return f"{self.play.title} - {self.show_time}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="reservations")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation at {self.created_at}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, related_name="tickets", blank=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="tickets", blank=False)

    class Meta:
        unique_together = ["row", "seat", "performance"]
        ordering = ["row", "seat"]

    def __str__(self):
        return f"{self.performance} — row {self.row}, seat {self.seat}"
