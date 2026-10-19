from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from theatre.models import TheatreHall, Play, Performance
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.test import TestCase


PERFORMANCE_LIST_URL = reverse("theatre:performance-list")


def sample_admin(**params):
    defaults = {"email": "test_admin@test.com", "password": "Admin_password_1234"}
    defaults.update(params)

    return get_user_model().objects.create_superuser(**defaults)


def sample_play(**params):
    defaults = {"title": "Sample play", "description": "Fun to watch!"}
    defaults.update(params)

    return Play.objects.create(**defaults)


def sample_hall(**params):
    defaults = {"name": "Main hall", "rows": 3, "seats_in_row": 4}
    defaults.update(params)

    return TheatreHall.objects.create(**defaults)


def sample_performance(play=None, hall=None, show_time=None, **params):
    return Performance.objects.create(
        play=play or sample_play(),
        theatre_hall=hall or sample_hall(),
        show_time=show_time or timezone.now() + timedelta(days=1),
        **params,
    )


class PerformanceOverlapTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_admin())
        self.hall = sample_hall()
        self.play = sample_play()
        self.start = timezone.now() + timedelta(days=1)
        sample_performance(play=self.play, hall=self.hall, show_time=self.start)

    def _post(self, show_time, hall=None):
        return self.client.post(
            PERFORMANCE_LIST_URL,
            {
                "play": self.play.id,
                "theatre_hall": (hall or self.hall).id,
                "show_time": show_time.isoformat(),
            },
            format="json",
        )

    def test_same_time_same_hall_rejected(self):
        response = self._post(self.start)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_time_same_hall_rejected(self):
        response = self._post(self.start + timedelta(minutes=30))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_time_other_hall_allowed(self):
        other = sample_hall(name="Second hall")
        response = self._post(self.start, hall=other)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_non_overlapping_same_hall_allowed(self):
        response = self._post(self.start + timedelta(days=1))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_only_one_performance_saved_after_rejection(self):
        self._post(self.start)

        self.assertEqual(Performance.objects.count(), 1)
