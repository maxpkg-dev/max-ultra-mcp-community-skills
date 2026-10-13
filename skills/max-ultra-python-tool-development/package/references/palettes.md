# Editable reference palettes

These JSON snapshots preserve the actual bytes of seven `assets/themes` files inspected in Max Ultra MCP at commit `8c364294e1b5f9cb0aed778ba8aaac91f3015070` on 2026-10-13. Source attribution: Lukianenko Vasyl / 3DGROUND. The user explicitly requested their inclusion for reuse in this standalone skill. This records local preparation authority, not a general license to the reference product or authorization to publish. The catalog terms retain that boundary.

| Editable file | Theme | SHA-256 of source bytes |
| --- | --- | --- |
| [graphite.json](themes/graphite.json) | Warm Graphite (recommended default) | `f1f175287d51f549c9cb564aa1032ad606f5dc6bb6c7c0fef4ef62930b305a46` |
| [forest.json](themes/forest.json) | Forest | `1a43f9fe122b09d3f961d073c3baf0c41d9ec38a067a62c96e374c7627b7154f` |
| [plum.json](themes/plum.json) | Muted Plum | `f4ea58617700d5d3337c9b824f59b74a3706d2b1ad3683566b54617e8c124a59` |
| [coffee.json](themes/coffee.json) | Coffee | `eb2e0097b1d86318f4246dac5393054ac660f6bdcea60acab3570521aa455de8` |
| [teal.json](themes/teal.json) | Deep Teal | `d0c31bf5b2336e79be887e1a783b77853780b829c002c6d5ed1c69498c926a0f` |
| [burgundy.json](themes/burgundy.json) | Burgundy | `0a345fbf4f6ee3d2fb2ed6be648d5f33e0c22c60bd6c36b8716e5bf54af6bdee` |
| [max.json](themes/max.json) | 3ds Max (user colors) | `38bb9ad1dbbd40494194f64980c40dd9b6c6c475e3753d05eb9080774c68f124` |

Each file has 83 semantic colors. Keep each palette separately editable. They are under `references/themes` to satisfy the instruction-only skill importer; in a generated tool they belong in `assets/themes`. Editing a generated tool's copy is intentional; these hashes identify this reference snapshot only. `bindings.json` is not needed: it maps legacy literal colors to roles, whereas new code should use roles directly. No runtime reference-repository path is required.

## Role mapping

Preserve the original keys in assets; map conceptual roles in shared code. This table separates actual palette keys from optional aliases for a new tool:

| Concept / recipe alias | Actual palette key |
| --- | --- |
| `window`, `surface`, `field`, `recessed`, `popup` | `window_background`, `button_background`, `field_background`, `recessed_background`, `dropdown_background` |
| `text`, `muted_text`, `selected_text`, `disabled_text` | Same names; text-entry content specifically uses `field_text` |
| `accent`, `border` | Same names |
| `hover`, `selected`, `focus` | `button_hover`, `selection_background`, `focus_border` |
| `disabled_surface`, `disabled_border` | Alias `button_background` for surface; `disabled_border` exists |
| `success`, `warning`, danger status text | `log_success`, `log_warning`, `log_error` |
| Destructive button `danger`, `danger_hover`, `danger_pressed`, `danger_text` | `delete_background`, `delete_hover`, `delete_pressed`, `delete_text`; also `delete_border` |
| `link` | Alias `support_link` consistently, or deliberately add a separate semantic link role to each generated palette |
| `link_hover`, ordinary `pressed` | New-tool aliases may use `accent`, `selection_background`; these exact generic keys are not present in the source |
| `scroll_track`, `scroll_thumb`, `scroll_hover`, `scroll_pressed` | `recessed_background`, `scrollbar_thumb`, `scrollbar_hover`, `text` |
| Tab boundary / pane / selected tab | `active_border`, `tab_pane_background`, `active_tab_background` |
| Checkbox borders | `checkbox_border`, `checkbox_hover_border`; prefer `accent` for a generic checked fill |

Do not use dark danger button background as small error text; use `log_error` for status text. The extra community/donation/journal roles are source data, not a requirement to add those product features.

## Interpreting values

Values are either `#RRGGBB`, `{"mix": [left, right, ratio]}` or `$nativeRole`. Mix each RGB channel as `round(left*(1-ratio)+right*ratio)`. Validate `0 <= ratio <= 1` and bounded recursion. `$nativeRole` uses the current host `colorMan` sample when available, otherwise the file's `colorMan` fallback. Query `colorMan` only on Max's main thread and never change its values. Refresh native samples when selecting the host-color theme.

For the host-color palette, the reference treats a resolved field background as light when its RGB weighted value `0.2126*R + 0.7152*G + 0.0722*B` exceeds 150, then overlays `light_colors`. This is an implementation threshold, not a WCAG contrast calculation. Validate actual readability separately.

New plain-data resolver example, compatible in syntax with Python 3.7:

```python
def resolve_palette(document, native_colors=None):
    import math
    import re
    colors = document["colors"]
    fallbacks = document.get("colorMan", {})
    native_colors = native_colors or {}

    def channels(value):
        return [int(value[i:i + 2], 16) for i in (1, 3, 5)]

    def resolve(value, depth=0):
        if depth > 8:
            raise ValueError("Theme expression is too deep")
        if isinstance(value, str):
            if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
                return value.lower()
            if value.startswith("$"):
                key = value[1:]
                if key not in fallbacks:
                    raise ValueError("Unknown native color " + key)
                return resolve(native_colors.get(key, fallbacks[key]), depth + 1)
        if isinstance(value, dict) and set(value) == {"mix"}:
            parts = value["mix"]
            if isinstance(parts, list) and len(parts) == 3:
                left, right, ratio = parts
                if type(ratio) in (int, float) and math.isfinite(ratio) and 0 <= ratio <= 1:
                    a = channels(resolve(left, depth + 1))
                    b = channels(resolve(right, depth + 1))
                    return "#" + "".join("{:02x}".format(round(x * (1-ratio) + y * ratio))
                                         for x, y in zip(a, b))
        raise ValueError("Invalid theme color expression")

    result = {key: resolve(value) for key, value in colors.items()}
    if fallbacks:
        rgb = channels(result["field_background"])
        if sum(c * w for c, w in zip(rgb, (0.2126, 0.7152, 0.0722))) > 150:
            result.update({key: resolve(value) for key, value in document.get("light_colors", {}).items()})
    return result
```

Before resolving, validate top-level types, a nonempty name, required role coverage, fallback hex values, and that override keys name existing roles. Do not accept arbitrary file paths from the theme picker. The resolver is a pure-data example, not permission to execute imported scripts. Apply the alias mapping after resolution so QSS and HTML consume one concrete palette.
