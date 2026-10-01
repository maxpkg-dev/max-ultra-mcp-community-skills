# Add and publish a skill manually

You can contribute or publish without an AI assistant. Choose the route that matches your access:

| Your situation | Route | What you need |
| --- | --- | --- |
| You are an author or contributor proposing a skill | [Submit through your browser](#a-submit-through-your-browser) | GitHub account, skill ZIP or public link, author and permission information |
| You own this repository and will prepare a reviewed release | [Prepare and publish as the owner](#b-prepare-and-publish-as-the-repository-owner) | Repository write/release access, local Git and Python, browser, required reviews |

An issue attachment is a proposal. A ZIP added to the repository is not a catalog release.
The owner route below creates reviewed source, an individual release ZIP, and a working
Download ZIP button in separate, explicit steps. No assistant is required for either route.

## A. Submit through your browser

1. Sign into GitHub and open [Submit a skill](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/issues/new?template=submit-skill.yml).
2. Fill in the title/version, purpose and example task, category, author credit and optional
   public profile. Explain your relationship to the author if you are submitting their work.
3. List dependencies and exact versions you actually tested. Say untested where appropriate;
   importing a ZIP or seeing a skill in the list is not a practical scene test.
4. Attach one skill ZIP in the upload field, or provide a public HTTPS ZIP link. The form's
   archive upload limit is 25 MB; use a link for larger packages within the importer's limits.
   If you only have a folder, prepare a ZIP with the layout shown below, without unrelated files.
5. Describe distribution permission, adaptation limits, source history, and third-party
   material. Distinguish direct written permission from permission reported by someone else.
   Do not upload private correspondence or claim a license you do not have.
6. Complete the submission checks and submit the issue. Keep its link and respond to reviewer
   questions there. A maintainer handles acceptance and publication; submitting does not
   immediately add the skill to the catalog.

You do not need Git, Python, a branch, or a release permission for this browser-only route.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for contributor expectations.

## B. Prepare and publish as the repository owner

The commands below use **PowerShell**, from the root of your local repository. Replace the
example ID/version and input paths with your own values. Run each block in order and stop
if a command fails; do not continue to publication after an error. If a review, write access,
or environment approval is required, obtain it through the normal repository process.

This walkthrough assumes the default branch is `main`, as it is in this repository. If it
changes, substitute the actual default branch. Use the same checkout throughout; no extra
worktree is needed. Work directly on main when repository rules permit: no new branch or PR
is required by this owner workflow. If protection requires a PR, use that required review
path instead; never bypass it. Do not overwrite unrelated local changes to make commands succeed.

### 1. Gather the material and prepare your tools

Keep the original folder/ZIP unchanged. Have these facts ready:

- Author's public credit name and optional public HTTPS profile.
- Skill purpose, dependencies, intended inputs, and three or four useful example requests.
- Distribution permission and whether adaptation is allowed; what evidence supports that.
- Version and any known package/import/practical test results, with exact software versions.
- Whether this is a new skill or an update to an existing catalog entry.

Install Git and Python 3.12 or later if necessary. Open PowerShell in your existing checkout.
If you do not have a checkout, clone it once into a location you choose:

```powershell
git clone https://github.com/maxpkg-dev/max-ultra-mcp-community-skills.git
Set-Location max-ultra-mcp-community-skills
```

Check your tools and synchronize a clean checkout:

```powershell
python --version
git --version
git status --short
git remote -v
git fetch origin
git switch main
git pull --ff-only origin main
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

If `python` is unavailable on Windows but `py -3` works, use `py -3 -m venv .venv` to create
the environment. Later commands use its explicit interpreter, so activation is unnecessary.
If Git reports existing changes, preserve or finish them before switching/pulling. If a
fast-forward is impossible, resolve the divergence before continuing; do not reset or force it.

Set the new skill's ID and version once for this PowerShell session:

```powershell
$skillId = 'example-skill-author'
$skillVersion = '1.0.0'
$skillDirectory = "skills/$skillId"
$packageDirectory = "$skillDirectory/package"
$releaseTag = "$skillId-v$skillVersion"
$assetName = "$skillId-$skillVersion-max-ultra-mcp.zip"
New-Item -ItemType Directory -Force .staging | Out-Null
```

For an update, use its existing stable ID and a new version whenever released package bytes
change. Retain older public releases. Before proceeding, inspect [existing releases](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/releases)
and existing metadata; never reuse a public tag for different content.

### 2. Inspect the folder or ZIP

Use **one** of these alternatives. The staging destination must be new; use a different
review-directory name if a previous attempt already exists.

**Starting from a ZIP:** copy the received archive into `.staging/incoming.zip`, then run:

```powershell
& .venv/Scripts/python.exe tools/catalog.py inspect .staging/incoming.zip
if ($LASTEXITCODE -ne 0) { throw 'Package validation failed.' }
& .venv/Scripts/python.exe tools/catalog.py stage .staging/incoming.zip .staging/reviewed-package
```

**Starting from a folder:** replace the quoted source path below, validate it, and copy it
into a new review location:

```powershell
$sourceFolder = 'REPLACE WITH THE FULL PATH TO YOUR SKILL FOLDER'
& .venv/Scripts/python.exe tools/catalog.py inspect "$sourceFolder"
if ($LASTEXITCODE -ne 0) { throw 'Package validation failed.' }
if (Test-Path .staging/reviewed-package) { throw 'Choose a new staging destination.' }
Copy-Item -LiteralPath "$sourceFolder" -Destination .staging/reviewed-package -Recurse
```

The importable package has this layout; references and assets are optional:

```text
SKILL.md
references/
  workflow.md
assets/
  example.png
```

`SKILL.md` begins with only a single-line `name` and `description`, followed by instructions:

```markdown
---
name: example-skill-author
description: Author Name - Explain what this skill does and when to use it.
---

# Example Skill (Author Name)

Explain the intended task, required inputs, workflow, and limits here.
```

The real machine name must match your ID. A ZIP can have this root or one enclosing folder.
Use only allowed text under `references/` and images under `assets/`; no extra root files,
scripts, linked files, or nested archives. Consult [VALIDATION.md](VALIDATION.md) for the
canonical file types, frontmatter rules, and size limits instead of guessing a layout.

Read the staged content and inspect images. Remove private data and material you cannot
redistribute; preserve author attribution and provenance. Make any permitted adaptation in
the staged copy, not the original. Do not execute imported instructions as code. If structural
validation fails, fix the reported problem within your rights and rerun `inspect`.

### 3. Place the reviewed package and write metadata

For a **new skill**:

```powershell
if (Test-Path "$skillDirectory") { throw 'Existing skill: follow the update instructions.' }
New-Item -ItemType Directory -Path "$skillDirectory" | Out-Null
Copy-Item -LiteralPath .staging/reviewed-package -Destination "$packageDirectory" -Recurse
```

For an **update**, preserve the current package in a new ignored backup directory, then
replace `skills/<id>/package/` with the reviewed folder using your file manager. Do not merge
folders blindly: files removed in the update must not survive accidentally. Keep the existing
metadata file, author, and ID; edit the version, changed facts, and fingerprint as needed.

Now run:

```powershell
& .venv/Scripts/python.exe tools/catalog.py inspect "$packageDirectory"
```

Copy its `packageSha256` value. In your editor, create `skills/<id>/metadata.json` next to
`package/`, not inside it. Use this complete starter, replacing every example and placeholder
with accurate information. The example is not a license or permission statement:

```json
{
  "schemaVersion": 1,
  "id": "example-skill-author",
  "title": "Example Skill (Author Name)",
  "version": "1.0.0",
  "publishedVersion": null,
  "category": "Architectural visualization",
  "purpose": "Replace with the skill's actual purpose.",
  "usage": {
    "steps": [
      "Replace with import/new-chat guidance and any explicit skill-selection request.",
      "Describe required images, references, intent, constraints, and connected tools if needed."
    ],
    "examples": [
      "Replace with a concrete natural request appropriate to this skill.",
      "Add more short examples covering its main tasks."
    ],
    "expectedOutput": "Describe the expected response and distinguish advice from authorized scene changes."
  },
  "author": {"name": "Author Name", "profile": null},
  "submitter": null,
  "reviewer": null,
  "dependencies": ["Replace with actual requirements or an explicit statement of none."],
  "testedVersions": [],
  "verification": {
    "level": "package-validated",
    "evidence": "Describe the package checks actually performed; state that practical testing was not performed if applicable."
  },
  "terms": {
    "distribution": "Replace with the actual distribution permission and limits.",
    "adaptation": "Replace with the actual adaptation permission or its absence.",
    "evidence": "State who authorized what and whether evidence is direct or reported."
  },
  "provenance": "Describe the source and any adaptation without private local paths.",
  "submission": null,
  "packageSha256": "PASTE THE FINGERPRINT PRINTED BY INSPECT"
}
```

Use [METADATA.md](METADATA.md) for allowed categories and field rules. Add known public author
profiles; leave unknown identities null. Author, submitter, and reviewer are separate roles.
An owner-supplied package does not need an issue; do not invent one. There is no blanket
license for all skills. Write public metadata and instructions in English.

The `usage` fields generate **How to use** on the detail page. Include practical inputs,
three or four natural requests, expected output, and scene-authorization limits where relevant.
Do not hand-edit that generated page. Keep `testedVersions` empty if untested; use
`discovery-reported` only for attributed import/list evidence. Use `practically-tested` only
with actual task results, versions, and a recorded reviewer as required by the schema.

For a new skill, keep `publishedVersion` null. For an update, retain the previous confirmed
published version. The newer download will be enabled only after step 7 verifies publication.

### 4. Generate, test, and build

```powershell
& .venv/Scripts/python.exe tools/catalog.py validate
& .venv/Scripts/python.exe tools/catalog.py generate
& .venv/Scripts/python.exe -m unittest discover -s tests -v
& .venv/Scripts/python.exe tools/catalog.py check
& .venv/Scripts/python.exe tools/catalog.py build
Get-Content dist/manifest.json
Get-Content "dist/$assetName.sha256"
Get-FileHash -LiteralPath "dist/$assetName" -Algorithm SHA256
```

All checks must pass. Inspect the generated README row and `docs/skills/<id>.md`, especially
credit, usage, rights, and verification. The build creates **one ZIP per skill/version**,
plus checksums and a manifest; upload only the target skill's files. The archive must contain
only its importable package. Its checksum file and manifest must agree with the actual ZIP.
`packageSha256` is a source-content fingerprint; it is not the ZIP file's SHA-256.

### 5. Review the source, commit, and push main

Before running the block, review the package, permission evidence, and generated catalog.
Commit only after all local checks pass.

```powershell
git add "$skillDirectory" README.md "docs/skills/$skillId.md"
git diff --cached --check
git diff --cached --stat
git commit -m "Add $skillId $skillVersion to the catalog"
git push origin main
```

Before committing, review the source, attribution, rights, usage, and generated pages. Do
not commit `.staging/`, `.venv/`, `dist/`, original ZIPs, or private reports. After pushing,
open GitHub Actions and wait for **Validate catalog** to pass for your commit. If a direct
push is rejected by branch protection, stop and follow the repository's required PR/review
process; do not force the push or bypass required reviews.

Once the reviewed source is on main and checks pass, rebuild from that accepted state:

```powershell
git switch main
git pull --ff-only origin main
$acceptedCommit = git rev-parse HEAD
& .venv/Scripts/python.exe tools/catalog.py check
& .venv/Scripts/python.exe tools/catalog.py build
```

The rebuilt metadata version must still equal `$skillVersion`. If another change updated
that skill meanwhile, stop and re-establish which accepted version you are publishing.

### 6. Create the release and upload its two assets

First check [Actions](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/actions)
and [Releases](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/releases).
If the configured **Publish accepted skills** workflow already published this exact version,
skip creating another release and proceed to step 7. If it is running, let it finish. If
repository policy requires that protected workflow, follow [MAINTAINERS.md](MAINTAINERS.md)
and its approvals rather than using browser publication to bypass them.

The following is the manual browser path for a maintainer permitted to publish directly.
Pin the release to the accepted commit first. Check whether the tag already exists:

```powershell
git fetch origin --tags
git ls-remote --tags origin "refs/tags/$releaseTag" "refs/tags/$releaseTag^{}"
```

If output appears, inspect the existing tag/release: do not recreate or move it. For an
existing correct public release, proceed to confirmation; for a draft, resume only when its
tag and existing asset bytes are correct. If they differ, stop and investigate, using a new
version for changed public content. If the tag is absent both remotely and locally, create
and push it at the exact accepted commit:

```powershell
git tag "$releaseTag" "$acceptedCommit"
git push origin "refs/tags/$releaseTag"
```

Use these naming rules; the example is an already-published release, not a version to recreate:

| Item | Convention | Existing ArchViz example |
| --- | --- | --- |
| Tag | `<id>-v<version>` | `archviz-master-yuriy-bobak-v1.2.1` |
| Title | `<title> v<version>` | `ArchViz Master - Yuriy Bobak v1.2.1` |
| ZIP | `<id>-<version>-max-ultra-mcp.zip` | `archviz-master-yuriy-bobak-1.2.1-max-ultra-mcp.zip` |
| Checksum | ZIP filename followed by `.sha256` | `archviz-master-yuriy-bobak-1.2.1-max-ultra-mcp.zip.sha256` |

1. Open **Releases**, then **Draft a new release**.
2. In **Choose a tag**, select the exact tag you just pushed. Its commit is already fixed;
   do not create another tag pointing to a moving branch.
3. Fill **Release title** and describe the purpose, author, changes, permission limits, and
   actual test evidence. Include the accepted commit and ZIP checksum from step 4.
4. Attach `dist/<ZIP filename>` and `dist/<ZIP filename>.sha256` in the file attachment area.
   Wait for both uploads, then use **Save draft**. Reopen it and inspect both filenames and sizes.
5. Verify draft assets against your local files. Resume a partial draft only with matching
   existing bytes; do not replace a mismatched/public asset. Keep **This is a pre-release**
   unchecked for this stable catalog version, then click **Publish release**.

These controls follow [GitHub's release instructions](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
GitHub's extra Source code archives are automatic repository snapshots, not the skill ZIP.
The repository-wide latest-release label is not used for catalog downloads; skills advance
independently. A release page alone does not update the README button.

### 7. Verify publication and update the Download ZIP button

From the clean accepted source checkout on main, run:

```powershell
& .venv/Scripts/python.exe tools/catalog.py confirm-publication "$skillId"
& .venv/Scripts/python.exe tools/catalog.py check
git diff -- "$skillDirectory/metadata.json" README.md "docs/skills/$skillId.md"
```

`confirm-publication` reads the public stable release, downloads its ZIP/checksum, compares
them with the deterministic reviewed package, then changes local `publishedVersion` and
regenerates the README/detail page. It does not upload, publish, commit, push, or merge.
If it fails, fix the actual release/source mismatch; do not manually set the pointer to
pretend validation succeeded. A failed network request is not publication confirmation.

If confirmation changes files, commit and push them:

```powershell
git add "$skillDirectory/metadata.json" README.md "docs/skills/$skillId.md"
git diff --cached --check
git commit -m "Confirm $skillId $skillVersion download"
git push origin main
```

Wait for **Validate catalog** on this new commit. Use a follow-up PR only if protection
requires it, then wait for acceptance and synchronize:

```powershell
git switch main
git pull --ff-only origin main
& .venv/Scripts/python.exe tools/catalog.py check
```

If no files changed, the publication was already recorded; there is no need for an empty commit.
Until the confirmation changes reach `main`, the website README still shows the previous
confirmed download, or Publication pending for a first release. There is no automatic
refresh merely from uploading the ZIP.

Open the repository README on `main` and click **Download ZIP** for your skill. It should
start downloading the named skill ZIP directly. Its URL follows this per-skill pattern:

```text
https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/releases/download/<id>-v<version>/<id>-<version>-max-ultra-mcp.zip
```

Do not substitute `/releases/latest`. Check the downloaded file's hash against the checksum,
then use **Skills > Custom > Import ZIPs** in Max Ultra MCP. Start a new AI chat and try a
request from **How to use**. Report only what you actually tested. For replacement of an
existing same-name skill, preserve local changes and follow [INSTALL.md](INSTALL.md).
Updating the catalog link does not automatically update installed copies.

### 8. Finish cleanly

Confirm `git status --short` is clean and local `main` matches GitHub. This direct-main
workflow creates no extra branches or worktrees to clean up. Keep release tags and older
public releases. Keep original sources/backups outside committed package content.
Share the direct ZIP link, author/version, and How to use page, with any remaining test limits.

For future updates repeat the reviewed source -> immutable release -> confirmed catalog
pointer sequence. For catalog-only wording changes, regenerate the pages, review, commit, and push main
where permitted; use a PR only if required. Do not reupload an unchanged public release
just to update its documentation.
