"""Collect the three newest stable releases per app for a fresh signed catalog."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

APPS = [
    ("assur2/notes", "org.weare.notes", "Notes", "Edit a local text note", "Writing",
     "9eaada59bb9ff563d7b17efdb937fa8830c97fee78f536c9d75ca9e8f4b83472"),
    ("assur2/opvang", "org.weare.opvang", "Opvang", "Lees je KOVnet-ouderportaal", "Reading",
     "9afe0a27e5b84ed788a9a9db35ac2ed9f995fb6da436e47ea42da2907c139bdd"),
    ("assur2/glasswater-defense", "org.weare.glasswaterdefense", "Glasswater Defense",
     "Defend a canal lock across 12 waves", "Games",
     "de0385f0c407af4c4462121a66ec330f27a17d3f5ab52742338178e5bc1f2de4"),
    ("assur2/clover-card-room", "org.weare.clovercardroom", "Clover Card Room",
     "Play Poker, Hearts, Klaverjassen, Solitaire and Switchyard offline", "Games",
     "227f6eaaedd67b44bed93d1d101cbae3d9b1f749c06c78d0c73e8ced89334202"),
    ("assur2/ritwijzer", "org.weare.ritwijzer", "Ritwijzer",
     "Plan je autoroute en vind verkeersinformatie, laadpunten en parkeerplaatsen", "Navigation",
     "320ea41680186e62056362e95c9aec36180d84a216200bb962957431b8830092"),
    ("assur2/wachterlicht", "org.weare.wachterlicht", "Wachterlicht",
     "Verdedig de vuurtoren tegen acht golven mechanische krabben", "Games",
     "ab696749b945deb7a33e5fa5ae62dc4546e83d9b965263e465a7e4508d46de93"),
]

ARTIFACT_STORES = {
    "assur2/wachterlicht": "WACHTERLICHT_ARTIFACTS",
    "assur2/ritwijzer": "RITWIJZER_ARTIFACTS",
    "assur2/opvang": "OPVANG_ARTIFACTS",
    "assur2/glasswater-defense": "GLASSWATER_ARTIFACTS",
    "assur2/clover-card-room": "CLOVER_ARTIFACTS",
}


def output(*args):
    return subprocess.check_output(args, text=True)


def releases(source, app_id):
    if source in ARTIFACT_STORES:
        store = Path(os.environ[ARTIFACT_STORES[source]])
        packages = []
        for apk in store.glob(f"{app_id}_*.apk"):
            code = int(apk.stem.split("_", 1)[1])
            if not 0 < code <= 999_999_999 or not apk.with_name(f"{apk.stem}_src.tar.gz").is_file():
                raise ValueError(f"Incomplete or invalid staged release: {apk.name}")
            major, rest = divmod(code, 1_000_000)
            minor, patch = divmod(rest, 1000)
            packages.append((code, f"v{major}.{minor}.{patch}"))
        return sorted(packages, reverse=True)[:3]

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


def collect(source, app_id, name, summary, category, signer, versions):
    import yaml

    tools = Path(os.environ["ANDROID_HOME"]) / "build-tools/35.0.0"
    names = []
    for code, tag in versions:
        apk = Path("repo") / f"{app_id}_{code}.apk"
        archive = apk.with_name(f"{apk.stem}_src.tar.gz")
        if source in ARTIFACT_STORES:
            store = Path(os.environ[ARTIFACT_STORES[source]])
            shutil.copyfile(store / apk.name, apk)
            shutil.copyfile(store / archive.name, archive)
        else:
            subprocess.run(["gh", "release", "download", tag, "--repo", source,
                            "--pattern", name.replace(" ", ".") + ".apk", "--output", apk], check=True)
            with archive.open("wb") as file:
                subprocess.run(["gh", "api", f"repos/{source}/tarball/{tag}"], stdout=file, check=True)
        certs = output(tools / "apksigner", "verify", "--print-certs", apk)
        actual = re.findall(r"^Signer #\d+ certificate SHA-256 digest: (\w+)$", certs, re.MULTILINE)
        if actual != [signer]:
            raise ValueError(f"Unexpected APK signer for {source}@{tag}")
        info = output(tools / "aapt", "dump", "badging", apk)
        identity = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", info, re.MULTILINE)
        if not identity or identity.groups() != (app_id, str(code), tag[1:]):
            raise ValueError(f"Unexpected APK identity for {source}@{tag}")
        names.append(apk.name)

    latest_code, latest_tag = versions[0]
    metadata = dict(Name=name, Summary=summary, Description=summary,
                    License="GPL-3.0-only", Categories=[category],
                    SourceCode=f"{os.environ['FEED_URL']}/{app_id}_{latest_code}_src.tar.gz",
                    CurrentVersion=latest_tag[1:], CurrentVersionCode=latest_code, AllowedAPKSigningKeys=[signer])
    Path(f"metadata/{app_id}.yml").write_text(yaml.safe_dump(metadata))
    return names


def main():
    versions = {app_id: tags for source, app_id, *_ in APPS
                if (tags := releases(source, app_id))}
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        indexed = json.loads(Path(sys.argv[2]).read_text())["packages"]
        removed_package = "us.mitene"  # Albumvenster was withdrawn from distribution.
        missing_apps = set(indexed) - versions.keys() - {removed_package}
        if missing_apps:
            raise ValueError(f"Catalog configuration would remove existing apps: {sorted(missing_apps)}")
        expected = {app_id: {code for code, _ in tags} for app_id, tags in versions.items()}
        actual = {app_id: {int(item["versionCode"]) for item in items} for app_id, items in indexed.items()}
        for app_id, published in actual.items():
            if app_id == removed_package:
                continue
            desired = expected[app_id]
            if max(desired) < max(published) or published - desired and len(desired) < 3:
                raise ValueError(f"Release inputs would roll back or drop retained releases for {app_id}")
        print("true" if expected != actual else "false")
        return
    if len(sys.argv) != 1:
        raise SystemExit("Usage: catalog.py [--check index-v1.json]")
    Path("repo").mkdir()
    Path("metadata").mkdir()
    expected = [name for app in APPS if app[1] in versions
                for name in collect(*app, versions[app[1]])]
    Path("expected-apks.txt").write_text("\n".join(expected))


if __name__ == "__main__":
    main()

