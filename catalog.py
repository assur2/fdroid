"""Collect the three newest stable releases per app for a fresh signed catalog."""
import json
import os
import re
import subprocess
from pathlib import Path

import yaml

APPS = [
    ("assur2/notes", "org.weare.notes", "Notes", "Edit a local text note", "Writing",
     "9eaada59bb9ff563d7b17efdb937fa8830c97fee78f536c9d75ca9e8f4b83472"),
    ("assur2/opvang", "org.weare.opvang", "Opvang", "Lees je KOVnet-ouderportaal", "Reading",
     "9afe0a27e5b84ed788a9a9db35ac2ed9f995fb6da436e47ea42da2907c139bdd"),
    ("assur2/glasswater-defense", "org.weare.glasswaterdefense", "Glasswater Defense",
     "Defend a canal lock across 12 waves", "Games",
     "de0385f0c407af4c4462121a66ec330f27a17d3f5ab52742338178e5bc1f2de4"),
]


def output(*args):
    return subprocess.check_output(args, text=True)


def releases(source):
    pages = json.loads(output("gh", "api", "--paginate", "--slurp",
                              f"repos/{source}/releases?per_page=100"))
    selected = []
    for page in pages:
        for release in page:
            tag = release["tag_name"]
            match = re.fullmatch(r"v(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})", tag)
            if match and not release["draft"] and not release["prerelease"]:
                major, minor, patch = map(int, match.groups())
                code = major * 1_000_000 + minor * 1000 + patch
                if code:
                    selected.append((code, tag))
    if not selected:
        raise RuntimeError(f"No stable release for {source}")
    return sorted(selected, reverse=True)[:3]


def collect(source, app_id, name, summary, category, signer):
    tools = Path(os.environ["ANDROID_HOME"]) / "build-tools/35.0.0"
    names = []
    asset_name = name.replace(' ', '.') + '.apk'
    versions = releases(source)
    for code, tag in versions:
        apk = Path("repo") / f"{app_id}_{code}.apk"
        subprocess.run(["gh", "release", "download", tag, "--repo", source,
                        "--pattern", asset_name, "--output", apk], check=True)
        certs = output(tools / "apksigner", "verify", "--print-certs", apk)
        actual = re.findall(r"^Signer #\d+ certificate SHA-256 digest: (\w+)$", certs, re.MULTILINE)
        if actual != [signer]:
            raise ValueError(f"Unexpected APK signer for {source}@{tag}")
        info = output(tools / "aapt", "dump", "badging", apk)
        identity = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", info, re.MULTILINE)
        if not identity or identity.groups() != (app_id, str(code), tag[1:]):
            raise ValueError(f"Unexpected APK identity for {source}@{tag}")
        with apk.with_name(f"{apk.stem}_src.tar.gz").open("wb") as archive:
            subprocess.run(["gh", "api", f"repos/{source}/tarball/{tag}"], stdout=archive, check=True)
        names.append(apk.name)

    latest_code, latest_tag = versions[0]
    metadata = dict(Name=name, Summary=summary, Description=summary,
                    License="GPL-3.0-only", Categories=[category],
                    SourceCode=f"{os.environ['FEED_URL']}/{app_id}_{latest_code}_src.tar.gz",
                    CurrentVersion=latest_tag[1:], CurrentVersionCode=latest_code, AllowedAPKSigningKeys=[signer])
    Path(f"metadata/{app_id}.yml").write_text(yaml.safe_dump(metadata))
    return names


if __name__ == "__main__":
    Path("repo").mkdir()
    Path("metadata").mkdir()
    expected = [name for app in APPS for name in collect(*app)]
    Path("expected-apks.txt").write_text("\n".join(expected))

