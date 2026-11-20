#!/usr/bin/env bash
set -euo pipefail
umask 077
key="$RUNNER_TEMP/catalog.p12"
trap 'rm -f "$key" config.yml' EXIT
printf '%s' "$KEYSTORE" | base64 --decode > "$key"
python3 - <<'PY'
import os, yaml
from pathlib import Path
config = dict(repo_name="Notes", repo_description="Official Notes releases",
              repo_url=os.environ["FEED_URL"], repo_icon="icon.png",
              keystore=str(Path(os.environ["RUNNER_TEMP"]) / "catalog.p12"),
              repo_keyalias="catalog", keystorepass=os.environ["PASSWORD"],
              keypass=os.environ["PASSWORD"], make_current_version_link=False,
              archive_older=0)
Path("config.yml").write_text(yaml.safe_dump(config))
PY
mkdir -p repo/icons
cp icon.png repo/icons/icon.png
# The corresponding-source archive lives next to each signed APK.
fdroid update
python3 - <<'PY'
import json
from pathlib import Path
repo = Path("repo")
entries = json.loads((repo / "index-v1.json").read_text())["packages"]
indexed = {v["apkName"] for versions in entries.values() for v in versions}
expected = set(Path("expected-apks.txt").read_text().splitlines())
assert expected and indexed == expected, (expected, indexed)
assert (repo / "index-v1.jar").stat().st_size > 0
PY
