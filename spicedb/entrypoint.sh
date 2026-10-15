#!/bin/sh
set -e

echo "Waiting for database..."
until pg_isready -h $DB_HOST -p $DB_PORT -U root -d spicedb; do
  echo "Database not ready - waiting"
  sleep 2
done

echo "Running SpiceDB migrations..."
spicedb migrate head \
  --datastore-engine postgres \
  --datastore-conn-uri "postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$SPICEDB_NAME?sslmode=disable"

echo "Migration complete."