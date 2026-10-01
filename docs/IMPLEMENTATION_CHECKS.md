# Local implementation checks

Checked on 2026-10-01, before remote publication.

- Unit/integration suite: 27 tests, 26 passed, 1 skipped. The Windows account could not
  create a filesystem symlink; the archive-symlink rejection test passed. The filesystem
  test runs on Linux CI where symlink creation is normally available.
- YAML parsed with PyYAML 6.0.3. Scoped tests check Issue Form fields, pinned actions,
  permissions, credential handling, release gate, and absence of issue-driven publication.
  Field choices were checked against the official GitHub documentation linked in VALIDATION.md.
- Catalog metadata validation, generated-file consistency, deterministic packaging,
  ZIP roundtrip, and Git whitespace checks passed.
- Real product `scanPackage` and `withZipSkill` accepted the prepared folder and the new
  ZIP. Their revisions matched the originally supplied validated ZIP: 84 files,
  179,657 expanded bytes. This was a one-time read-only compatibility check, not a runtime
  dependency or a change to the product repository.
- All original package file bytes and provenance were retained. Public documentation and
  package content were scanned for Cyrillic and common private machine-path patterns;
  none were found. Automated scans do not replace human content review.
- Repeated ZIP builds produced SHA-256
  `7f50c8902906fbfc4331c86174da5362713dc103f04ab49cd37b497979ce2097`.
  ZIP container bytes differ from the original archive because packaging is deterministic;
  the imported file contents match exactly.

Not performed: push, PR creation, merge, repository-setting changes, GitHub Actions runs,
release publication, live Issue Form submission, AI-client behavior tests, or real 3ds Max
scene work. Current discovery evidence remains the user's reported import/list visibility.

The release workflow is gated off until maintainers complete the activation steps in
[MAINTAINERS.md](MAINTAINERS.md). Release links in the catalog are availability searches,
not claims that download assets already exist.
