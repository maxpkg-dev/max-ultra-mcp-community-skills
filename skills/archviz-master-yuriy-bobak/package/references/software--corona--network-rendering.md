# Corona Network / Distributed Rendering

## Native DR
Corona Distributed Rendering combines multiple machines on one image and can scale close to linearly in suitable scenes, with transfer/coordination overhead.

## Requirements
Master and nodes should use matching Corona and 3ds Max versions. DR Server runs on nodes; machines must communicate on the required LAN/firewall ports and have Corona licensing available.

## Animation
For frame sequences, use Backburner or a third-party render manager so machines render separate frames rather than using native DR for every frame.

## Studio implication
For a multi-node ArchViz farm, keep software/plugin versions, assets, fonts, maps, proxies, ForestPack/RailClone dependencies and paths synchronized. Run a preflight before submitting.

## Version scope
Inherited software notes; only the selected claims in [compatibility and validation](compatibility-and-validation.md) were rechecked during v1.2 adaptation. Confirm version-specific features, compatibility, UI paths and numeric settings against official documentation matching the installed version before use.
