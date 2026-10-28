# Interface size on 2K / 4K screens

Implementation: [ui-scale template](templates/ui-scale.md) and `measure_scale`, `scale_font`, `inherit_fonts` in
[qt-compat](templates/qt-compat.md).

## Why tools look tiny in 3ds Max on large screens

3ds Max starts Qt with `QT_ENABLE_HIGHDPI_SCALING=0` and `QT_SCALE_FACTOR=1`: the device pixel ratio is 1 on every
screen. Every size written in pixels (style sheet, `setFixedSize`, margins, icon sizes, the window size) stays
physical, so a tool designed on Full HD is small on a 2K screen and tiny on 4K. Only point-size fonts follow Windows
scaling (logical DPI). Qt will not fix this; the tool must.

## The rule

One target scale, measured once at start-up before any window exists:

- **Screen step** from the screen under Max's main window (found by position, never `widget.screen()`): the smaller of
  width / 1920 and height / 1080 against steps: below 1.15 -> 100 % (Full HD), below 1.6 -> 125 % (2K, 2560 x 1440),
  below 2.4 -> 150 % (4K, 3840 x 2160), above -> 200 % (5K and more).
- **Windows / Max scaling**: logical DPI / 96 times Qt's own ratio, and 3ds Max's UI scale (`rt.GetUIScaleFactor()`).
- **Target** = the largest of these ("Auto"). Settings > Appearance > Interface size overrides it with 100 / 125 / 150 /
  175 / 200 %; stored as text ("1.25"), like the default "auto" (a stored value of another type is ignored).
- Factors: pixels x `target / qt_ratio` (`px()`), points x `target / windows_scale` (`pt()`), so nothing is scaled twice.

The interface size applies while windows are built. A changed choice shows "Applies when Name opens again." and a
"Reopen Now" button (inside Max: run the launcher again after the click returns; it restarts the session).

## How to write sizes

- Every pixel number in UI code goes through `px()`: margins, spacings, fixed sizes, icon sizes, minimum sizes, offsets
  of popups. Class constants stay logical (`EDGE = 4`) because they are evaluated at import, before the scale is
  known; multiply them where they are used (`px(self.EDGE)`).
- Every explicit font size goes through `pt()` (`font.setPointSizeF(pt(20))`).
- The style sheet is written at 100 %; the theme manager multiplies every `Npx` (1 px borders stay at least 1 px) and
  every `Npt` when it builds the sheet. Ratios that must hold (a scroll thumb radius = half its width) must still hold
  after each number is rounded on its own: pick numbers that scale cleanly or check 125 % and 150 %.
- Painted controls (pills, progress, balloons) use `px()` for padding and radii and the widget's font metrics for text.
- Icons are rendered at `px(size)` times the device pixel ratio so they stay sharp.

## Fonts reach every widget

- `scale_font(window)` once at the very start of each top-level window's constructor (top-level windows do not inherit
  fonts from a parent window). Popups (balloons, completer lists) take the font of the window that opens them.
- A widget matched by a style sheet rule (lists, tables, some item views) gets the application's font back when it is
  polished, and item views have their own class default font in Qt 5 (9 pt beside the application's 8.25 pt). Run
  `inherit_fonts(root)` after polish: in the main window's `showEvent`, in each dialog's `showEvent`, and after building
  rows later (lists refilled, groups rebuilt). It compares every widget with its class default and gives it its
  parent's size when it was not set on purpose.
- Every re-polish does the same: a field whose property changes (a search field that squares its corners while its
  suggestions are open) or a button whose variant changes (primary to danger while a job runs) falls back to 8.25 / 9
  pt. `repolish(widget)` gives the widget its parent's size again right after polishing it; never re-polish by hand.
- A dropdown's list is polished when it first opens, after the window's `showEvent`: `ComboBox.showPopup` polishes its
  view and runs `inherit_fonts` on the popup before Qt measures the rows.
- Check: open the window at 125 % or 150 % and compare the point size of a label, a checkbox, a field and a list; they
  must be equal unless one was set on purpose. Then open a dropdown and switch a button's variant twice, and check
  again: no visible widget may be left at a default size.

## Responsive breakpoints are a different thing

The interface size is the same for the whole session and follows the screen; it is part of DPI correctness and is on by
default. Breakpoint adaptation (smaller text and icon-only buttons in narrow windows, larger in wide ones) remains an
opt-in the user must choose, as SKILL.md says.
