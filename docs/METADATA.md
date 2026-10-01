# Catalog metadata

One `skills/<id>/metadata.json` drives the README row and detail page. Validation rejects unknown or missing fields. Use the initial skill's metadata as a concrete example; replace its attribution and evidence rather than copying claims.

| Field | Meaning |
| --- | --- |
| schemaVersion | Integer `1` |
| id | Directory name and SKILL.md machine name; lowercase hyphenated, at most 64 characters |
| title | Human-facing title, including author where appropriate |
| version | Stable `X.Y.Z`; do not change released package bytes under an existing version |
| publishedVersion | Latest confirmed public stable version for this skill, or null before first publication; never newer than `version` |
| category | Architectural visualization, Modeling, Materials, Lighting, Cameras, Scene preparation, or Other |
| purpose | Concise description of the outcome |
| usage | Object with nonempty `steps` and `examples` arrays (up to 10 each), plus `expectedOutput`; generates the How to use section |
| author | Object with `name` and HTTPS `profile` (or null profile) |
| submitter / reviewer | Same person object, or null if identity is not recorded; never infer from the author |
| dependencies | Array of explicit requirements and conditional plugin requirements |
| testedVersions | Array of actual software/version tests; empty when untested |
| verification | Object with `level` and specific `evidence` |
| terms | Object with separate `distribution`, `adaptation`, and `evidence` text |
| provenance | Source history and attribution limits, without local machine paths |
| submission | Public HTTPS issue/PR URL or null for a prepared initial contribution |
| packageSha256 | Content fingerprint printed by `inspect`; binds reviewed metadata to exact package bytes |

Verification levels are `package-validated`, `discovery-reported`, and `practically-tested`.
All packages pass structural validation. Discovery is an attributed report of import/list
visibility. Practical testing requires a named reviewer, tested versions, and evidence
describing the task/result. These are maintained claims, not certifications produced by CI.

The fingerprint hashes a sorted UTF-8 JSON inventory of paths, byte counts, and per-file
SHA-256 hashes. It is different from the SHA-256 of the finished ZIP. Both are deterministic.
Package bytes are exempt from Git line-ending normalization to retain source fidelity.

Download links are derived from the skill ID and `publishedVersion`, using GitHub's
`releases/download/<skill-tag>/<skill-asset>` URL. No repository-global latest-release
link is used. Bumping `version` leaves the previous `publishedVersion` in place; a pending
version cannot produce a premature download link. After publishing, run
`python tools/catalog.py confirm-publication <id>` and commit its metadata/generated-page
changes to main where permitted, or through a PR when required. This read-only GitHub check
verifies the public stable release,
ZIP bytes, and checksum against the reviewed current package before changing local links.
