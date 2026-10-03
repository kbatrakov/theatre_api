from django.contrib import admin
from theatre.models import (
    Play, Performance, TheatreHall,
    Actor, Genre, Ticket, Reservation
    )

models = [Play, Performance, TheatreHall,
    Actor, Genre, Ticket, Reservation]

for model in models:
    admin.site.register(model)
