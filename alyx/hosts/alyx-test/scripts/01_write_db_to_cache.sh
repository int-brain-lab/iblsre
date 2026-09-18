#!/bin/bash
#./01_write_db_to_cache.sh /home/ubuntu/current_database.sql
set -e
if [ -z "$1" ]; then
    echo "usage: $0 <destination.sql>" >&2
    exit 1
fi

# Dump the database the running Alyx container uses, not whatever POSTGRES_DB means inside the
# postgres container - they differ while a trial deployment is live.
ALYX_CONTAINER=${ALYX_CONTAINER:-$(docker ps --filter name=^alyx_apache --format '{{.Names}}' | head -n 1)}
if [ -z "${ALYX_CONTAINER}" ]; then
    echo "no running alyx_apache* container: cannot tell which database to dump" >&2
    exit 1
fi
ALYX_DB=$(docker exec "${ALYX_CONTAINER}" printenv POSTGRES_DB)
if [ -z "${ALYX_DB}" ]; then
    echo "could not read POSTGRES_DB from ${ALYX_CONTAINER}" >&2
    exit 1
fi
echo "dumping database '${ALYX_DB}' served by container '${ALYX_CONTAINER}' to $1"

docker exec -e PGPASSWORD=postgres -e TARGET_DB="${ALYX_DB}" alyx_postgres sh -c '/usr/bin/pg_dump -cOx -h $POSTGRES_HOST -U $POSTGRES_USER -d $TARGET_DB -f /home/alyx_test.sql'
docker cp alyx_postgres:/home/alyx_test.sql "$1"
docker exec alyx_postgres rm -f /home/alyx_test.sql
