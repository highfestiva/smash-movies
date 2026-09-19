#!/usr/bin/env bash

set -euo pipefail

BUCKET="${1:?Usage: $0 <bucket-name>}"
DIR="$(pwd)"
NAME="$(basename "$DIR")"

echo "Uploading '$NAME/' to s3://$BUCKET/$NAME/"

aws s3 sync "$DIR/" "s3://$BUCKET/$NAME/" \
  --delete \
  --exclude ".git/*"

echo "Done."
