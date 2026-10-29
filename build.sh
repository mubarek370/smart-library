#!/usr/bin/env bash
# Render build script
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --no-input

# Run database migrations against Supabase
python manage.py migrate --no-input
