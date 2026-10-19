import threading
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from theatre.models import TheatreHall, Performance, Ticket, Reservation, Play
from datetime import timedelta


RESERVATION_LIST_URL = reverse("theatre:reservation-list")
PERFORMANCE_LIST_URL = reverse("theatre:performance-list")


def reservation_detail_url(pk):
    return reverse("theatre:reservation-detail", args=[pk])


def sample_user(**params):
    defaults = {"email": "user_test@test.com", "password": "User_password_123"}
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def sample_hall(**params):
    defaults = {"name": "Main hall", "rows": 3, "seats_in_row": 4}
    defaults.update(params)

    return TheatreHall.objects.create(**defaults)


def sample_play(**params):
    defaults = {"title": "Sample play", "description": "Fun to watch!"}
    defaults.update(params)

    return Play.objects.create(**defaults)


def sample_performance(play=None, hall=None, show_time=None, **params):
    return Performance.objects.create(
        play=play or sample_play(),
        theatre_hall=hall or sample_hall(),
        show_time=show_time or timezone.now() + timedelta(days=1),
        **params,
    )


class ReservationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.hall = sample_hall(rows=2, seats_in_row=2)  # 4 места
        self.performance = sample_performance(hall=self.hall)

    def _payload(self, *seats):
        return {
            "tickets": [
                {"row": r, "seat": s, "performance": self.performance.id}
                for r, s in seats
            ]
        }

    def _reserve(self, *seats):
        return self.client.post(
            RESERVATION_LIST_URL, self._payload(*seats), format="json"
        )

    def test_create_reservation(self):
        response = self._reserve((1, 1))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_duplicate_seat_in_same_request_rejected(self):
        response = self._reserve((1, 1), (1, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_already_taken_seat_rejected(self):
        self._reserve((1, 1))
        response = self._reserve((1, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_taken_seat_by_another_user_rejected(self):
        other = sample_user(email="other@test.com")
        other_client = APIClient()
        other_client.force_authenticate(user=other)
        other_client.post(RESERVATION_LIST_URL, self._payload((1, 1)), format="json")

        response = self._reserve((1, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_seat_other_performance_allowed(self):
        other_perf = sample_performance(hall=self.hall, play=sample_play(title="Other"))
        self._reserve((1, 1))
        response = self.client.post(
            RESERVATION_LIST_URL,
            {"tickets": [{"row": 1, "seat": 1, "performance": other_perf.id}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_row_out_of_range_rejected(self):
        response = self._reserve((3, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_seat_out_of_range_rejected(self):
        response = self._reserve((1, 3))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_row_or_seat_rejected(self):
        self.assertEqual(self._reserve((0, 1)).status_code, 400)
        self.assertEqual(self._reserve((1, 0)).status_code, 400)

    def test_empty_tickets_rejected(self):
        response = self.client.post(
            RESERVATION_LIST_URL, {"tickets": []}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_performance_rejected(self):
        response = self.client.post(
            RESERVATION_LIST_URL,
            {"tickets": [{"row": 1, "seat": 1, "performance": 99999}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_fully_booked_performance_rejects_new_reservation(self):
        response = self._reserve((1, 1), (1, 2), (2, 1), (2, 2))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self._reserve((1, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ticket.objects.count(), 4)

    def test_fully_booked_performance_shows_zero_available(self):
        self._reserve((1, 1), (1, 2), (2, 1), (2, 2))
        response = self.client.get(PERFORMANCE_LIST_URL)

        self.assertEqual(response.data[0]["available_seats_count"], 0)

    def test_partial_failure_is_atomic(self):
        self._reserve((1, 1))
        response = self._reserve((1, 2), (1, 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_unauthenticated_cannot_reserve(self):
        response = APIClient().post(
            RESERVATION_LIST_URL, self._payload((1, 1)), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_reservations(self):
        self._reserve((1, 1))
        other_client = APIClient()
        other_client.force_authenticate(user=sample_user(email="other@test.com"))
        response = other_client.get(RESERVATION_LIST_URL)

        self.assertEqual(response.data["count"], 0)


class ReservationUpdateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.hall = sample_hall(rows=2, seats_in_row=2)
        self.performance = sample_performance(hall=self.hall)

        self.reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1, seat=1, performance=self.performance, reservation=self.reservation
        )

    def _ticket(self, row, seat):
        return {"row": row, "seat": seat, "performance": self.performance.id}

    def test_update_to_free_seat(self):
        response = self.client.put(
            reservation_detail_url(self.reservation.id),
            {"tickets": [self._ticket(2, 2)]},
            format="json",
        )
        self.assertIn(
            response.status_code, (status.HTTP_200_OK,
                                   status.HTTP_405_METHOD_NOT_ALLOWED)
        )
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(self.reservation.tickets.count(), 1)
            self.assertTrue(
                self.reservation.tickets.filter(row=2, seat=2).exists()
            )

    def test_update_to_taken_seat_rejected(self):
        other = Reservation.objects.create(user=sample_user(email="o@test.com"))
        Ticket.objects.create(
            row=2, seat=2, performance=self.performance, reservation=other
        )
        response = self.client.put(
            reservation_detail_url(self.reservation.id),
            {"tickets": [self._ticket(2, 2)]},
            format="json",
        )
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response.status_code, 500)

    def test_update_does_not_create_duplicates(self):
        self.client.put(
            reservation_detail_url(self.reservation.id),
            {"tickets": [self._ticket(1, 1)]},
            format="json",
        )
        self.assertEqual(
            Ticket.objects.filter(
                performance=self.performance, row=1, seat=1
            ).count(),
            1,
        )

    def test_cannot_update_someone_else_reservation(self):
        other_client = APIClient()
        other_client.force_authenticate(user=sample_user(email="o@test.com"))
        response = other_client.put(
            reservation_detail_url(self.reservation.id),
            {"tickets": [self._ticket(2, 2)]},
            format="json",
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND,
             status.HTTP_405_METHOD_NOT_ALLOWED),
        )


class ConcurrentReservationTest(TransactionTestCase):
    def setUp(self):
        self.user = sample_user()
        self.hall = sample_hall(rows=1, seats_in_row=1)
        self.performance = sample_performance(hall=self.hall)

    def test_two_parallel_requests_for_same_seat_create_one_ticket(self):
        results = []

        def reserve():
            client = APIClient()
            client.force_authenticate(user=self.user)
            try:
                response = client.post(
                    RESERVATION_LIST_URL,
                    {"tickets": [
                        {"row": 1, "seat": 1, "performance": self.performance.id}
                    ]},
                    format="json",
                )
                results.append(response.status_code)
            finally:
                connection.close()

        threads = [threading.Thread(target=reserve) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(results.count(status.HTTP_201_CREATED), 1)
        self.assertNotIn(500, results)
