# UI Style Guide (Draft)

## Principles
- Consistency: unified colors, spacing, card and toolbar patterns.
- Clarity: clear task flow and visible primary actions.
- Responsiveness: adapt columns and layout to window width.
- Feedback: progress, cancellable actions, readable errors.

## Colors
- Background: `#F7F8FA`
- Card: `#FFFFFF`
- Text: `#1F2937`
- Muted: `#6B7280`
- Border: `#E5E7EB`
- Accent: `#2563EB` (buttons/primary)

## Typography
- Base font: Arial 10–12
- Titles: Arial Bold 12–14
- Spacing: 8px unit; button padding (10, 6)

## Components
- Toolbar: left title, right action buttons (primary on the rightmost).
- Card: subtle border, padding 10–16, stacked content.
- Buttons: primary uses Accent; hover darkens.
- Toast: bottom-right, auto-dismiss in 2–3s.

## Patterns
- Results Grid: dynamic columns (min card width 260px, max 6 columns).
- Scroll: vertical default; horizontal appears only when content overflows.
- Batch actions: download/copy/open grouped at the top-right of results.

## Accessibility
- Contrast: ensure text/background ratio > 4.5.
- Keyboard: tab order logical; visible focus.
- Language: Traditional Chinese first, English secondary.

This draft is applied via `ui_components.UITheme`, `Toolbar`, and `Card`. Further refinements welcome.
