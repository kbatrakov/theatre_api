from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from theatre.models import TheatreHall


HALL_LIST_URL = reverse("theatre:theatrehall-list")


def sample_admin(**params):
    defaults = {"email": "test_admin@test.com", "password": "Admin_password_1234"}
    defaults.update(params)

    return get_user_model().objects.create_superuser(**defaults)


class TheatreHallValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_admin())

    def _post(self, **overrides):
        payload = {"name": "Hall", "rows": 5, "seats_in_row": 10}
        payload.update(overrides)

        return self.client.post(HALL_LIST_URL, payload, format="json")

    def test_create_hall_valid(self):
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)

    def test_zero_rows_rejected(self):
        self.assertEqual(self._post(rows=0).status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_rows_rejected(self):
        self.assertEqual(self._post(rows=-1).status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_seats_rejected(self):
        self.assertEqual(
            self._post(seats_in_row=0).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_negative_seats_rejected(self):
        self.assertEqual(
            self._post(seats_in_row=-5).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_invalid_hall_not_saved(self):
        self._post(rows=0)
        self.assertEqual(TheatreHall.objects.count(), 0)
