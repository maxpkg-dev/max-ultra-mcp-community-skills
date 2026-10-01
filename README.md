# Max Ultra MCP Community Skills

Community-created skills for **3DGROUND — Max Ultra MCP**.

Discover workflows for architectural visualization, modeling,
materials, lighting, cameras, and scene preparation.

## Install a skill

1. Click **Download ZIP** beside the skill you want.
2. In Max Ultra MCP, open **Skills → Custom → Import ZIPs**.
3. Select the downloaded ZIP.
4. Start a new conversation in your AI client.

Import each skill separately.

**Download ZIP** downloads the latest confirmed published version of that skill
directly. Its version appears beside the button. New versions awaiting publication
do not replace an existing download; new skills show **Publication pending** until ready.
See [installation and updates](docs/INSTALL.md).

## Skill catalog

<!-- catalog:start -->

| Skill | Author | Category | Purpose | Version | Verification | Download |
| --- | --- | --- | --- | --- | --- | --- |
| [ArchViz Master \(Yuriy Bobak\)](docs/skills/archviz-master-yuriy-bobak.md) | Yuriy Bobak | Architectural visualization | Architectural render critique, composition, mood design, and production planning. | 1.2.1 | discovery-reported | [Download ZIP](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/releases/download/archviz-master-yuriy-bobak-v1.2.1/archviz-master-yuriy-bobak-1.2.1-max-ultra-mcp.zip) (v1.2.1) |

<!-- catalog:end -->

## Add or publish a skill without AI

Follow the [step-by-step manual guide](docs/MANUAL_PUBLISHING.md) to submit through your
browser or prepare, review, upload, and publish a skill as the repository owner.

## Contribute

Community submissions are welcome.
[Submit a skill](https://github.com/maxpkg-dev/max-ultra-mcp-community-skills/issues/new?template=submit-skill.yml)
with a free GitHub account, or contribute a pull request using the
[contribution guide](CONTRIBUTING.md).

Each submission must include its author, purpose, dependencies,
tested software versions, and distribution permission.

Skills are reviewed before publication.
Issue submissions and labels never trigger package publication.

## Verification

Package validation and practical testing are reported separately.
A valid package does not guarantee compatibility with every
3ds Max version, renderer, or plugin.

## Authors and permissions

Each skill retains its author attribution and its own distribution terms.
Inclusion in this catalog does not assign a common license to all skills.

## Maintainers

Each `skills/<id>/metadata.json` is the catalog source for its skill. Package
instructions live in `skills/<id>/package/`; catalog metadata stays outside ZIPs.
README catalog rows and [detail pages](docs/skills) are generated together.

With Python 3.12 or later (package tools use the standard library; tests use pinned PyYAML):

```sh
python -m pip install -r requirements-dev.txt
python tools/catalog.py validate
python tools/catalog.py generate
python -m unittest discover -s tests -v
python tools/catalog.py check
python tools/catalog.py build
```

Builds write individual versioned ZIPs and SHA-256 files into ignored `dist/`.
See [moderation and release activation](docs/MAINTAINERS.md),
[metadata fields](docs/METADATA.md), and [validation boundaries](docs/VALIDATION.md).
No separate website or hosting service is required.
