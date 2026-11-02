#!/usr/bin/env bash
# Render build script
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate --no-input

# Ensure Django Site record exists to prevent allauth 500 errors
python manage.py setup_site
