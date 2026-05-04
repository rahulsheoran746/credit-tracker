#!/usr/bin/env bash
# Nightly Postgres backup -> gzip -> S3.
#
# Requires on the host:
#   - aws CLI configured (via `aws configure` or an IAM role if on EC2/Lightsail)
#   - Environment variables: S3_BACKUP_BUCKET, DB_USER, DB_NAME
#   - The postgres container named 'shiv-postgres' must be running
#
# Typical cron entry (every day at 02:00):
#   0 2 * * * cd /home/ubuntu/credit-tracker && ./scripts/backup.sh >> /var/log/shiv-backup.log 2>&1

set -euo pipefail

# Load .env from the project root so DB_USER / DB_NAME / S3_BACKUP_BUCKET are picked up
if [ -f "$(dirname "$0")/../.env" ]; then
    set -a
    source "$(dirname "$0")/../.env"
    set +a
fi

: "${DB_USER:?DB_USER must be set}"
: "${DB_NAME:?DB_NAME must be set}"
: "${S3_BACKUP_BUCKET:?S3_BACKUP_BUCKET must be set}"

CONTAINER="shiv-postgres"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
FILE="shiv-${DATE}.sql.gz"
LOCAL="/tmp/${FILE}"
S3_KEY="shiv-dairy/${FILE}"

echo "[$(date)] Starting backup..."

# Dump + compress
docker exec -t "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$LOCAL"
SIZE=$(du -h "$LOCAL" | cut -f1)
echo "[$(date)] Local dump: $LOCAL ($SIZE)"

# Upload to S3 (Standard-IA is cheaper for archives)
aws s3 cp "$LOCAL" "s3://${S3_BACKUP_BUCKET}/${S3_KEY}" --storage-class STANDARD_IA
echo "[$(date)] Uploaded: s3://${S3_BACKUP_BUCKET}/${S3_KEY}"

# Clean up local copy
rm -f "$LOCAL"

echo "[$(date)] Backup complete."
