#!/usr/bin/env bash
# Restore a backup from S3 into the running Postgres container.
# WARNING: this DROPS the existing database and recreates it from the dump.
#
# Usage:  ./scripts/restore.sh shiv-2026-04-20_02-00-00.sql.gz

set -euo pipefail

if [ -f "$(dirname "$0")/../.env" ]; then
    set -a
    source "$(dirname "$0")/../.env"
    set +a
fi

: "${DB_USER:?DB_USER must be set}"
: "${DB_NAME:?DB_NAME must be set}"
: "${S3_BACKUP_BUCKET:?S3_BACKUP_BUCKET must be set}"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup-filename>"
    echo "Example: $0 shiv-2026-04-20_02-00-00.sql.gz"
    exit 1
fi

FILE="$1"
LOCAL="/tmp/${FILE}"
CONTAINER="shiv-postgres"

echo "Downloading s3://${S3_BACKUP_BUCKET}/shiv-dairy/${FILE}..."
aws s3 cp "s3://${S3_BACKUP_BUCKET}/shiv-dairy/${FILE}" "$LOCAL"

read -rp "About to WIPE and RESTORE '${DB_NAME}' from this backup. Continue? (yes/no) " ans
if [ "$ans" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo "Dropping and recreating database..."
docker exec -i "$CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
docker exec -i "$CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE ${DB_NAME};"

echo "Restoring..."
gunzip -c "$LOCAL" | docker exec -i "$CONTAINER" psql -U "$DB_USER" "$DB_NAME"

echo "Done."
rm -f "$LOCAL"
