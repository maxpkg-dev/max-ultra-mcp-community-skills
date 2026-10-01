# Contribute a community skill

Authors receive visible credit in the catalog, detail page, and original package.
Provide a public portfolio or profile if you want a clickable author credit.
The author, submitting GitHub account, and reviewer are separate roles.

## Submit through GitHub

1. Sign into GitHub and select [Submit a skill](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/issues/new?template=submit-skill.yml).
2. Describe the skill, category, dependencies, actual tests, author, and submitter relationship.
3. Attach one ZIP or provide a public HTTPS download link. GitHub's upload field currently limits archives to 25 MB; the importer permits ZIPs up to 54 MiB. Use a link for larger supported packages.
4. State distribution and adaptation terms separately. Explain the basis for permission, including whether it is reported or documented. Do not upload private correspondence or claim rights you do not hold.
5. Submit the issue and discuss reviewer feedback there. Submission does not publish a package or grant a common open-source license.

Use English for public instructions and metadata. Remove private machine paths, credentials, customer scenes, identifying screenshots, and unlicensed source material.
Attach examples only when you have distribution permission. Source books and licensed plugin assets do not belong in a skill package.

## Package contract

Include exactly one `SKILL.md` at ZIP root or within one enclosing folder.
Its frontmatter contains only single-line `name` and `description`. Use a lowercase
hyphenated machine name up to 64 characters. Put MD/TXT/JSON/CSV references under
`references/` and PNG/JPG/JPEG/WebP images under `assets/`.
No scripts, extra root files, nested archives, symbolic links, or client configuration.
See [all limits](docs/VALIDATION.md).

## Pull requests

Experienced contributors can create `skills/<id>/metadata.json` and `skills/<id>/package/`
directly. Include practical usage steps, example requests, and expected output in metadata.
Set `publishedVersion` to null for a new skill; retain the previous value when preparing
an update until its new release is public and confirmed. Use [the metadata guide](docs/METADATA.md); unknown author profiles or review
identities stay `null`. Link the submission issue if one exists.

Run `python tools/catalog.py inspect skills/<id>/package` to get the content fingerprint,
install the test dependency with `python -m pip install -r requirements-dev.txt`,
then run `python tools/catalog.py generate`, `python -m unittest discover -s tests -v`, and
`python tools/catalog.py build`. Commit metadata, instructions, and generated Markdown;
do not commit `dist/`, original ZIPs, reports with private paths, or backups.
Use a new X.Y.Z version for changed released content. Maintainers review both content
and permissions before merging. Do not edit workflow code as part of an ordinary skill submission.
