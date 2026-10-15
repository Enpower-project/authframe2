#!/bin/sh
set -e

# echo "Updating CA trust..."
# update-ca-certificates

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8081 #\
  # --log-level trace

# uvicorn app.main:app \
#   --host 0.0.0.0 \
#   --port 8444 \
#   --ssl-certfile /certs/pdp.crt \
#   --ssl-keyfile /certs/pdp.key \
#   --ssl-ca-certs /certs/ca.crt \
#   --ssl-cert-reqs 2 \
#   --log-level trace


  # CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug", "--access-log"]