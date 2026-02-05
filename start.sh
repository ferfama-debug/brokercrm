#!/bin/bash
python manage.py migrate
python manage.py createsuperuser --noinput || true
gunicorn brokercrm.wsgi:application --bind 0.0.0.0:$PORT
