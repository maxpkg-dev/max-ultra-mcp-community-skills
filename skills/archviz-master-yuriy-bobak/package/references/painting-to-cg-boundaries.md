# Painting-to-CG Interpretation Boundaries


1. **Fresnel is not synonymous with total internal reflection.** L 185-186 offers useful observations about grazing reflections, but its causal explanation should not be copied as a general technical rule. Fresnel reflectance concerns angle and optical properties at an interface; total internal reflection is a specific condition for transmission toward a lower-index medium above a critical angle. Technical cross-check: [PBRT, Specular Reflection and Transmission](https://www.pbr-book.org/4ed/Reflection_Models/Specular_Reflection_and_Transmission).
2. **Depth of field, tilt/shift and atmosphere are different controls.** P 43-51 uses loose or simplified terminology in places. Focus blur is associated with camera/lens geometry; fog alters light through participating media. Diagnose these separately. Technical cross-checks: [PBRT, Projective Camera Models](https://www.pbr-book.org/4ed/Cameras_and_Film/Projective_Camera_Models) and [PBRT, Volume Scattering](https://www.pbr-book.org/4ed/Volume_Scattering).
3. **Painting ratios are not renderer settings.** Rules about halving values, limiting bounce intensity or choosing a fixed number of tones are contextual teaching devices. Do not convert them into universal albedo, light-intensity or tone-mapping values.
4. **A visual simplification is not necessarily a scene edit.** Grayscale, posterization, paintovers and softened boundaries can be temporary diagnostics. Distinguish the diagnostic from the final physical or compositional correction.
5. **Quiet images remain valid.** High contrast, strong foregrounds, dramatic atmosphere and orange-blue palettes are options. Judge them against the intended architectural message.



Source keys: [evidence register](book-evidence-register.md). The linked PBRT sections are narrow optics cross-checks, not verification of Corona or 3ds Max version-specific behavior.
