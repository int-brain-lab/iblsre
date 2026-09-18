#!/bin/bash
set -e
# Load environment variables from the deployment .env if available. This script is synced
# to ~/app/scripts/ by ansible_deploy_alyx.yaml, so ../.env is ~/app/.env. It previously read
# ../app/.env relative to its old home in the iblsre checkout, which resolved to a path that
# never existed -- the source silently did nothing and the defaults below were always used.
# ~/app/.env is tried as a fallback so a copy run from elsewhere still finds the real values.
for env_file in "$(dirname "$0")/../.env" ~/app/.env; do
    if [ -f "$env_file" ]; then
        source "$env_file"
        break
    fi
done
# Set default values for uploaded folders paths
DJANGO_MEDIA_ROOT=${DJANGO_MEDIA_ROOT:-/home/ubuntu/uploaded}
ALYX_TABLES_ROOT=${ALYX_TABLES_ROOT:-/home/ubuntu/tables}

# Read from what is running rather than assumed: a trial deployment uses its own container
# name and database, and hard-coding these reset a database nobody was using.
ALYX_CONTAINER=${ALYX_CONTAINER:-$(docker ps --filter name=^alyx_apache --format '{{.Names}}' | head -n 1)}
if [ -z "${ALYX_CONTAINER}" ]; then
    echo "no running alyx_apache* container: nothing to rebuild" >&2
    exit 1
fi
ALYX_DB=$(docker exec "${ALYX_CONTAINER}" printenv POSTGRES_DB)
if [ -z "${ALYX_DB}" ]; then
    echo "could not read POSTGRES_DB from ${ALYX_CONTAINER}" >&2
    exit 1
fi
echo "rebuilding database '${ALYX_DB}' served by container '${ALYX_CONTAINER}'"

# Loads the database into the postgres container and into postgres
docker cp ~/alyx_test.sql alyx_postgres:/home
docker exec -e PGPASSWORD=postgres -e TARGET_DB="${ALYX_DB}" alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $TARGET_DB -c "drop schema public cascade"'
docker exec -e PGPASSWORD=postgres -e TARGET_DB="${ALYX_DB}" alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $TARGET_DB -c "create schema public"'
docker exec -e PGPASSWORD=postgres -e TARGET_DB="${ALYX_DB}" alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $TARGET_DB -f /home/alyx_test.sql'

# Clean up old files in uploaded folders (older than 5 days)
# Using environment variables for paths, with defaults from docker-compose.host.yaml
sudo find "${DJANGO_MEDIA_ROOT}" -type f -mtime +5 -delete 2>/dev/null || true
sudo find "${ALYX_TABLES_ROOT}" -type f -mtime +5 -delete 2>/dev/null || true

# apply migrations and load init fixtures to stay up to date with alyx
# (no -it: this runs unattended from cron, with no TTY to attach)
docker exec "${ALYX_CONTAINER}" python manage.py check
docker exec "${ALYX_CONTAINER}" python manage.py migrate
docker exec "${ALYX_CONTAINER}" /var/www/alyx/scripts/load-init-fixtures.sh
docker exec "${ALYX_CONTAINER}" python manage.py set_db_permissions
docker exec "${ALYX_CONTAINER}" python manage.py set_user_permissions

# Regenerate the ONE cache tables for the database just restored. --compress writes cache.zip
# and cache_info.json, without which /cache/info answers 500.
docker exec "${ALYX_CONTAINER}" python manage.py one_cache --compress
