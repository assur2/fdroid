"""Build the public input directory for fdroid update on a fresh CI runner."""
import json
import os
import re
import subprocess
from pathlib import Path

import yaml


def version(tag):
    component = r"(0|[1-9][0-9]{0,2})"
    match = re.fullmatch("v" + r"\.".join([component] * 3), tag)
    if not match:
        return None
    major, minor, patch = map(int, match.groups())
    return major * 1_000_000 + minor * 1000 + patch


def select_releases(pages):
    selected = []
    for page in pages:
        for release in page:
            if release["draft"] or release["prerelease"]:
                continue
            tag = release["tag_name"]
            code = version(tag)
            if code:
                selected.append((code, tag))
    if not selected:
        raise RuntimeError("No stable vMAJOR.MINOR.PATCH releases found")
    return sorted(selected, reverse=True)[:3]


def output(*args):
    return subprocess.check_output(args, text=True)


def main():
    source = os.environ["NOTES_REPO"]
    app_id = os.environ["APP_ID"]
    signer = os.environ["APK_SHA256"].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", signer):
        raise ValueError("APK_SHA256 must be a hex SHA-256 fingerprint without colons")
    tools = Path(os.environ["ANDROID_HOME"]) / "build-tools/35.0.0"
    pages = json.loads(output("gh", "api", "--paginate", "--slurp",
                              f"repos/{source}/releases?per_page=100"))
    releases = select_releases(pages)
    repo = Path("repo")
    repo.mkdir()
    names = []
    for code, tag in releases:
        apk = repo / f"{app_id}_{code}.apk"
        subprocess.run(["gh", "release", "download", tag, "--repo", source,
                        "--pattern", "Notes.apk", "--output", apk], check=True)
        certs = output(tools / "apksigner", "verify", "--print-certs", apk)
        actual = re.findall(r"^Signer #\d+ certificate SHA-256 digest: (\w+)$",
                            certs, re.MULTILINE)
        if actual != [signer]:
            raise ValueError(f"Unexpected signer for {tag}")
        info = output(tools / "aapt", "dump", "badging", apk)
        identity = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'",
                             info, re.MULTILINE)
        if not identity or identity.groups() != (app_id, str(code), tag[1:]):
            raise ValueError(f"Unexpected package or version for {tag}")
        archive = repo / f"{app_id}_{code}_src.tar.gz"
        with archive.open("wb") as destination:
            subprocess.run(["gh", "api", f"repos/{source}/tarball/{tag}"],
                           stdout=destination, check=True)
        names.append(apk.name)

    latest_code, latest_tag = releases[0]
    metadata = dict(Name="Notes", Summary="Edit a local text note",
                    Description="A simple Kotlin Compose text editor.",
                    License="GPL-3.0-only", Categories=["Writing"], SourceCode=f"{os.environ['FEED_URL']}/{app_id}_{latest_code}_src.tar.gz",
                    CurrentVersion=latest_tag[1:],
                    CurrentVersionCode=latest_code, AllowedAPKSigningKeys=[signer])
    Path("metadata").mkdir()
    Path(f"metadata/{app_id}.yml").write_text(yaml.safe_dump(metadata))
    Path("expected-apks.txt").write_text("\n".join(names))


if __name__ == "__main__":
    main()
