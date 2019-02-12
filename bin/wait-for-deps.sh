#!/bin/sh

set -e

cmd="$@"

until python bin/connect-to-postgres.py; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

until python bin/connect-to-solr.py; do
  >&2 echo "solr is unavailable - sleeping"
  sleep 1
done

>&2 echo "required services are up - executing command"
exec $cmd
