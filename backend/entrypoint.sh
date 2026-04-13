#!/bin/bash
set -e

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "
import socket, sys
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(('${DB_HOST}', ${DB_PORT}))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "PostgreSQL not ready yet, retrying..."
    sleep 2
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding database..."
python manage.py seed_db

echo "Starting server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 3
