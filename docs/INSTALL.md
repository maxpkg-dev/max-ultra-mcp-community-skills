# Install and update

1. Click **Download ZIP** in the catalog or on the skill's detail page. The file downloads directly; the version is shown beside the link.
2. Optionally compare the file's SHA-256 with the **SHA-256** link on the detail page.
3. Open **Skills → Custom → Import ZIPs** in Max Ultra MCP and select the ZIP.
4. Start a new conversation in your AI client (or restart it if discovery has not refreshed).

Import each skill separately. Read attribution, dependencies, permissions, and verification evidence first.

The link tracks the latest confirmed published version of that specific skill. A new skill
shows **Publication pending** until its ZIP is available. While an update awaits publication,
the existing version remains downloadable. You do not need GitHub's Source code archives.

## Updates

Updating the catalog's download link does not update copies already installed in your AI client.

Import is not an in-place update. Preserve any local changes first. When the new package has a different machine name, import it, verify its presence, then remove the old entry. For example, `archviz-master-yuriy-bobak` can replace an older `archviz-master` entry this way.

If the same machine name already exists, the current importer rejects a duplicate: export or preserve the old copy, remove its imported entry, then import the new ZIP. Start a new AI chat after replacement so previously loaded instructions are refreshed.

Discovery means that a skill appears in the available list. It does not prove that its advice or live scene operations have been practically tested.
