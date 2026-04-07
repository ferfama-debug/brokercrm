#!/usr/bin/env bash
set -euo pipefail

echo "Applying admin migrations with fake-initial..."
python manage.py migrate admin --fake-initial --noinput || true

echo "Applying migrations..."
python manage.py migrate --fake-initial --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity 2

echo "Starting Gunicorn..."
exec gunicorn brokercrm.wsgi:application --bind 0.0.0.0:$PORT