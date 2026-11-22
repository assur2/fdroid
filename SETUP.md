# Weare Apps F-Droid repository

[Add this repository to F-Droid](https://assur2.github.io/fdroid/repo/). The repository certificate SHA-256 fingerprint is `386B766ECB792F3B6061A694306224FD5C49E3D15BCDB9B0DD0B141547F01EB1`.

The catalog includes Notes (`org.weare.notes`), Opvang (`org.weare.opvang`), Glasswater Defense (`org.weare.glasswaterdefense`) and Clover Card Room (`org.weare.clovercardroom`) and Ritwijzer (`org.weare.ritwijzer`). Each app signs its APK with its own key. Stable version tags use vMAJOR.MINOR.PATCH. The publisher collects up to three stable releases per app. It verifies package identity, version and signing certificate, then includes each APK and its tagged source archive in the signed index. App identities and certificate pins are in `catalog.py`.

Catalog signing runs serially in the `catalog-signing` environment in assur2/notes on a reviewed publisher tag. A Notes release dispatches it directly. A twice-hourly workflow also dispatches it. The publisher compares the release set of every app to the live index and skips signing when they match. Run **Check for new app releases** manually to reconcile immediately. GitHub Pages serves the result from `site/`. A failed build or signature check stops publication before the existing feed is replaced.

Opvang, Glasswater Defense, Clover Card Room and Ritwijzer stage each signed GitHub release and matching source archive on their private `fdroid-artifacts` branches. The Notes signing job reads each branch with a dedicated read-only deploy key. The apps use their own repository-scoped Actions tokens to stage releases. Branch pushes retry if two versions are staged at the same time.

To update the publisher, commit changes here, update the commit pin in the Notes catalog workflow, and create a new `v-catalog-*` tag there. Allow the new tag in the Notes catalog signing environment and update the dispatch targets. Retire older publisher tags from the environment when a new app joins so stale snapshots cannot replace the index. The repository signing key stays in its existing environment.


New private apps can be registered before their first APK is staged. The publisher omits them until an artifact branch appears and still refuses to remove any previously published app.

Albumvenster (org.weare.albumvenster) stages its signed offline input test and GPL source on its private fdroid-artifacts branch. The publisher reads it with a dedicated read-only deploy key.
