# Display metadata inside skill ZIPs

Place UTF-8 `skill.json` beside `SKILL.md`, at the ZIP root or inside the same single
enclosing folder. This file supplies the title, description, author, and version shown
by compatible Max Ultra MCP versions in the skill list and About view. It is display
data, not executable instructions. `source` supplies the declared source label in About;
Built-in/Custom remains the skill type. Older importers may reject this newly supported file.

As of 2026-10-12, this metadata extension has passed targeted compatibility tests in an
updated development build of Max Ultra MCP. That product build is not yet released.
The About fields require a build that supports this schema; publishing these catalog ZIPs
does not update the installed importer. Earlier immutable skill releases remain available
for older importers.

```json
{
  "schemaVersion": 1,
  "title": "Example Skill",
  "description": "Create an editable model from the supplied reference.",
  "author": "Author Name",
  "version": "1.0.0",
  "source": "Community Skills",
  "website": "https://example.org/",
  "email": "author@example.org"
}
```

The file limit is 8192 bytes. `schemaVersion` must be the JSON number `1`. All text
fields are optional in the importer, but catalog packages containing a manifest
must provide title, description, author, version, and source. Website and email remain
optional; omit them when no public author contact is established. The example contacts
above are placeholders, not contacts to copy into a real package. Unknown fields, arrays, null, invalid UTF-8/JSON, empty or
whitespace-only values, and ASCII control characters are rejected. Text is single-line.
Limits are 160 UTF-16 code units for title and source, 1024 for description, 256 for author,
and 64 for version, matching JavaScript string length. Version must be `MAJOR.MINOR.PATCH`,
with no leading zeroes, prerelease suffix, or build suffix. A UTF-8 BOM is accepted.
Write each key once; catalog generation produces plain UTF-8 without a BOM.

`website` is limited to 2048 UTF-16 code units and must be an absolute HTTPS URL with
a hostname, no username/password, whitespace, or backslashes. `email` is limited to
254 code units and must be one plain ASCII address, without a `mailto:` prefix,
parameters, or display name. Its local part is at most 64 characters, with no leading,
trailing, or repeated dots; the domain needs at least two valid DNS labels (1-63
letters/digits/hyphens each, with no leading/trailing hyphen). Absent contacts do not
produce empty About links. These checks validate syntax, not ownership or reachability.

Legacy packages without `skill.json` remain valid. The machine ID and AI routing
description still come from the strict `name`/`description` frontmatter in `SKILL.md`.
The display description can be a shorter explanation for users; it does not replace
the AI routing description. Importing a ZIP does not authorize scene changes.

## Catalog source of truth

Edit `skills/<id>/metadata.json` first. The mapping is:

| Catalog field | Package field |
| --- | --- |
| title | title |
| purpose | description |
| author.name | author |
| version | version |
| Catalog constant: Community Skills | source |
| author.profile, when non-null | website |
| author.email, when present | email |

`source` is a package-declared display label, not cryptographically verified provenance
or a certification by the catalog. Keep detailed provenance and permission evidence in
the external catalog record.

Website and email appear in About only when supplied. Use established public author
contacts; never substitute repository maintenance contacts. The author profile remains
clickable in the external catalog and is also copied into the manifest's website field.
Rights, provenance, verification, dependencies, and usage examples remain outside
the manifest and are not valid fields in `skill.json`.

After reviewing the version and attribution, run:

```sh
python tools/catalog.py sync-manifest <id>
python tools/catalog.py inspect skills/<id>/package
python tools/catalog.py generate
python tools/catalog.py check
python tools/catalog.py build
```

`sync-manifest` writes the display JSON and updates the package fingerprint. It validates
the proposed content first and refuses to change a package whose version is marked
published. Bump the version before changing released manifest bytes. Keep the previous
`publishedVersion` until the new release is verified. Numbered releases remain immutable.
Inspect release history as well: the local pointer is not a substitute for that check.

Ordinary `generate`, `check`, and `build` never silently repair manifest drift. Validation
requires exact correspondence to the catalog mapping, including all five strings.
Catalog-only changes to fields outside that mapping do not change ZIP bytes.
