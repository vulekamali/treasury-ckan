#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ckan_default;
    CREATE DATABASE ckan_default;
    GRANT ALL PRIVILEGES ON DATABASE ckan_default TO ckan_default;
EOSQL
