#!/bin/bash
# AGENTS_RULES v2 — Supervisor cron script
# Runs every hour via cron to check repository health
# Usage: Add to crontab with: crontab -e
#   0 * * * * /home/segun/CascadeProjects/Перед\ 0_2/AGENTS_RULES-v2/supervisor_cron.sh

set -euo pipefail

REPO_DIR="/home/segun/CascadeProjects/Перед 0_2/AGENTS_RULES-v2"
LOG_FILE="$REPO_DIR/supervisor_cron.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Supervisor cron starting..." >> "$LOG_FILE"

cd "$REPO_DIR" || exit 1

git pull --rebase origin main 2>/dev/null || git pull origin main 2>/dev/null || true

python3 "$REPO_DIR/supervisor.py" --fix >> "$LOG_FILE" 2>&1

python3 "$REPO_DIR/compile.py" --no-push >> "$LOG_FILE" 2>&1

if ! git diff --quiet 2>/dev/null; then
    git add -A
    git commit -m "[Supervisor-Cron] hourly health check + auto-fix" 2>/dev/null || true
    git push origin main 2>/dev/null || echo "[$TIMESTAMP] WARNING: git push failed" >> "$LOG_FILE"
fi

echo "[$TIMESTAMP] Supervisor cron done." >> "$LOG_FILE"
