#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo '::error::The catalog preflight credential is missing.'
  exit 1
fi

repo=assur2/notes
api_version='X-GitHub-Api-Version: 2026-03-10'
run_id=$(gh api --method POST "repos/$repo/actions/workflows/catalog.yml/dispatches" \
  --header "$api_version" --raw-field "ref=$PUBLISHER_REF" \
  --raw-field 'inputs[preflight]=true' --jq '.workflow_run_id')

if [[ ! "$run_id" =~ ^[1-9][0-9]*$ ]]; then
  echo '::error::GitHub did not return a specific preflight run ID.'
  exit 1
fi
echo "Catalog preflight: https://github.com/$repo/actions/runs/$run_id"

deadline=$((SECONDS + 420))
while (( SECONDS < deadline )); do
  result=$(gh api "repos/$repo/actions/runs/$run_id" --header "$api_version" \
    --jq 'if .status == "completed" then (.conclusion // "unknown") else "pending" end')
  case "$result" in
    success) exit 0 ;;
    pending) sleep 10 ;;
    *)
      echo "::error::Catalog preflight ended with '$result'. Release blocked."
      exit 1 ;;
  esac
done

echo '::error::Timed out waiting for catalog preflight. Release blocked.'
exit 1
