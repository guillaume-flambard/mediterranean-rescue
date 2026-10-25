#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v app_password="$DB_PASSWORD" <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE ROLE rescue LOGIN CREATEDB PASSWORD :'app_password';
GRANT CONNECT ON DATABASE rescue TO rescue;
GRANT USAGE, CREATE ON SCHEMA public TO rescue;
SQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
