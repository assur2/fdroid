# Weare Apps F-Droid repository

[Add this repository to F-Droid](https://assur2.github.io/fdroid/repo/). The repository certificate SHA-256 fingerprint is `386B766ECB792F3B6061A694306224FD5C49E3D15BCDB9B0DD0B141547F01EB1`.

The catalog includes Notes (`org.weare.notes`) and Opvang (`org.weare.opvang`). Each application signs its APK with its own key. Stable version tags use vMAJOR.MINOR.PATCH. The publisher collects up to three stable releases **per app**, verifies package identity, version and signing certificate, then places the APK and the corresponding tagged source archive in the signed index. The app name and certificate pins are in `catalog.py`.

Catalog signing runs in the `catalog-signing` environment in assur2/notes on a reviewed publisher tag. A Notes release dispatches it directly. A twice-hourly check in Notes notices new Opvang releases and incomplete publications. Run **Check for new app releases** manually to reconcile immediately. GitHub Pages serves the result from `site/`. A failed build or signature check stops publication before the existing feed is replaced.

To update the publisher, commit changes here, update the commit pin in the Notes catalog workflow, and create a new `v-catalog-*` tag there. Update the dispatch targets in Notes to the new tag. The repository signing key stays in its existing environment.

