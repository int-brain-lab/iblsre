#!/bin/bash
# Fail the dump pipeline if pg_dump fails, not just gzip
set -o pipefail

# Configuration
BACKUP_DIR="/home/ubuntu/backups"
FINAL_FILENAME="alyx_full.sql.gz"
TEMP_FILENAME="alyx_full.tmp.sql.gz"
CONTAINER="alyx_postgres"
DB_USER="alyx" # Change if needed (e.g., 'alyx')
DB_NAME="alyx_steinmetz"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

# 1. Dump to a TEMPORARY file first
# We use \$POSTGRES_PASSWORD to safely use the password inside the container
docker exec $CONTAINER bash -c "PGPASSWORD=\$POSTGRES_PASSWORD pg_dump -U $DB_USER $DB_NAME" | gzip > "$BACKUP_DIR/$TEMP_FILENAME"
DUMP_STATUS=$?

# 2. Check the dump succeeded (gzip output is never empty, so size alone isn't enough)
if [ $DUMP_STATUS -eq 0 ] && [ -s "$BACKUP_DIR/$TEMP_FILENAME" ]; then
    # SUCCESS:
    # Overwrite the static file with the new valid dump
    mv "$BACKUP_DIR/$TEMP_FILENAME" "$BACKUP_DIR/$FINAL_FILENAME"

    # Touch the file to ensure the timestamp is exactly now (optional but good for verification)
    touch "$BACKUP_DIR/$FINAL_FILENAME"

    echo "Backup successful: $(date)"
else
    # FAILURE:
    # Remove the empty temp file and exit with error
    echo "Backup FAILED: pg_dump exited with status $DUMP_STATUS. Keeping previous version."
    rm -f "$BACKUP_DIR/$TEMP_FILENAME"
    exit 1
fi

