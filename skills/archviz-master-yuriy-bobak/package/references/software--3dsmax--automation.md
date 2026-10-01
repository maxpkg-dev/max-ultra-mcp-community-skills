# 3ds Max Automation

## MAXScript
MAXScript is 3ds Max's native scripting language and is suitable for scripted utilities, scene operations and tool building.

## Python
Use Python/pymxs for cross-application pipeline tools and access to 3ds Max functionality. Python is especially useful when integrating file systems, databases, data analysis or external pipeline tooling.

## ArchViz automation targets
- scene cleanup and naming;
- missing asset/bitmap audits;
- texture resolution reports;
- batch relinking;
- camera validation;
- material audits;
- instance/reference checks;
- render submission/preflight;
- batch object transforms;
- asset placement;
- export/import helpers;
- render-node preparation.

## Rule
Codex should generate automation only after defining scope, destructive risk, selection behavior, undo strategy and version assumptions.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.

For Max Ultra MCP execution, follow [integration safeguards](max-ultra-integration.md): serialize selected-instance operations through the main-thread queue and prefer verified semantic tools. Python availability does not authorize direct background access to the Max runtime.
