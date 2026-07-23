#!/bin/bash
set -e
# Loads the database into the postgres container and into postgres
docker cp ~/alyx_test.sql alyx_postgres:/home
docker exec -e PGPASSWORD=postgres alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "drop schema public cascade"'
docker exec -e PGPASSWORD=postgres alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "create schema public"'
docker exec -e PGPASSWORD=postgres alyx_postgres sh -c 'psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f /home/alyx_test.sql'

# apply migrations and load init fixtures to stay up to date with alyx
# (no -it: this runs unattended from cron, with no TTY to attach)
docker exec alyx_apache python manage.py check
docker exec alyx_apache python manage.py migrate
docker exec alyx_apache /var/www/alyx/scripts/load-init-fixtures.sh
docker exec alyx_apache python manage.py set_db_permissions
docker exec alyx_apache python manage.py set_user_permissions
