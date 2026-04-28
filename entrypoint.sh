#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Creating admin user..."
python manage.py create_admin

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
