# Notes releases

Notes uses Jetpack Compose, application ID `org.weare.notes`, and GPL-3.0-only.
The Notes app repository is private. The public catalog repository
[assur2/fdroid](https://github.com/assur2/fdroid) hosts the signed F-Droid feed
and the corresponding source archive from the Git tag of every distributed version.

## CI
Run unit tests and lint from Actions > Test Notes > Run workflow. Select the emulator
option to include the Android editor test. Tests run only on manual request.

## Signing and hosting
The Notes repository holds two tag-restricted GitHub Actions environments.
`android-release` contains the APK keystore and password. `catalog-signing` contains
the separate catalog keystore and password and the SSH deploy key for fdroid.
The catalog action is fetched from the public fdroid repository by commit SHA.
The Notes workflow reads its own release assets with a job-scoped token. The feed
publisher can push to the public feed repository using its dedicated deploy key.
The public Pages workflow publishes only the site directory.

The Notes repository variables are APP_ID, APK_SHA256, CATALOG_SHA256, FEED_REPO and FEED_URL.
The two signing certificates are long-lived. Keep the original private signing keys
and recoverable passwords backed up outside Git. Replacing either changes identity.

## Release
Tag a reviewed main commit with vMAJOR.MINOR.PATCH (each component 0..999, increasing).
For example, push v0.1.0 to create the first release. CI assigns Android versionCode 1000.
The release workflow builds and signs the APK, creates a private GitHub Release,
builds a signed catalog from the three latest stable releases, and pushes the feed
plus source archives to fdroid. Check the public repository's Pages deployment
for final publication status. Re-run failed jobs if the catalog job fails after
the GitHub Release exists.

[Download page](https://assur2.github.io/fdroid/repo/) · [Release source archives](https://github.com/assur2/fdroid/tree/main/site/repo) (files ending in `_src.tar.gz`).
The first release creates the subscription link and signed index. To check upgrades,
install the first release through F-Droid, save a note, publish the next version,
and confirm the note opens after upgrading.
