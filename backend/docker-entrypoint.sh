#!/bin/sh

# Check if postgres database is ready
if [ "$DATABASE" = "postgres"]
then
  echo "Waiting for postgres ..."

  while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
    sleep 0.1
  done

  echo "PostgreSQL started"

fi

echo "Collect static files"
python manage.py collectstatic --noinput

echo "Apply database migrations"
python manage.py migrate

 echo "Filling database"
 python manage.py loaddata db.json

exec "$@"