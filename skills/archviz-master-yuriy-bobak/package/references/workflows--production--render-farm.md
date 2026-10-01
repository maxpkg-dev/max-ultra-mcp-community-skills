# Render Farm — Production Workflow

## Corona distinction
Native Corona DR: multiple machines contribute to one image.
Animation sequence: prefer render manager so machines render separate frames.

## Preflight
- matching 3ds Max version;
- matching Corona version;
- matching ForestPack/RailClone/plugin versions;
- licensing available;
- all maps/proxies/assets/fonts;
- consistent paths;
- color management;
- output path;
- frame range;
- render elements;
- procedural/scatter dependencies;
- enough RAM;
- test node.

## Still
Use DR only when one high-resolution image benefits from combined machines and network overhead is acceptable.

## Animation
Split frames across nodes. Render representative frames on multiple machines before full submission. Check identical output.

## Failure diagnosis
Missing assets → path/package issue.
Different appearance → version/color/plugin/system setting mismatch.
Node crash → RAM/plugin/asset/scene-specific test.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Corona Network / Distributed Rendering](software--corona--network-rendering.md)
- [Corona Animation](software--corona--animation.md)
- [Corona + 3ds Max Color Management](software--corona--color-management.md)
- [Scene Optimization — Production Workflow](workflows--production--scene-optimization.md)
