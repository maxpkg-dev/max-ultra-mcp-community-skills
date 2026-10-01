# Compatibility and Validation Scope

## Package and software scope

ArchViz Master (Yuriy Bobak) v1.2.1 is an instruction-only custom skill for 3DGROUND - Max Ultra MCP. The import package contains root SKILL.md plus supporting text in references. Its internal manifest is informational, not an executable installer or an importer schema extension. No scripts, client adapters, plugins, scenes, source books or downloaded assets are bundled.

Max Ultra MCP targets 3ds Max 2022-2027. Artistic diagnosis is not tied to a Max version. This package preserves a 2027-family software knowledge baseline; it has not been executed across that range, nor does it prove Corona, ForestPack or RailClone compatibility on any installed machine. Runtime capability checks and installed-version vendor documentation remain necessary.

## Sampled official checks on 2026-10-01

These are documentation checks, not scene tests or an exhaustive audit of the software library.

- Autodesk's [3ds Max 2027.2 overview](https://help.autodesk.com/cloudhelp/2027/ENU/3dsMax-WhatsNew/files/GUID-D11D1F34-C9FF-4981-AAE3-5A969986FCF4.html) lists Gaussian Splat support, the Point object and Point Instance render-time instancing. This does not establish Corona support for those features.
- ITOOSOFT's [ForestPack 9.4.1 changelog](https://docs.itoosoft.com/changelog/2026/06/17/forestpack-9_4_1) records RailClone segment distribution and the RailClone 7.3.2-or-later requirement, including the Export to Forest and Reference distribution route. Other detailed integration behavior still needs the relevant installed-version reference.
- Chaos's [Corona Material Library for 3ds Max](https://support.chaos.com/hc/en-us/articles/4528593932945-How-to-use-the-Corona-Material-Library-in-3ds-Max) states that the legacy toolbar library was removed starting with Corona 15 and materials are accessed through Cosmos. The [offline-library article](https://support.chaos.com/hc/en-us/articles/4528215807761-How-to-install-the-material-library-in-offline-mode) separately identifies the same 3ds Max change. Do not apply old offline-library instructions to that version.

All other feature, numeric, performance, UI and version assertions are inherited notes pending task-specific verification. Documentation can change; use the installed build as the applicability boundary, not the word 'current' in a historical reference title.

## Verification boundaries

Importer validation establishes file layout, metadata, text encoding, bounded size and internal references. ZIP verification establishes archive safety, checksums and equality with the folder. Neither proves client activation, artistic quality, renderer compatibility or correct scene execution. A written scenario review is not a real-Max test. No user scene should be opened or modified just to validate this package.

The source books and historical OCR artifacts were unavailable during this adaptation. Their reported coverage and page-specific claims remain attributed to the supplied package, as explained in [provenance](provenance-and-distribution.md).
