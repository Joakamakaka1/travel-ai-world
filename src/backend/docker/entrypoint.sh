#!/bin/sh
# Entrypoint of both images: serves on :8000 (Compose, and Lambda through the Web Adapter).
# Nothing runs before serving: core_api's DynamoDB table (ADR 0023) belongs to Terraform
# on AWS, and the service creates it itself against a local endpoint.
set -e

echo "==> [${SERVICE}] Starting uvicorn on :8000"
# the structured access log uses route templates; uvicorn's own lines would repeat
# each request with its raw path and query string
case "${ACCESS_LOG_ENABLED:-false}" in
  1|true|True|TRUE|yes|Yes|YES|on|On|ON) set -- --no-access-log ;;
  *) set -- ;;
esac
exec uvicorn "${SERVICE}.main:app" --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*" "$@"
