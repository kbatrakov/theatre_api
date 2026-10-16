from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from theatre.models import Actor, Play, Genre
from theatre.serializers import PlayListSerializer, PlayDetailSerializer

PLAY_LIST_URL = reverse("theatre:play-list")
PERFORMANCE_LIST_URL = reverse("theatre:performance-list")


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


def sample_user(**params):
    defaults = {"email": "user_test@test.com", "password": "User_password_123"}
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def sample_admin(**params):
    defaults = {"email": "test_admin@test.com", "password": "Admin_password_1234"}
    defaults.update(params)

    return get_user_model().objects.create_superuser(**defaults)


def sample_actor(**params):
    defaults = {"first_name": "Johnny", "last_name": "Depp"}
    defaults.update(params)
    return Actor.objects.create(**defaults)


def sample_genre(**params):
    defaults = {"name": "Drama"}
    defaults.update(params)
    return Genre.objects.create(**defaults)


def sample_play(actors=None, genres=None, **params):
    defaults = {"title": "Sample play", "description": "Fun to watch!"}
    defaults.update(params)
    play = Play.objects.create(**defaults)
    if actors:
        play.actors.set(actors)
    if genres:
        play.genres.set(genres)
    return play


class PlayPublicAccessTest(TestCase):

    def test_unauthorized_check(self):
        response = self.client.get(PLAY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PlayPrivateAccessTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_user())

    def test_authorized_check(self):
        response = self.client.get(PLAY_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PlayListRetrieveTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_user())

        actor = sample_actor()
        actor_1 = sample_actor(first_name="Emilia", last_name="Watson")
        actor_2 = sample_actor(first_name="Kirsten", last_name="Dunst")
        actor_3 = sample_actor(first_name="Keanu", last_name="Reeves")
        drama = sample_genre()
        comedy = sample_genre(name="Comedy")

        self.play_1 = sample_play(
            title="Shakespeare's Sonnets",
            actors=[actor, actor_2],
            genres=[drama, comedy],
        )
        self.play_2 = sample_play(
            title="Hamlet",
            description="Also fun to watch!",
            actors=[actor_1, actor_3],
            genres=[drama, comedy],
        )

    def test_list_play(self):
        response = self.client.get(PLAY_LIST_URL)

        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_play(self):
        response = self.client.get(detail_url(self.play_1.id))

        serializer = PlayDetailSerializer(self.play_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class PlayFilterTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_user())

        self.actor = sample_actor()
        self.actor_2 = sample_actor(first_name="Emilia", last_name="Watson")
        self.actor_3 = sample_actor(first_name="Keanu", last_name="Reeves")

        self.drama = sample_genre()
        self.comedy = sample_genre(name="Comedy")

        self.play_1 = sample_play(
            title="Shakespeare's Sonnets",
            actors=[self.actor, self.actor_2],
            genres=[self.drama],
        )

        self.play_2 = sample_play(
            title="Hamlet",
            actors=[self.actor_3],
            genres=[self.comedy],
        )

        self.play_3 = sample_play(title="Without relations")

    def test_filter_plays_by_title(self):
        response = self.client.get(PLAY_LIST_URL, {"title": "Hamlet"})

        serializer_1 = PlayListSerializer(self.play_1)
        serializer_2 = PlayListSerializer(self.play_2)
        serializer_3 = PlayListSerializer(self.play_3)

        self.assertIn(serializer_2.data, response.data)
        self.assertNotIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_3.data, response.data)

    def test_filter_by_actors(self):
        response = self.client.get(PLAY_LIST_URL, {"actors": self.actor.id})

        serializer_1 = PlayListSerializer(self.play_1)
        serializer_2 = PlayListSerializer(self.play_2)
        serializer_3 = PlayListSerializer(self.play_3)

        self.assertIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_2.data, response.data)
        self.assertNotIn(serializer_3.data, response.data)

    def test_filter_by_genres(self):
        response = self.client.get(PLAY_LIST_URL, {"genres": self.comedy.id})

        serializer_1 = PlayListSerializer(self.play_1)
        serializer_2 = PlayListSerializer(self.play_2)
        serializer_3 = PlayListSerializer(self.play_3)

        self.assertIn(serializer_2.data, response.data)
        self.assertNotIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_3.data, response.data)

    def test_filter_by_multiple_actors(self):
        response = self.client.get(
            PLAY_LIST_URL, {"actors": f"{self.actor.id},{self.actor_2.id}"}
        )

        serializer_1 = PlayListSerializer(self.play_1)
        serializer_2 = PlayListSerializer(self.play_2)
        serializer_3 = PlayListSerializer(self.play_3)

        self.assertIn(serializer_1.data, response.data)
        self.assertNotIn(serializer_2.data, response.data)
        self.assertNotIn(serializer_3.data, response.data)

    def test_actors_filter_non_numeric_does_not_crash(self):
        response = self.client.get(PLAY_LIST_URL, {"actors": "abc"})

        self.assertLess(response.status_code, 500)

    def test_genres_filter_partially_invalid_does_not_crash(self):
        response = self.client.get(PLAY_LIST_URL, {"genres": "1,x"})

        self.assertLess(response.status_code, 500)

    def test_actors_filter_nonexistent_id_returns_empty_list(self):
        sample_play()
        response = self.client.get(PLAY_LIST_URL, {"actors": 99999})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_performance_filter_invalid_date_does_not_crash(self):
        response = self.client.get(PERFORMANCE_LIST_URL, {"date": "not-a-date"})

        self.assertLess(response.status_code, 500)


class PlayModifyByUserTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_user())

    def test_create_play_forbidden(self):
        payload = {"title": "New play", "description": "Desc"}
        response = self.client.post(PLAY_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Play.objects.filter(title="New play").exists())

    def test_delete_play_forbidden(self):
        play = sample_play()

        response = self.client.delete(detail_url(play_id=play.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Play.objects.filter(id=play.id).exists())


class PlayModifyByAdminTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=sample_admin())

    def test_create_play(self):
        actor = sample_actor()
        genre = sample_genre()
        payload = {
            "title": "test_title",
            "description": "desc",
            "actors": [actor.id],
            "genres": [genre.id],
        }
        response = self.client.post(PLAY_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        play = Play.objects.get(id=response.data["id"])

        self.assertEqual(payload["title"], play.title)
        self.assertEqual(payload["description"], play.description)

    def test_create_play_with_actors_and_genres(self):
        actor = sample_actor()
        genre = sample_genre()

        payload = {
            "title": "TestTitle",
            "description": "Test desc",
            "actors": [actor.id],
            "genres": [genre.id],
        }

        response = self.client.post(PLAY_LIST_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        play = Play.objects.get(id=response.data["id"])

        self.assertIn(actor, play.actors.all())
        self.assertIn(genre, play.genres.all())

    def test_create_play_invalid_data(self):
        payload = {"title": "", "description": "desc"}

        response = self.client.post(PLAY_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Play.objects.all().count(), 0)

    def test_delete_play(self):
        play = sample_play()

        response = self.client.delete(detail_url(play.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Play.objects.filter(id=play.id).exists())

    def test_delete_nonexistent_play(self):
        response = self.client.delete(detail_url(999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
