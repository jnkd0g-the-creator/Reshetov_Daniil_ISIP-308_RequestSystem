#!/usr/bin/env bash
# Collection, not an unattended script. Never put real credentials in this file.
# Full executable check (29 requests): python scripts/check_api.py
set -eu
umask 077
BASE="${BASE:-http://127.0.0.1:8000}"
mkdir -p .local
curl -sS "$BASE/health"
curl -sS -w '\n%{http_code}\n' "$BASE/requests"  # 401 without login
# Prepare .local/login.json locally: {"username":"...","password":"..."}.
test -f .local/login.json || { echo 'Create private .local/login.json locally first.'; exit 1; }
curl -sS -c .local/cookies -H 'Content-Type: application/json' \
  --data-binary @.local/login.json "$BASE/auth/login" -o .local/login-response.json
CSRF="$(python -c 'import json; print(json.load(open(".local/login-response.json"))["csrf_token"])')"
curl -sS -b .local/cookies "$BASE/requests"
curl -sS -b .local/cookies "$BASE/requests/1"
curl -sS -b .local/cookies --get --data-urlencode 'q=КРАН' "$BASE/requests"
curl -sS -b .local/cookies "$BASE/requests?status_code=new&category_id=1"
curl -sS -b .local/cookies "$BASE/users"
curl -sS -b .local/cookies "$BASE/statuses"
curl -sS -b .local/cookies "$BASE/categories"
curl -sS -b .local/cookies "$BASE/cafes"
curl -sS -b .local/cookies -w '\n%{http_code}\n' "$BASE/requests/99999999"
curl -sS -b .local/cookies -H "X-CSRF-Token: $CSRF" -H 'Content-Type: application/json' \
  --data '{"title":""}' -w '\n%{http_code}\n' "$BASE/requests" # 422
curl -sS -b .local/cookies -X POST -H "X-CSRF-Token: $CSRF" "$BASE/auth/logout"
