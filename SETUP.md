# Notes releases

Notes uses Jetpack Compose, application ID `org.weare.notes`, and GPL-3.0-only.
The Notes app and catalog builder repositories are private. The public repository
[assur2/notes-feed](https://github.com/assur2/notes-feed) hosts the signed F-Droid feed
and the corresponding source archive from the Git tag of every distributed version.

## CI
Every branch push runs unit tests and lint. Pull requests and version tags additionally
run the Android emulator. Non-release tag pushes run the fast checks. Pushes to a branch
with an open pull request can have both a push run and a PR run.

## Signing and hosting
The Notes repository holds two tag-restricted GitHub Actions environments.
`android-release` contains the APK keystore and password. `catalog-signing` contains
the separate catalog keystore and password and the SSH deploy key for notes-feed.
The catalog action is fetched from the private fdroid-repo repository by commit SHA.
The Notes workflow reads its own release assets with a job-scoped token. The feed
publisher can push to the public feed repository using its dedicated deploy key.
The public Pages workflow publishes only the site directory.

The Notes repository variables are APP_ID, APK_SHA256, CATALOG_SHA256, FEED_REPO and FEED_URL.
The two signing certificates are long-lived. Keep the original private signing keys
and recoverable passwords backed up outside Git. Replacing either changes identity.

## Release
Tag a reviewed main commit with vMAJOR.MINOR.PATCH (each component 0..999, increasing).
For example, push v0.1.0 to create the first release. CI assigns Android versionCode 1000.
After tests pass the workflow signs the APK, creates a private GitHub Release,
builds a signed catalog from the three latest stable releases, and pushes the feed
plus source archives to notes-feed. Check the public repository's Pages deployment
for final publication status. Re-run failed jobs if the catalog job fails after
the GitHub Release exists.

[Download page](https://assur2.github.io/notes-feed/).
The first release creates the subscription link and signed index. To check upgrades,
install the first release through F-Droid, save a note, publish the next version,
and confirm the note opens after upgrading.
