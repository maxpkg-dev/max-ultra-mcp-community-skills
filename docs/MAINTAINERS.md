# Moderation and publication

## Trust boundary

An issue, attachment, external URL, label, or comment is untrusted input. No issue-triggered
workflow downloads or publishes it. Labels may help humans track work but confer no authority.
Only reviewed repository content merged into the protected default branch is eligible for
release. Review tool/workflow changes particularly carefully: Actions execute repository
tooling, never skill instructions. PR validation has read-only permissions, no secrets, and
does not use `pull_request_target` or a privileged `workflow_run` artifact handoff.

## Accept a submission

1. Read the issue and identify author, submitter, source, dependencies, permission basis,
   and requested adaptation rights. Ask for missing facts in the issue through your own
   normal moderation process. Do not infer rights or testing from a checkbox.
2. Download the supplied ZIP manually to an ignored local staging area. Inspect its origin;
   tooling does not automatically follow arbitrary issue URLs. Never run included instructions.
3. Run `python tools/catalog.py inspect .staging/submission.zip`. Then run
   `python tools/catalog.py stage .staging/submission.zip .staging/reviewed-package`.
   The destination must be new. Validation completes before any archive files are written.
4. Read the staged instructions, references, and images. Check private data, third-party
   material, hidden prompt directives, intended scope, attribution, and permission evidence.
   Record practical tests separately; use `package-validated` when no discovery/test evidence exists.
5. Create a contribution branch, copy only the reviewed package into `skills/<id>/package/`,
   and create metadata using [the field guide](METADATA.md). Keep issue URL, submitter,
   reviewer, and author distinct. Use the fingerprint printed by `inspect`.
6. Run generation, unit tests, catalog check, and build as shown in README. Inspect the
   resulting ZIP and generated author credit. Changes to released bytes require a new version.
7. Open a PR linking the issue. A maintainer reviews package content, permission limits,
   metadata claims, and generated output. Require the **validate** check and review before merge.
8. Merge accepted content. When release automation is enabled, the default-branch push
   builds each version and publishes missing releases after the environment approval.
   Existing published assets must match exactly; they are never overwritten. After the
   release is public, confirm the catalog download as described below. Close the
   submission issue with its accepted PR/release or a clear rejection reason.

The initial ArchViz contribution retains user-reported distribution permission and an
unrecorded reviewer identity. It is prepared for review, not a claim that a named maintainer
has already accepted it. Initial import/discovery evidence is explicitly user-reported.

## Activate after review

Nothing in the local implementation changes GitHub settings or publishes releases.

1. Review and commit this implementation, push its branch, and open/merge a reviewed PR.
2. Enable Issues and Actions on the repository. Verify the Issue Form renders and accepts
   a ZIP or link. Its upload field uses the current GitHub schema; do not invent a `file_types` attribute.
3. Protect the default branch: require PR reviews, dismiss stale approvals, require the
   **validate** check, and restrict direct pushes/bypass permissions. Add actual trusted
   maintainers as code owners for `tools/` and `.github/` if desired; no identities are invented here.
4. Create the **skill-releases** environment, restrict it to the default branch, and require
   a trusted reviewer (prevent self-review where available). Verify environment protections
   are supported and active on your GitHub plan. Do not enable publication without them.
5. Confirm the default branch is `main`. If it differs, update the release workflow's push
   branch filter; its runtime guard always verifies the repository's actual default branch.
6. Set repository Actions variable **ENABLE_SKILL_RELEASES** to the exact string `true`.
   Without it, the release job is skipped. Run **Publish accepted skills** manually on the
   default branch for the first release, and approve the environment after checking the commit.
7. Verify the release contains the per-skill ZIP and checksum, download/import it, then
   complete the download confirmation below. Future accepted default-branch pushes use the same path.

## Advance a skill's direct download

Keep `publishedVersion` at the previous public version when preparing an update, or null
for a new skill. Merge the reviewed package/version first, then publish its release. Only
after the public ZIP and checksum are present, run:

```sh
python tools/catalog.py confirm-publication <skill-id>
```

This command reads GitHub, checks the current version's public stable release and exact
ZIP/checksum bytes, then updates `publishedVersion` and regenerates README/detail links
locally. Review and commit those changes in a follow-up PR. It never publishes, uploads,
pushes, or overwrites release assets. The release workflow does not write to the protected
branch; its log reminds maintainers to complete this confirmation step.

The old direct download remains valid during this two-step publication process. A new
skill has no download button until confirmation. Each skill advances independently; do
not use the repository-wide `/releases/latest` URL. Catalog updates do not update installed
copies. If a release is withdrawn, explicitly revert its pointer or set it to null.

No personal access token, website deployment, Pages hosting, or bot write access to PRs
is required. The release job alone has `contents: write`; its token is supplied only to the
publisher step. Checkout does not persist credentials. All jobs use GitHub-hosted runners.

## Recovery and updates

Re-run a failed release job after inspecting its error. A partial draft resumes uploads only
when existing bytes match, then becomes public. A published release with changed/missing
assets stops for human investigation. Never replace a public version to hide changes.
The first upload uses an immutable commit SHA as its tag target. Metadata-only corrections
regenerate catalog pages without overwriting release assets. Removing a catalog entry does
not delete historical releases; handle withdrawals explicitly with a public explanation.

Disable the repository variable to pause future publication. Local `build` always remains
available without credentials. README generation preserves text outside the catalog markers;
contributors run it before committing and CI fails if generated pages drift. This avoids
privileged bot commits or duplicate hand-maintained tables.
