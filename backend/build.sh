#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate
python manage.py migrate authtoken

echo "Creating superuser..."
DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser \
  --noinput \
  --username lennox \
  --email lennox@test.com

echo "Build complete!"