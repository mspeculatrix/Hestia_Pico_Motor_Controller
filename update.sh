#!/usr/bin/env zsh
set -euo pipefail  # Exit immediately on any error or unset variable

SOURCE_DIR="."
TARGET_USER="smd"
TARGET_HOST="localhost"
TARGET_DIR="/Users/smd/Dev/PROJECTS/HESTIA/HESTIA_WEBSERVER/public_html/firmware"
TARGET_KEY="${HOME}/.ssh/ssh-key"

# Regenerate manifest.json
python3 update.py

# Extract filenames (JSON keys) from manifest.json into an array
# and append manifest.json itself to the upload list
files=( ${(f)"$(python3 -c 'import json; print("\n".join(json.load(open("manifest.json")).keys()))')"} )
files+=("manifest.json")

echo "Deploying ${#files[@]} files to ${TARGET_USER}@${TARGET_HOST}:${TARGET_DIR}..."

# Ensure target directory exists on remote/local host
ssh -i "${TARGET_KEY}" "${TARGET_USER}@${TARGET_HOST}" "mkdir -p '${TARGET_DIR}'"

# Upload all files in a single SCP batch (or use rsync for delta transfers)
scp -i "${TARGET_KEY}" "${files[@]}" "${TARGET_USER}@${TARGET_HOST}:${TARGET_DIR}/"

echo "Deployment complete"
