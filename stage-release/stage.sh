#!/usr/bin/env bash
set -euo pipefail

if [[ ! "$GITHUB_REF_NAME" =~ ^v(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})$ ]]; then
  exit 1
fi
code=$(( BASH_REMATCH[1]*1000000 + BASH_REMATCH[2]*1000 + BASH_REMATCH[3] ))
(( code > 0 ))
[[ "$APP_ID" =~ ^org\.weare\.[a-z][a-z0-9]*$ ]]

stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
apk="${APP_ID}_${code}.apk"
src="${APP_ID}_${code}_src.tar.gz"
gh release download "$GITHUB_REF_NAME" --repo "$GITHUB_REPOSITORY" --pattern "$APK_NAME" --output "$stage/$apk"
git archive --format=tar.gz --prefix="${GITHUB_REPOSITORY#*/}-${GITHUB_REF_NAME#v}/" --output="$stage/$src" "$GITHUB_SHA"
git config user.name 'Weare Apps publisher'
git config user.email 'notes-publisher@users.noreply.github.com'

for attempt in 1 2 3 4; do
  if [[ -n "$(git ls-remote --heads origin refs/heads/fdroid-artifacts)" ]]; then
    git fetch --no-tags origin refs/heads/fdroid-artifacts
    git switch --detach FETCH_HEAD
  else
    git switch --orphan "stage-$attempt"
  fi
  if [[ -e "$apk" || -e "$src" ]]; then
    cmp "$apk" "$stage/$apk"
    git show "HEAD:$src" | tar -tzf - >/dev/null
    exit 0
  fi
  cp "$stage/$apk" "$stage/$src" .
  git add -- "$apk" "$src"
  git commit -m "Stage ${GITHUB_REF_NAME} for F-Droid"
  if git push origin HEAD:refs/heads/fdroid-artifacts; then
    exit 0
  fi
  sleep "$attempt"
done
exit 1
