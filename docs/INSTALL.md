# Install and update

1. Open the skill's catalog detail page and follow **Find this version in Releases**.
2. If no matching release exists, publication is pending. Maintainers can build a local ZIP; no live download is implied by the catalog entry.
3. Download the asset named `<id>-<version>-max-ultra-mcp.zip`. GitHub's automatic Source code archives contain the repository and cannot be imported as a skill.
4. Optionally compare the file's SHA-256 with the adjacent `.sha256` release asset.
5. Open **Skills → Custom → Import ZIPs** in Max Ultra MCP and select the ZIP.
6. Start a new conversation in your AI client (or restart it if discovery has not refreshed).

Import each skill separately. Read attribution, dependencies, permissions, and verification evidence first.

## Updates

Import is not an in-place update. Preserve any local changes first. When the new package has a different machine name, import it, verify its presence, then remove the old entry. For example, `archviz-master-yuriy-bobak` can replace an older `archviz-master` entry this way.

If the same machine name already exists, the current importer rejects a duplicate: export or preserve the old copy, remove its imported entry, then import the new ZIP. Start a new AI chat after replacement so previously loaded instructions are refreshed.

Discovery means that a skill appears in the available list. It does not prove that its advice or live scene operations have been practically tested.
