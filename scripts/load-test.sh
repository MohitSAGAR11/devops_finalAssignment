#!/usr/bin/env bash
# Generates API traffic so Grafana panels fill up and the backend HPA has CPU to react to.
# Usage: URL=http://<ingress-host> REQUESTS=5000 CONCURRENCY=20 ./scripts/load-test.sh
set -euo pipefail

URL="${URL:-http://inventory.local}"
REQUESTS="${REQUESTS:-3000}"
CONCURRENCY="${CONCURRENCY:-20}"

echo "Sending $REQUESTS requests to $URL with concurrency $CONCURRENCY"
seq "$REQUESTS" | xargs -P "$CONCURRENCY" -I{} sh -c '
  case $(( {} % 4 )) in
    0) curl -s -o /dev/null "$0/api/products/stats" ;;
    1) curl -s -o /dev/null "$0/api/products" ;;
    2) curl -s -o /dev/null "$0/api/products/999999" ;;   # 404s show up as 4xx in Grafana
    3) curl -s -o /dev/null "$0/" ;;
  esac
' "$URL"
echo "Load test completed"
