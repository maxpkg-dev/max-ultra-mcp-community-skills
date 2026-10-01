# Illustrated Book Case Studies

Read the [evidence register](book-evidence-register.md) for source keys and coverage. The supplied package reports that these nine comparisons were checked against page images during earlier development; this adaptation did not reproduce that source inspection. Proposed ArchViz tests have not been run in a 3D scene.

### A. The same key light can produce different shadow colors

**Evidence:** L PDF 111-112, printed 112-113, figures 83-85. Charlie Pickard's sphere comparisons, a white ball on grass, and Joaquin Sorolla's fountain painting.

**Visible evidence:** the spheres retain a warm illuminated side while shadow colors change with the surrounding field. On the ball, the upper shadowed area is cooler and the lower area greener. The fountain example relates upper-facing and lower-facing surfaces to sky and ground illumination.

**Principle:** a shadow is a region missing a particular direct contribution, not a surface with a universal shadow pigment. The ball is especially useful because different orientations on one object receive different environmental contributions.

**ArchViz test:** if the underside of a canopy is unexpectedly green, first inspect the grass or planting it faces. Compare a diagnostic render with that suspected contributor temporarily made neutral, keeping camera, exposure and key light fixed. A reduction in the tint supports that explanation; unchanged tint means another cause must be investigated. Restore the intended materials afterward.

**Boundary:** the book's ambient-color shorthand is not a complete rendering equation. Multiple lights, material color, visibility and reflections still matter. Do not neutralize a physically motivated tint merely because it is green.

### B. A reflective material describes its surroundings

**Evidence:** L PDF 149-150, printed 150-151, figures 38-41.

**Visible evidence:** a cube is shown inside a simple environment containing a light panel; reflective garden spheres carry recognizable sky and ground regions; cubes inserted into a beach scene adopt different reflected fields on different faces.

**Principle:** reflection patterns need coherent surroundings. A material sample cannot be judged independently of what it reflects. Orientation changes appearance even when material identity remains the same.

**ArchViz test:** before replacing an apparently dull metal, temporarily place a broad bright/dark diagnostic card where the surface can reflect it. Keep material and exposure fixed. If the expected structured reflection appears, the original environment may lack readable variation. This test identifies a contributor; it does not establish that every material parameter is correct.

**Boundary:** the book's idealized statements about shadows on specular objects must not become blanket instructions for mixed, rough or coated materials. Nor should all reflection values be darkened by a fixed painting ratio. Reflection cards are a diagnostic suggestion here, not a required change to the final scene.

### C. Texture visibility changes without changing texture geometry

**Evidence:** L PDF 193 and 196, printed 194 and 197, figures 16 and 20-23.

**Visible evidence:** a repeated ridged surface moves through different lighting orientations; the grooves become more or less conspicuous. Separate spheres show horizontal and vertical scratches with different highlight spreading, while increasingly irregular red spheres change both highlight clarity and surface appearance.

**Principle:** visible texture combines geometry and lighting response. Direction matters: surface structure is not always well represented by undirected noise. The ridged study also prevents a common misreading: greater darkness does not monotonically reveal more relief.

**ArchViz test:** examine plaster or stone with a broad frontal source and then a grazing source, without changing relief strength. Check both a close crop and the delivery resolution. If the relief appears only under grazing light, it may be present but weakly revealed in the intended shot. Decide whether that shot actually needs stronger visibility before exaggerating the surface.

**Boundary:** roughness, geometric relief and direction-dependent reflection are separate controls. A brushed metal's directional appearance is not solved by increasing generic bump alone. Product identity may require subtle, nearly invisible texture.

### D. Attention has several independent causes

**Evidence:** C PDF 293 and 296, printed 110-111, diagrams A-I in Devin Elle Kurtz's Sea Serpent tutorial.

**Visible evidence:** one diagram isolates a shape difference among circles; another isolates size; others isolate color, sharpness, detail or texture. The final comparison combines differences so one colored area has more prominence than another.

**Principle:** grayscale reveals value hierarchy but cannot diagnose every source of attention. A small unusually sharp, colorful or patterned object can remain distracting even when its value matches its surroundings.

**ArchViz test:** for a distracting foreground chair, list the possible differences: light/dark separation, hue, saturation, silhouette, size, sharpness and texture density. Test one contributor at a time. A material adjustment may suffice; removing the chair is not the only option.

**Boundary:** the diagrams are teaching examples, not measurements predicting every viewer's gaze. Recognition, meaning and the brief also affect attention. A required brand accent may intentionally dominate.

### E. Correcting hierarchy and correcting depth are separate steps

**Evidence:** C PDF 332 and 335, printed 123-124, Sea Serpent figures 33-35.

**Visible evidence:** the foreground dragon initially competes with the photographer. The next treatment reduces conspicuous highlights and surrounding contrast. A further comparison changes the sky and middle-distance value range to improve spatial separation.

**Principle:** the tutorial solves two linked but distinct problems: who should attract attention, and which planes should recede. Treating both as a request for more global contrast would lose that distinction.

**ArchViz test:** when a sunlit shrub competes with an entrance, first test a restrained local reduction in its prominence. Then independently check whether background masses still sit behind the building. Compare full-frame views, not only the corrected crop. Keep temporary paintovers separate from the eventual scene solution.

**Boundary:** in this painting the photographer is the intended focal point, not necessarily the largest creature. In an architectural brief, the intended first read must likewise be established rather than assumed. Brighter backgrounds or stronger foreground contrast are not universal depth requirements.

### F. A local shape can create a false structural reading

**Evidence:** C PDF 535-538, printed 192-193, Joshua Clare's Lone Rider, figures 31a-31c and 33a-33b.

**Visible evidence:** the cloud edge meets a turn in the hill contour awkwardly; extending the cloud resolves the coincidence. A dark patch beside a horse's leg makes the leg appear longer; a small digital paintover tests the correction.

**Principle:** perceived form depends on adjacent shapes. A local rendering problem can look like a modeling problem. The author tests a minimal intervention before committing to the painting.

**ArchViz test:** if a column seems too wide, first inspect nearby shadows and overlapping tree trunks. If the outline is ambiguous, test a small crop, viewpoint adjustment or temporary paintover to isolate the cause before altering dimensions.

**Boundary:** do not change approved architecture to repair an accidental view. A paintover demonstrates a visual hypothesis; it does not verify that the proposed lighting or geometry is physically achievable. Final completion still requires the brief's technical deliverables, beyond the painting's expressive stopping criterion.

### G. Overlap can establish depth without a strong value gradient

**Evidence:** P PDF 159 and 163, printed 154 and 158, Nathan Fowkes's overlap diagrams and pavilion detail, figure 30.

**Visible evidence:** a sequence of similarly sized gray squares suggests ordering through occlusion. Marked vegetation and architectural boundaries form a chain of overlaps. The pavilion crop distinguishes front, side and underside surfaces despite loose brushwork.

**Principle:** several depth cues can cooperate without all being maximized. Overlap establishes front/back order; plane-specific illumination establishes volume. The simple squares alone establish ordering more clearly than metric distance.

**ArchViz test:** trace a route from foreground planting through steps, facade and roof. At each transition, identify the visible boundary that establishes which surface is in front. Resolve ambiguous touches or merged silhouettes before adding fog. Separately check that returns and soffits have enough evidence to read as distinct planes.

**Boundary:** adding more overlapping plants can hide the design. The painting's count of overlaps is an observation about that picture, not a target number. ForestPack density should serve readability and the actual planting plan.

### H. Repetition is a scale system, not just ornament

**Evidence:** P PDF 240 and 245, printed 235 and 240, GUWEIZ's Night Warrior, figures 27 and 30.

**Visible evidence:** windows, balconies and dormers make a large building interpretable. Long repeated structural lines support perspective, while more intricate motifs remain grouped within the architectural form.

**Principle:** familiar dimensions provide anchors for unfamiliar large forms. Repetition can describe surface direction and distance simultaneously; simple and complex patterns can operate at different viewing scales.

**ArchViz test:** judge a facade first with only the main masses and a few correctly sized openings, then add repeated detail. If the building seems miniature or enormous, check opening sizes, floor heights and camera relationships before adding ornaments. For RailClone elements, verify the intended real dimensions and continuity at corners.

**Boundary:** irregularity is useful only when it belongs to the design. Do not distort modular construction or randomize window spacing to imitate a painterly city. Repetition is not inherently a defect.

### I. Material detail can explain form, while distant detail can be omitted

**Evidence:** P PDF 253-254, printed 248-249, Night Warrior texture and material panels A-C.

**Visible evidence:** wet highlights and water paths follow the character's surfaces; paired light/dark marks describe scratches. The architecture crop explicitly distinguishes a detailed nearby area from farther surfaces where individual tiling is omitted and a few highlights remain.

**Principle:** useful detail communicates shape, orientation, material or distance. Equivalent effort everywhere can weaken spatial hierarchy. The far building remains legible through carefully placed cues rather than a complete inventory of small features.

**ArchViz test:** inspect the final-resolution image and name what each prominent texture contributes. Reduce unnecessary contrast in distant joints or tiles while retaining scale-defining openings. Place streaking and wear according to construction and exposure rather than covering every surface with the same procedural noise.

**Boundary:** this is not permission to remove required architectural information or create physically inconsistent wear. Close-up deliverables and different cameras may need the details that a wide shot does not resolve. Review every required view.
