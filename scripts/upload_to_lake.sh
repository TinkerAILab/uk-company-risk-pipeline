#!/usr/bin/env bash
# Upload a monthly snapshot's raw and clean files to the Azure Data Lake.
# Usage: scripts/upload_to_lake.sh 2026-10-01

set -euo pipefail

SNAPSHOT_DATE="${1:?Please give a snapshot date, e.g. 2026-10-01}"
ACCOUNT="ukcompanyrisk2026"

if [ -z "${AZ_SAS_TOKEN:-}" ]; then
  echo "AZ_SAS_TOKEN is not set. Add it as a Codespaces secret." >&2
  exit 1
fi

upload() {
  local container="$1" lake_path="$2" local_file="$3"
  echo "Uploading $local_file -> $container/$lake_path"
  az storage fs file upload \
    --account-name "$ACCOUNT" \
    --sas-token "$AZ_SAS_TOKEN" \
    --file-system "$container" \
    --path "$lake_path" \
    --source "$local_file" \
    --overwrite \
    --only-show-errors \
    --output none
}

upload raw   "bulk/companies_${SNAPSHOT_DATE}.parquet" \
             "data/raw/bulk/companies_${SNAPSHOT_DATE}.parquet"

upload clean "companies/companies_clean_${SNAPSHOT_DATE}.parquet" \
             "data/clean/companies_clean_${SNAPSHOT_DATE}.parquet"

echo "Done."