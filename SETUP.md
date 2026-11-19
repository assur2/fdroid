# Notes release starter

Copy the contents of `notes/` and `fdroid-repo/` (including hidden files) into two separate **private** GitHub repositories. Use `main` as the default branch of both. This starter uses Android-only Jetpack Compose, a single app-private UTF-8 file and a Save button. Android removes this file on uninstall. A shared folder picker and multi-note UI can be added independently of these workflows. Notes is licensed under the GNU General Public License, version 3 only (GPL-3.0-only). See `notes/LICENSE`.

## 1. Pick the Android ID and build locally

Replace `applicationId = "org.example.notes"` in `notes/app/build.gradle.kts` with your permanent unique ID before the first release. The internal Kotlin namespace can stay as supplied. For a local build install JDK 17, Android SDK platform 35, Build Tools 35.0.0 and Gradle 8.11.1. Set ANDROID_HOME to your SDK. From the notes repository run:

```sh
gradle :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

With an Android test device connected, `gradle :app:connectedDebugAndroidTest` runs the editor test. CI installs the exact Gradle version directly via Gradle's setup action. CI runs unit tests, lint and the Android emulator test on every pull request to the repository, push to main and release tag. Emulator testing runs on a hosted Linux VM.

## 2. Create two independent signing identities

From a private directory outside both checkouts, use the JDK's keytool. These commands prompt for the passwords. Use a different password per store. Each PKCS12 key uses its store's password.

```sh
keytool -genkeypair -storetype PKCS12 -keystore notes.p12 -alias notes -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=Notes Android"
keytool -genkeypair -storetype PKCS12 -keystore catalog.p12 -alias catalog -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=Notes Repository"
keytool -list -v -keystore notes.p12 -alias notes
keytool -list -v -keystore catalog.p12 -alias catalog
```

Keep encrypted backups of both stores and their passwords. From each listing, copy its certificate SHA256 fingerprint and remove all colons. The **notes** fingerprint goes into APK_SHA256. The **catalog** fingerprint goes in the public subscription link. Keep both identities across releases.

## 3. Configure GitHub

Create these environments under each repository's Settings → Environments. Restrict `android-release` to release tags matching `v*`, and `catalog-signing` and `github-pages` to `main`. Set a tag ruleset so only trusted maintainers can create or change release tags. Protect the catalog's default branch, which contains the workflow that uses the catalog key. If you want unattended publishing, leave required reviewers off.

| Repository | Environment | Environment secrets |
|---|---|---|
| notes | android-release | APK_KEYSTORE_B64, APK_PASSWORD, CATALOG_DISPATCH_TOKEN |
| fdroid-repo | catalog-signing | CATALOG_KEYSTORE_B64, CATALOG_PASSWORD, NOTES_RELEASE_READ_TOKEN |

For the two B64 secrets use the Base64 encoding of the entire corresponding PKCS12 file. For example, from the private key directory in **PowerShell**, after authenticating GitHub CLI, pipe the encoding directly to the right secret:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path notes.p12))) | gh secret set APK_KEYSTORE_B64 --repo OWNER/notes --env android-release
[Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path catalog.p12))) | gh secret set CATALOG_KEYSTORE_B64 --repo OWNER/fdroid-repo --env catalog-signing
```

Create a fine-grained personal access token for **only the fdroid-repo repository**, granting **Actions: write**. Save it in notes as CATALOG_DISPATCH_TOKEN. It only needs to start the catalog workflow. A normal workflow token from notes is scoped to notes. Replace the dispatch token before its expiration.

In **Settings → Secrets and variables → Actions → Variables**, set these **repository variables**:

| Repository | Variable | Example |
|---|---|---|
| notes | CATALOG_REPO | OWNER/fdroid-repo |
| notes and fdroid-repo | APK_SHA256 | 64 hex digits from notes.p12, no colons |
| fdroid-repo | NOTES_REPO | OWNER/notes |
| fdroid-repo | APP_ID | your actual Android applicationId |
| fdroid-repo | FEED_URL | https://OWNER.github.io/fdroid-repo/fdroid/repo |

In fdroid-repo, select **Settings → Pages → Build and deployment → Source → GitHub Actions**. Push both repositories to main before tagging. For the catalog to download private APKs, create a fine-grained token scoped to notes with Contents read permission and save it as NOTES_RELEASE_READ_TOKEN in the catalog-signing environment. Private repository Pages hosting requires an eligible GitHub plan. Enabling and deploying Pages can publish the APKs and catalog publicly. Before distributing GPLv3 binaries, provide recipients with access to the corresponding source for each release. If your organization restricts third-party actions, allow Gradle's setup action and ReactiveCircus's emulator action, or substitute your own runner steps. For release hardening, pin action references to reviewed full commit SHAs and update them with Dependabot.

## 4. Publish and install the first version

Run in the notes repository on a reviewed commit already pushed to main:

```sh
git tag -a v0.1.0 -m "First Notes release"
git push origin v0.1.0
```

The release workflow tests the tagged commit, produces an unsigned release APK, signs it in a separate job, checks the certificate and attaches Notes.apk to the GitHub Release. Its last job dispatches publish.yml in fdroid-repo. **A successful dispatch means the catalog job has started. Check the catalog repository's Actions run for actual deployment success.**

The catalog workflow downloads up to three most recent stable releases ordered by numeric version, verifies each APK's certificate, application ID, version name and version code, signs the index, checks that every expected APK is indexed, and deploys the complete feed to Pages. GitHub Releases retains the older APKs. Prereleases and drafts are skipped. Keep release tags and published assets immutable.

Put this link in your app README, replacing OWNER and the fingerprint with yours:

```text
https://OWNER.github.io/fdroid-repo/fdroid/repo?fingerprint=CATALOG_SHA256_WITHOUT_COLONS
```

Open it with F-Droid or paste it under Repositories, confirm the repository and install Notes. Write and save a note.

## 5. Publish an update

Tag a later commit `v0.1.1` and push that tag exactly as above. Each component of vMAJOR.MINOR.PATCH must be 0..999, with no leading zeroes. The version code is major × 1,000,000 + minor × 1,000 + patch (v0.1.0 → 1000 and v0.1.1 → 1001). Use increasing versions. Once the catalog deployment succeeds, refresh F-Droid, update the installed Notes app, and reopen the saved note. Background checks and unattended install timing depend on the client settings and Android version.

If the GitHub Release already exists but dispatch or catalog publication fails, fix the configuration and use **fdroid-repo → Actions → Publish Notes catalog → Run workflow → main**. This rebuilds the feed from published APKs. A failed catalog build leaves the last successful Pages deployment serving users. For a defective public app release, ship a higher patch version.

## References

- [Create a custom binary F-Droid repository](https://f-droid.org/en/docs/Setup_an_F-Droid_App_Repo/)
- [F-Droid signing identities](https://f-droid.org/en/docs/Signing_Process/)
- [Dispatching a GitHub Actions workflow](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
- [GitHub Pages deployment workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Android APK signing and verification](https://developer.android.com/tools/apksigner)
