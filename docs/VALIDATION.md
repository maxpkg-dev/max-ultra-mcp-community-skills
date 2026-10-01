# Validation and security boundaries

`tools/validate.py` independently implements the public instruction-only import contract
observed in Max Ultra MCP's `core/skill-store.js`, `core/skill-zip.js`,
`docs/CUSTOM_SKILLS.html`, and `docs/SUBMIT_SKILL.html` on 2026-10-01.
The product implementation credits Lukianenko Vasyl / 3DGROUND. No product source is
vendored and this repository has no runtime dependency on a product checkout.

Limits: 200 files, 50 MiB expanded, 54 MiB ZIP, 64 KiB SKILL.md, 1 MiB per supporting
text file, and 5 MiB per image. Only STORE and DEFLATE classic unencrypted ZIPs are
accepted. ZIP64, split archives, duplicate/case-conflicting paths, special files,
symlinks/reparse points, path escapes, unexpected roots, and unsupported files fail.
Folder depth and UTF-8 text are checked. Relative Markdown links must resolve inside
the package. Native shell preprocessing and @file inclusion are rejected.

Catalog policy additionally rejects common private machine-path patterns and multiple
SKILL.md files in folders. It is deliberately conservative; this is not a complete
Markdown parser or a byte-for-byte reimplementation of every importer diagnostic.
Remote URLs are not fetched; images are not analyzed for private content; referenced
vendor claims, artistic quality, intellectual-property rights, and prompt behavior need
human review. Structural validation never grants permissions or proves practical usability.

Input ZIPs are validated in memory before staging. They are never executed. Extraction
writes only validated files into a new destination. Deterministic release ZIPs use fixed
timestamps, sorted paths, fixed permissions, and STORE compression so runtime compressor
versions cannot alter bytes. Metadata, generated docs, and review notes are excluded.

## GitHub schema references

Checked against official documentation on 2026-10-01:

- [Issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [Form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema): upload accepts `label`/`description` attributes and `required`/`accept` validations.
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Deployment environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)

Local tests parse YAML with pinned PyYAML and verify the used form fields and security configuration. GitHub remains the
final runtime/schema authority; remote Actions and the live Issue Form need verification
after repository activation. These checks are scoped assertions, not an official offline GitHub schema validator.
