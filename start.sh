#!/usr/bin/env bash
set -euo pipefail

echo "Applying migrations..."
python manage.py migrate --fake-initial --noinput --verbosity 2

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

echo "Starting Gunicorn..."
exec gunicorn brokercrm.wsgi:application --bind 0.0.0.0:$PORT