#!/bin/sh

# Check if postgres database is ready
if [ "$DB_NAME" = "postgres"]
then
  echo "Waiting for postgres ..."

  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
  done

  echo "PostgreSQL started"

fi

echo "Collect static files"
python manage.py collectstatic --noinput

echo "Apply database migrations"
python manage.py migrate

exec "$@"