#!/usr/bin/env bash
set -euo pipefail

container="${OPENVIKING_CONTAINER:-openviking-dialectic}"
data_dir="${OPENVIKING_DATA_DIR:-/opt/openviking-dialectic}"
backup_dir="${OPENVIKING_BACKUP_DIR:-/opt/backups/openviking-dialectic}"
passphrase_file="${OPENVIKING_BACKUP_PASSPHRASE_FILE:-/etc/openviking-dialectic/backup.passphrase}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
plain_name="openviking-${stamp}.ovpack"

install -d -m 0700 "$data_dir/backup-staging" "$backup_dir"
test -s "$passphrase_file"
docker exec "$container" ov language en >/dev/null
docker exec "$container" sh -lc '
  printf "%s" "$OPENVIKING_ROOT_API_KEY" |
    ov config add custom \
      --name kanister-backup-local \
      --url http://127.0.0.1:1933 \
      --root-api-key-stdin \
      --account kanister \
      --user tenant-1 \
      --activate \
      -o json >/dev/null
'
docker exec "$container" ov backup "/app/.openviking/backup-staging/$plain_name"
gpg --batch --yes --symmetric --cipher-algo AES256 \
  --passphrase-file "$passphrase_file" \
  --output "$backup_dir/${plain_name}.gpg" \
  "$data_dir/backup-staging/$plain_name"
rm -f "$data_dir/backup-staging/$plain_name"
find "$backup_dir" -type f -name 'openviking-*.ovpack.gpg' -mtime +14 -delete
