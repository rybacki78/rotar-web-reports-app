#!/usr/bin/env bash
set -Eeuo pipefail


: "${JOB_SCRIPT}"
: "${STREAMLIT_PORT}"
: "${STREAMLIT_ADDRESS}"
: "${TZ}"

mkdir -p /var/log
touch /var/log/cron.log

echo "[entrypoint] Running one-off job: ${JOB_SCRIPT}"
if ! /usr/local/bin/python "$JOB_SCRIPT"; then
  echo "[entrypoint] WARNING: one-off job failed (continuing so cron can retry)" | tee -a /var/log/cron.log
fi

CRON_FILE="/etc/cron.monthly/update-stock-data"
{
  echo "SHELL=/bin/bash"
  echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  echo "CRON_TZ=${TZ}"
  echo "0 0 7 * * root cd /app && /usr/local/bin/python \"$JOB_SCRIPT\" >> /var/log/cron.log 2>&1"
} > "$CRON_FILE"

chmod 0644 "$CRON_FILE"

echo "[entrypoint] Starting cron"
if command -v cron >/dev/null 2>&1; then
  cron
else
  /usr/sbin/cron
fi

tail -F /var/log/cron.log &

echo "[entrypoint] Starting Streamlit on ${STREAMLIT_ADDRESS}:${STREAMLIT_PORT}"
exec streamlit run "/app/streamlit_app.py" \
  --server.port="${STREAMLIT_PORT}" \
  --server.address="${STREAMLIT_ADDRESS}"