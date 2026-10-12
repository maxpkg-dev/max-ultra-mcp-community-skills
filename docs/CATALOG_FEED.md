# Community Skills install feed

Public endpoint: <https://maxpkg-dev.github.io/max-ultra-mcp-community-skills/catalog.json>

Manual browsing and ZIP import remain available through the
[catalog website](https://maxpkg-dev.github.io/max-ultra-mcp-community-skills/).
The feed is for a supporting Max Ultra MCP build's Community Skills install interface;
publishing the feed does not update the installed product.

The response is UTF-8 JSON, with exactly `schemaVersion` (integer `1`) and `skills`
(an array, sorted by ID). Each entry contains exactly:

| Field | Type and meaning |
| --- | --- |
| id | Lowercase hyphenated catalog ID, at most 64 characters |
| name | SKILL.md machine name; equals id |
| title | Nonempty display title, at most 160 UTF-16 code units |
| description | Nonempty display description, at most 1024 UTF-16 code units |
| author | Nonempty author credit string, at most 256 UTF-16 code units |
| version | Stable MAJOR.MINOR.PATCH string, no leading zeroes or suffixes |
| downloadUrl | Absolute HTTPS URL for the immutable numbered ZIP in this repository |
| sha256 | 64 lowercase hexadecimal characters; SHA-256 of downloaded ZIP bytes |
| sizeBytes | Positive integer, ZIP byte length, at most 56,623,104 (54 MiB) |

Text fields contain no ASCII controls. Each ID appears once. No credentials, author
contacts, installation paths, executable commands, or rights records are in the feed.
The URL is constructed exactly as:

```text
https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/releases/download/<id>-v<version>/<id>-<version>-max-ultra-mcp.zip
```

The feed intentionally uses numbered assets, not the mutable `-latest` alias. A cached
feed therefore still identifies matching bytes after a newer version is released.
HTTPS asset redirects are normal GitHub download behavior; clients must enforce their
own safe download/redirect rules and verify the final size and SHA-256 before import.
The checksum is an integrity check, not a cryptographic author signature. Apply normal
ZIP and instruction-only import validation even after the hash matches.

## Publication evidence and generation

`catalog.json` is generated, never maintained by hand. An optional `publishedPackage`
snapshot in each external `metadata.json` stores exactly one feed entry. Only
`confirm-publication <id>`, after checking the public stable numbered release,
uploaded ZIP/checksum, and permanent alias against reviewed deterministic package
bytes, records or advances that snapshot. Existing releases are initialized with the
same command. No network checks or imported instructions run during ordinary generation.

`generate`, `check`, and `build` validate snapshots and generate/check the feed with the
Markdown catalog. A `publishedVersion` value alone is insufficient: records without a
verified snapshot are omitted. While a new source version is pending, the old snapshot
and immutable URL remain unchanged; pending titles, versions, and local ZIP hashes do
not enter the feed. The snapshot version must equal `publishedVersion`, and its ID/name,
URL, checksum, and size must meet the schema. When it represents the current source
version, its complete contents must also match the current deterministic package.

The normal numbered-release/download-refresh workflow records the snapshot and commits
`catalog.json` alongside confirmed metadata using a normal push. GitHub Pages deploys
that accepted feed. CI rejects stale generated output. Do not edit a snapshot to claim
unverified publication. Review remains necessary: local validation cannot independently
prove the historical remote checks recorded in a committed snapshot.

Removing a skill from the catalog removes its feed entry without deleting old releases.
Feed-only changes do not revise any skill ZIP or numbered release.
