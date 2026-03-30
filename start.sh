#!/bin/sh
# Start Python API on port 8000 (internal only)
gunicorn api.app:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --timeout 300 &

# Start Next.js on port 8080 (exposed to Cloud Run)
export API_INTERNAL_URL=http://127.0.0.1:8000
export PORT=8080
export HOSTNAME=0.0.0.0
cd /app/frontend
node server.js &

# Wait for either process to exit
wait -n
exit $?
