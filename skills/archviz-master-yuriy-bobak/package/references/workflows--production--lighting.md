# Lighting — Production Workflow

## Load
light, color-value, depth, materials-reflections, visual-hierarchy; Corona lighting/environment, LightMix, VFB.

## Decision tree
Exterior controlled daylight → Corona Sun/Sky candidate.
Complex photographic environment/reflections → HDRI candidate.
Interior/custom fixtures → Corona Lights / Light Material as appropriate.

## Process
1. Establish mood/time.
2. Choose key direction.
3. Read major form/cast shadows.
4. Check facade/interior plane separation.
5. Check focal illumination.
6. Check environment/bounce.
7. Check material response.
8. Add secondary practical lights only with purpose.
9. Use LightMix for balancing and variants, not to hide broken source setup.
10. Tone-map after the lighting structure works.

## Failure modes
Flat = often direction/hierarchy problem, not contrast-slider problem.
Too dramatic = verify whether shadow/value pattern still serves architecture.

## Linked dependencies
Read the references needed for the selected branch; procedural modules apply only when those systems are used in the scene.

- [Light](knowledge--light.md)
- [Color & Value](knowledge--color-value.md)
- [Depth](knowledge--depth.md)
- [Materials & Reflections](knowledge--materials-reflections.md)
- [Visual Hierarchy](knowledge--visual-hierarchy.md)
- [Corona Lighting & Environment](software--corona--lighting-environment.md)
- [Corona LightMix](software--corona--lightmix.md)
- [VFB / Tone Mapping / Post](software--corona--tone-mapping-vfb.md)


## Artistic diagnosis and mood
For mood alternatives use [Mood Design](mood-design.md). For uncertain visual causes use the [Artistic Diagnostic Workflow](artistic-diagnostic-workflow.md), then the [Artistic Review Checklist](artistic-review-checklist.md). These extend the artistic layer without establishing new version-specific software settings.
