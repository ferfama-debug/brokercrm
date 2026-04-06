#!/usr/bin/env bash
set -euo pipefail

echo "Applying core migrations..."
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate sessions
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity 2

echo "Creating superuser if not exists..."
python manage.py shell <<'END'
from django.contrib.auth import get_user_model
User = get_user_model()

username = "admin"
password = "admin123"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created.")
else:
    print("Superuser already exists.")
END

echo "Forcing session table creation..."
python manage.py shell <<'END'
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS django_session (
        session_key varchar(40) NOT NULL PRIMARY KEY,
        session_data text NOT NULL,
        expire_date timestamp with time zone NOT NULL
    );
    """)
    print("django_session ensured.")
END

echo "Starting Gunicorn..."
exec gunicorn brokercrm.wsgi:application --bind 0.0.0.0:$PORT