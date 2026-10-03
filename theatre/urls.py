from django.contrib.auth.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter
from theatre.views import ActorViewSet, GenresViewSet, PlayViewSet, TheatreHallViewSet, PerformanceViewSet, \
    ReservationViewSet, TicketViewSet


router = DefaultRouter()
router.register("actors", ActorViewSet)
router.register("genres", GenresViewSet)
router.register("plays", PlayViewSet)
router.register("theatre_halls", TheatreHallViewSet )
router.register("performances", PerformanceViewSet)
router.register("reservations", ReservationViewSet)
router.register("tickets", TicketViewSet)

urlpatterns = [
    path("", include(router.urls))
]

app_name = "theatre"
