# Theatre API Service

REST API for a theatre, built with Django REST Framework. It manages plays, actors, genres, theatre halls, performances and reservations (with tickets), and uses JWT authentication with login by email.

## Features

- JWT authentication (email + password), custom `User` model
- CRUD for plays, actors, genres, theatre halls, performances and reservations (with tickets)
- Filtering plays by title, actors and genres
- Permissions: authenticated users can read; only admins can create, update and delete
- Interactive API documentation (Swagger, drf-spectacular)
- Dockerized setup with PostgreSQL
- Automated tests

## Tech stack

- Python 3.11
- Django, Django REST Framework
- djangorestframework-simplejwt
- drf-spectacular
- PostgreSQL 16
- Docker, Docker Compose

## Getting started (Docker)

1. Clone the repository:

```
git clone https://github.com/kbatrakov/theatre_api.git
cd theatre_api
```

2. Create the environment file from the sample:

```
cp .env.sample .env
```

On Windows PowerShell use `copy .env.sample .env`. Adjust the values if needed.

3. Build and start the containers:

```
docker compose up --build
```

Migrations are applied automatically on startup.

4. Create a superuser (in a second terminal):

```
docker compose exec app python manage.py createsuperuser
```

5. The API is available at `http://localhost:8000/`.

## Environment variables

| Variable | Description |
|---|---|
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `POSTGRES_HOST` | Database host (`db` inside Docker Compose) |
| `POSTGRES_PORT` | Database port (default `5432`) |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development |
| `ALLOWED_HOSTS` | Comma-separated list of hosts |

## Authentication

1. Register a user: `POST /api/user/register/`
2. Get a token pair: `POST /api/user/login/` with `email` and `password`
3. Send the access token in the header of every request:

```
Authorization: Bearer <access_token>
```

4. Refresh an expired access token: `POST /api/user/refresh/` with the `refresh` token
5. Current user profile: `GET /api/user/me/`

## API documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

In Swagger use the **Authorize** button and paste the access token.

## Main endpoints

| Resource | Endpoint |
|---|---|
| Actors | `/api/theatre/actors/` |
| Genres | `/api/theatre/genres/` |
| Plays | `/api/theatre/plays/` |
| Theatre halls | `/api/theatre/theatre_halls/` |
| Performances | `/api/theatre/performances/` |
| Reservations | `/api/theatre/reservations/` |

### Filtering plays

```
GET /api/theatre/plays/?title=hamlet
GET /api/theatre/plays/?actors=1,2
GET /api/theatre/plays/?genres=3
```

## Sample data

To fill the database with demo data from the fixture:

```
docker compose exec app python manage.py loaddata theatre_fixture.json
```

## Running tests

```
docker compose exec app python manage.py test
```

## Useful commands

```
docker compose up -d              # run in the background
docker compose logs -f app        # follow application logs
docker compose down               # stop containers (data is kept)
docker compose down -v            # stop containers and delete the database volume
```

## Project structure

```
theatre_api/
├── theatre/                    # main app: theatre domain
│   ├── migrations/
│   ├── tests/                  # API tests
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py          # custom permission classes
│   ├── serializers.py
│   ├── urls.py                 # router with all viewsets
│   └── views.py                # viewsets, filtering
├── user/                       # users app: registration, JWT login, profile
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py               # custom User model (login by email)
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── theatre_api_service/        # project settings and root urls
├── templates/
├── theatre_fixture.json        # sample data
├── schema.yml                  # OpenAPI schema
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.sample                 # example environment variables
├── manage.py
└── requirements.txt
```
