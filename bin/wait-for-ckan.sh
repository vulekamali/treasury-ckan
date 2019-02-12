#!/bin/sh

set -e

cmd="$@"

until curl ckan:5000; do
  >&2 echo "CKAN is unavailable - sleeping"
  sleep 1
done

>&2 echo "required services are up"
