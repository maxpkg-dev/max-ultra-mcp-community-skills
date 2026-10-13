# Adaptable UI implementation recipes

These are new illustrative templates, not a vendored widget library or tested drop-in toolkit. Put implementations in the generated tool's own theme/UI modules, adapt Qt enum spellings through `qt_compat`, and test in the targeted hosts. The package itself stays instruction-only.

## Theme files and resolver

Use the actual [bundled palette files](palettes.md), especially [Warm Graphite](themes/graphite.json), instead of reconstructing colors from screenshots. Copy the selected JSON files to the generated tool's assets/themes folder; preserve their role names and provenance. The design-system role table is an abstraction: map those roles to the original keys as documented in the palette reference.

The palette reference includes a complete plain-data resolver for hex colors, mix expressions, native colorMan fallbacks and light-color overrides. Add schema validation before committing a theme change. Use semantic tokens in canonical QSS; a strict rendering helper for an already resolved color dictionary is:

```python
def render_qss(source, colors):
    import re
    return re.sub(r"@([a-z][a-z0-9_]*)", lambda m: colors[m.group(1)], source)
```

Missing tokens intentionally raise. Use the same roles when constructing HTML CSS, but never run this substitution indiscriminately over prose, source code, URLs, or attributes containing user data. Build trusted style blocks separately and HTML-escape displayed values. Keep an immutable original source so repeated theme changes do not accumulate transformations.

## Applying themes and reflow without recursion

Theme-manager transaction (conceptual protocol; implement registry/persistence/error behavior in the tool):

```text
select_theme(id):
  load and validate candidate from its file
  snapshot current palette and live owned windows; deduplicate descendants
  save focus, selection, scroll anchors, and each window's updatesEnabled state
  suspend painting on owning windows
  try:
    activate candidate; apply canonical QSS to all registered widgets
    ask rich-content adapters to rerender canonical source with candidate CSS
    update custom-painted controls and icon tint caches
  on failure:
    restore previous palette and styles; report error; restore picker
  finally:
    restore previous painting states
    repaint owning windows with QtWidgets.QWidget.update(window)
  after successful application:
    persist theme id; report persistence failure if any
```

Do not indiscriminately call `widget.update()` on all descendants: PySide6 `QListView`/item-view overload resolution can require an index. Repaint their viewport explicitly when necessary, or the owning QWidget as above. Avoid visiting a child Settings dialog twice through both its parent and a window registry.

For responsive rich text, rendering can trigger resize while changing scrollbars and document layout. Preserve canonical source once; schedule reflow after the current render finishes. An owned single-shot zero-delay timer can coalesce requests and be cancelled at disposal:

```text
set_source(html):
  canonical_source = html
  request_render()
request_render():
  if disposed: return
  pending = true
  if not rendering: reflow_timer.start(0)
flush_render():
  if disposed or rendering or not pending: return
  pending = false; rendering = true
  save selection and top visible character anchor
  try:
    metrics = compute font/padding from available viewport
    render ONCE from canonical_source plus current theme CSS
    call base QTextBrowser.setHtml(rendered) once
    restore clamped selection and scroll anchor
  finally:
    rendering = false
    if pending: reflow_timer.start(0)
resizeEvent:
  call base resizeEvent
  if font/padding/layout metrics differ from last render: request_render()
```

Guard both rendering and resize entry points, and compare metrics before rescheduling to avoid endless resize/reflow oscillation. Never use `toHtml()` output as the new canonical source or append metadata again during reflow. External source changes during a render replace the pending canonical source; last request wins. The reference's `_rendering_html` / `_reflow_pending` guard solves this class of duplication; the owned timer here additionally supports explicit cancellation.

## Control styling and native clipping

Use selector scopes to avoid styling unrelated children accidentally. Illustrative shared QSS tokens:

```css
QCheckBox { color:@text; spacing:9px; }
QCheckBox::indicator { width:20px; height:20px; border:1px solid @border;
  border-radius:3px; background:@recessed; }
QCheckBox::indicator:checked { background:@accent; }
QCheckBox::indicator:hover { border-color:@focus; }
QCheckBox::indicator:disabled { background:@disabled_surface; border-color:@disabled_border; }
QCheckBox:disabled { color:@disabled_text; }
QCheckBox:focus { color:@selected_text; }
QGroupBox { border:1px solid @border; border-radius:5px; margin-top:12px; padding:10px; }
QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 4px; }
QComboBox { background:@field; color:@text; border:1px solid @border;
  border-radius:6px; padding:4px 24px 4px 6px; }
QComboBox::drop-down { width:22px; border:none; background:transparent; }
QComboBox::down-arrow { image:none; }
QListView#themePopup { background:@popup; color:@text; border:1px solid @border;
  border-radius:6px; padding:4px; outline:0; }
QListView#themePopup::item { padding:4px 10px; border-radius:4px; }
QListView#themePopup::item:selected, QListView#themePopup::item:hover {
  background:@selected; color:@selected_text; }
```

Add the licensed, tinted Lucide check glyph to checked indicators (and a partial glyph for tri-state); background alone does not communicate checked state. This excerpt does not include every state; complete the state table in [design system](qt-design-system.md), including focus and disabled popup items. Set the list view's object name to match its selector. Paint the chevron explicitly after normal combo painting, using the enabled/disabled text color and a reserved rectangle.

Rounded native-surface helper, callable after resize; `QtCore`, `QtGui` come from the selected binding:

```python
def clip_rounded(widget, radius):
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(widget.rect())
    radius = max(0, min(radius, rect.width() / 2, rect.height() / 2))
    path.addRoundedRect(rect, radius, radius)
    widget.setMask(QtGui.QRegion(path.toFillPolygon().toPolygon()))
```

Applying this to the full text-area owner clips its viewport children too; if clipping the viewport alone, compute its local inner radius and preserve the frame. Recompute masks on geometry changes and inspect at high DPI; a widget mask can affect shadows and hit regions. Use a custom clipped painter when a mask produces unacceptable edges.

For dropdown placement after `super().showPopup()`, obtain `popup = combo.view().window()`. Choose `field_bottom + 4` if the popup fits the active screen's `availableGeometry()`, otherwise `field_top - popup_height - 4`. Clamp both axes; reduce the popup height/use scrolling if neither side fits. Apply the rounded mask to the popup, not just its list view, and keep keyboard focus there. On very small work areas, remaining onscreen takes priority over the gap.

Scrollbar clearing rules to combine with themed rounded tracks/handles:

```css
QScrollBar:vertical { width:13px; background:@scroll_track; border:none;
  border-radius:6px; margin:0; }
QScrollBar:horizontal { height:13px; background:@scroll_track; border:none;
  border-radius:6px; margin:0; }
QScrollBar::handle:vertical { background:@scroll_thumb; min-height:24px;
  border-radius:4px; margin:2px; }
QScrollBar::handle:horizontal { background:@scroll_thumb; min-width:24px;
  border-radius:4px; margin:2px; }
QScrollBar::handle:hover { background:@scroll_hover; }
QScrollBar::handle:pressed { background:@scroll_pressed; }
QScrollBar::add-page, QScrollBar::sub-page { background:none; border:none; }
QScrollBar::add-line, QScrollBar::sub-line { background:none; border:none; width:0; height:0; }
QScrollBar::up-arrow, QScrollBar::down-arrow,
QScrollBar::left-arrow, QScrollBar::right-arrow { image:none; width:0; height:0; }
QWidget#qt_scrollarea_vcontainer, QWidget#qt_scrollarea_hcontainer {
  background:transparent; border:none; }
QAbstractScrollArea::corner { background:transparent; border:none; }
```

These Qt internal object names are observed in the reference, not a guarantee for every host style. Verify the actual background containers on each supported binding.

For user-approved responsive density, generate both axis thicknesses and compatible radii/margins from one density token set. The reference uses 7px tiny, 9px compact, 13px normal, 17px large and 21px extra-large tracks; tiny/compact handles have 1px margins and 2px radii. These are examples, not mandatory thresholds or an accessibility guarantee. Keep a usable thumb hit region and minimum length; after changing dynamic density properties, unpolish/polish the scrollbar and call `updateGeometry()`. Restore the normal token set when resizing back. Without opt-in, use one stable thickness plus ordinary DPI scaling. Explicitly style disabled handles if the tool uses disabled scroll areas.

## Copy and menu interaction

Create one single-shot `QTimer(button)` with interval 2000. Store the original caption, accessible name, and a copied `QIcon`. The clicked slot obtains current text, writes the clipboard, sets `Copied` plus check icon, then calls `timer.start()`; the timeout restores originals. Do not allocate a fresh unowned singleShot closure on every click.

For list context menus, get the target item under the pointer without changing selection. If native right-button handling changes current selection before `contextMenuEvent`, intercept that button in a small view subclass or suppress the selection-to-load handler for that event. Build menu actions against the captured item ID. Trigger loading only from the explicitly selected menu action or normal left-click/keyboard activation. Merely opening, dismissing, or copying from a menu must not enter the document-loading path.

For tables, store a typed sort key in a dedicated role instead of sorting formatted captions. For example, size `900` sorts before `1200`, dates sort by timestamp, and version `(1, 9, 0)` sorts before `(1, 10, 0)`. A `QSortFilterProxyModel.lessThan` or an item comparator can use those keys with a stable ID tie-breaker. Show and preserve the header's sort indicator; test both directions and missing data.

## Progress and veils

Paint a progress track using a rounded `QPainterPath`; clip the fill to that path. Compute known progress as clamped `(value-minimum)/(maximum-minimum)` only when the range is nonzero. Use a separate animation phase for indeterminate mode, and a widget-owned timer active only while visible and busy. Measure elapsed time from the operation start with `time.monotonic()`, not timer tick counts.

A content overlay resizes beneath the title bar, intercepts content clicks while busy, and paints translucent surface + centered spinner in `paintEvent`. Stop its timer on hide/disposal and clear state in operation completion/error/cancel handlers. Settings uses a separate registry of full-window veils; exclude the modal owner and its child dialogs. Store the base opacity independently, hide only the preview target's veil during slider dragging, and restore it on all drag-exit paths. Do not call `setWindowOpacity` merely to dim windows for modality.

### Concrete SettingsVeil recipe

This newly written version follows the inspected `SettingsVeil` resize-filter and paint approach. Imports come from `qt_compat`; `Qt` is its normalized enum facade. `color()` returns the active resolved color. The controller owns the veil manager and windows; this example omits optional nested Settings instances (allow only one).

```python
class SettingsVeil(QtWidgets.QWidget):
    def __init__(self, target, color):
        super().__init__(target)
        self.target = target
        self.color = color
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setCursor(Qt.ArrowCursor)
        self.setFocusPolicy(Qt.NoFocus)
        target.installEventFilter(self)
        self.setGeometry(target.rect())

    def eventFilter(self, watched, event):
        if watched is self.target and event.type() == QtCore.QEvent.Resize:
            self.setGeometry(watched.rect())
        return False

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        shade = QtGui.QColor(self.color())
        shade.setAlpha(150)
        painter.fillRect(self.rect(), shade)

    def dispose(self):
        self.target.removeEventFilter(self)
        self.hide()
        self.deleteLater()


class SettingsVeils:
    def __init__(self, color):
        self.color = color
        self.windows = set()
        self.veils = {}
        self.settings = None
        self.preview_target = None

    def register(self, window):
        self.windows.add(window)
        # Call again from window.showEvent so newly visible windows are covered.
        self.sync(window)

    def unregister(self, window):
        # Call before deleting the C++ window, while its wrapper is valid.
        if window is self.settings:
            self.end()
        veil = self.veils.pop(window, None)
        if veil is not None:
            veil.dispose()
        self.windows.discard(window)
        if self.preview_target is window:
            self.preview_target = None

    def sync(self, window):
        owner = self.settings
        excluded = owner is None or window is owner or owner.isAncestorOf(window)
        veil = self.veils.get(window)
        if excluded or not window.isVisible():
            if veil is not None:
                veil.hide()
            return
        if veil is None:
            veil = SettingsVeil(window, self.color)
            self.veils[window] = veil
        veil.setGeometry(window.rect())
        veil.setVisible(window is not self.preview_target)
        if veil.isVisible():
            veil.raise_()

    def begin(self, settings):
        self.settings = settings
        for window in list(self.windows):
            self.sync(window)

    def preview(self, target, active):
        self.preview_target = target if active else None
        for window in list(self.windows):
            self.sync(window)

    def end(self):
        self.settings = None
        self.preview_target = None
        for veil in self.veils.values():
            veil.hide()

    def dispose(self):
        self.end()
        for veil in self.veils.values():
            veil.dispose()
        self.veils.clear()
        self.windows.clear()
```

Integration obligations:

1. Parent Settings to the tool window, set window modality, and use `show()` in the host event loop. Its `showEvent` calls `begin(self)` after normal setup; `hideEvent`/close calls `end()`. Every other owned window calls `register`/`sync` on show and unregisters **before** deletion. Register modal child dialogs with their proper Settings parent so they are excluded.
2. The veil only supplies visual/pointer dimming; use proper Qt modality for keyboard blocking. Do not veil Settings itself or use a global topmost flag. If Settings launches another action/dialog, preserve the parent chain and stacking.
3. Connect slider press to `preview(main_window, True)`. Changes adjust only the main window's base opacity. Mouse release calls `preview(main_window, False)` and saves the value. Track press/release with an event filter if groove clicks are not covered by the slider signals. Hide/close, lost drag and exception paths restore the veil in `finally`.
4. Theme repaint reads current `color()` so veils update with all windows. Cleanup calls `dispose()` before destroying windows; disconnect slider slots and remove its filter. Do not let a registry retain dead C++ wrappers. Strong references here are safe only with this explicit controller ownership contract.

Unlike dimming through `setWindowOpacity`, this never alters the other windows' base opacity. The target's opacity changes only in the slider handler; removal of a veil requires no opacity restoration.

## Joined tabs

The inspected `JoinedTabBar` uses `setDrawBase(False)` to remove the native second frame. After Qt paints tabs, draw an active-border baseline at `height - 1` from the left edge to the selected tab's visible left edge and from its visible right edge to the bar's right edge. With no valid selection, draw the complete line. Account for styled trailing margin: the reference tab has a 4px trailing margin and resumes the line inside that margin, not under the selected tab's face.

When controls share a heading row, a companion heading widget continues that same line from the tab bar's mapped right edge across remaining row width at the same mapped Y coordinate. Use `mapTo` instead of guessing coordinates. Selected tab background meets the content pane without a bottom border; inactive tabs retain rounded upper corners and clear hover/focus states. Give all pages the same intentional content margins/padding, including scrolling pages. Remove native tab-bar base and square pane/viewport backing, and clip where necessary. Disabled tabs retain disabled text and arrow cursor. Preserve keyboard tab selection.

Recipe sketch for the baseline (call after normal tab painting, using the palette's `active_border`):

```python
def paint_tab_baseline(bar, selected_face, color):
    painter = QtGui.QPainter(bar)
    painter.setPen(QtGui.QColor(color))
    y = bar.height() - 1
    if selected_face.isValid():
        if selected_face.left() > 0:
            painter.drawLine(0, y, selected_face.left() - 1, y)
        if selected_face.right() < bar.width() - 1:
            painter.drawLine(selected_face.right() + 1, y, bar.width() - 1, y)
    else:
        painter.drawLine(0, y, bar.width() - 1, y)
```

Pass the actual selected painted face rectangle excluding its QSS margins. For scrolling/RTL tabs, obtain current style geometry and avoid painting over scroll buttons. Check the baseline with first/middle/last selection, narrow width, high DPI, and theme changes; a screenshot must show no double line or gap beneath adjacent heading controls.

## Spin boxes and other composite controls

This is a **new recommended pattern**, not a control implementation found in the inspected Max Ultra MCP UI. Implement and validate it before claiming support. Use a shared subclass/style for `QSpinBox` and `QDoubleSpinBox`; do not leave their native up/down square buttons inside an otherwise rounded design.

- Keep the outer field rounded, with reserved trailing space for two hit targets. Make `::up-button` / `::down-button` transparent and borderless; remove native `::up-arrow` / `::down-arrow` images. Theme hover/pressed states without reintroducing a square backing outside the rounded clip.
- Draw original Lucide `chevron-up` and `chevron-down` into those subcontrol rectangles, colored by effective step-enabled/disabled state. Obtain geometry from `QStyleOptionSpinBox` and `subControlRect`, not arbitrary pixel fractions. Draw after the native control's field/text paint so editable text, focus and caret remain intact. Clip arrow-area backgrounds to the outer rounded path.
- Prefer retaining native spin subcontrols for hit testing/repeat behavior while replacing their visual treatment. If using child tool buttons instead, disable native symbols, reserve margins, wire to `stepUp()`/`stepDown()`, and implement repeat, enablement and accessibility explicitly; this is more work and needs extra tests.
- Respect minimum/maximum, step size, wrapping, decimals, locale, prefix/suffix, read-only state and validation. Use `stepEnabled()` flags for each arrow so one can be disabled independently. Do not call `setValue(value+1)` for every numeric type.
- Preserve keyboard arrows, text editing, Enter/Tab and a documented wheel policy. Prefer changing on wheel only while focused to prevent accidental values during parent scrolling; route unfocused wheel events appropriately. Do not steal focus on repaint/theme change. Provide usable physical hit targets at 200%+ DPI; do not double-scale Qt logical geometry.
- Apply the same approach to date/time editors, editable combos, search clear buttons and other composites when used: one shared outer surface, compatible subcontrol states, original Lucide affordances and correct native interaction. These extensions also require their own tests.

Validate integer and floating controls at bounds, repeated press, disabled/read-only, negative and fractional values, locale input, keyboard/wheel, 200%+ DPI, theme switching and screenshot clipping. Compare real values and signal counts, not just QSS text. Unavailable host/binding validation remains explicitly untested.

## About dialog and shared insets

The follow-up reference inspection found `dialogs.py:AboutWindow` in an evolving working tree. It separates a full-width themed hero, accent separator and body; this recipe reuses the composition without the product's branding.

```text
About window (Max-owned; shared window chrome)
  header                    inner left/right inset = content inset
  hero surface              full bleed; inner padding uses shared tokens
    large product icon      original authorized brand asset; DPI-aware
    title / subtitle        larger title, muted supporting text, wraps if needed
  accent divider            full available width, deliberate no side inset
  body                      content inset matches header and hero text grid
    version / author / license or build metadata
    themed website / documentation links
    Donate / Close          shared action controls and matching heights
```

Create separate hero/body containers rather than removing margins from each child ad hoc. Set the outer composition spacing to zero only for the full-bleed sections, then apply the shared scale inside containers. Keep metadata compact, legible and selectable where useful; omit unknown author/license claims. Link styles use the theme's shared link role. Make `Close` use the normal dialog-close path; a Donate action uses the known project destination and original Lucide heart button icon (omit it if no destination was supplied). A product logo is a brand asset, not an exception permitting mixed button icon styles.

Use size hints and work-area bounds, with scrolling for small displays, rather than fixing a height that truncates body content at 200%+. Theme changes update hero, divider, links, icons and buttons while the dialog remains open. Test long product names, absent metadata, narrow width, keyboard close and Settings stacking; verify header/body left edges align while the intentional divider remains full width.
