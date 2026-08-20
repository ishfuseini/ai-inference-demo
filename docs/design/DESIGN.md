# Demo Application Design System

This document defines the shared visual language for demo applications. The goal is to create interfaces that feel polished and intentional while remaining focused on demonstrating the underlying product, API, workflow, or technical concept.

The design should feel **clean, technical, approachable, and lightweight** rather than like a heavily branded production SaaS application.

---

## 1. Design Principles

### Demo First

The interface exists to make the demonstrated concept easy to understand.

Prefer:

- Clear information hierarchy
- Obvious actions
- Visible system state
- Simple navigation
- Enough whitespace to understand the workflow

Avoid:

- Decorative UI that competes with the demo
- Excessive dashboard widgets
- Unnecessary navigation
- Marketing-style layouts inside functional demos
- Visual complexity added only to make the application look "finished"

### Intentional, Not Generic

Demo applications should look designed rather than like framework defaults.

Use the shared color, typography, spacing, and component conventions in this document instead of introducing arbitrary values.

### Technical Information Should Be Visible

When useful to the demo, expose technical information such as:

- Model names
- API providers
- Request state
- Latency
- Token usage
- IDs
- Parameters
- Structured responses
- Logs
- Errors

Use monospace typography to visually distinguish this information from normal application content.

---

# 2. Color System

## Core Tokens

```css
:root {
  /* Brand */
  --color-primary: #7B23D4;

  /* Text & Neutrals */
  --color-text-main: #261F2E;
  --color-surface: #F0EEF1;
  --color-background: #EEECFA;

  /* Contrast */
  --color-text-on-primary: #FFFFFF;
}
```

## Primary

`#7B23D4`

Use the primary purple for:

- Primary buttons
- Selected states
- Active navigation
- Links where appropriate
- Focus indicators
- Important interactive accents
- Small visual highlights

The primary color should communicate **interaction and emphasis**.

Do not use it indiscriminately as decoration.

## Background

`#EEECFA`

The application background should use the subtle lavender background rather than pure white.

This provides visual identity while keeping the interface light.

## Surface

`#F0EEF1`

Use surface colors for:

- Cards
- Panels
- Input areas
- Secondary containers
- Grouped information

Surfaces should create hierarchy without requiring heavy shadows.

## Primary Text

`#261F2E`

Use for:

- Body text
- Headings
- Labels
- Navigation
- Important metadata

Avoid pure black when this token provides sufficient contrast.

## Text on Primary

`#FFFFFF`

Use when text appears over the primary purple, particularly for primary buttons and selected controls.

---

# 3. Color Usage

Color should communicate hierarchy rather than decorate every component.

A typical screen should be dominated by:

1. Background
2. Neutral surfaces
3. Dark text
4. Small amounts of primary purple

Avoid large areas of saturated purple unless they serve a clear structural purpose.

Do not introduce arbitrary brand colors into individual demo applications.

Semantic colors for success, warning, error, and informational states may be introduced when required, but they should remain visually secondary to the primary palette.

---

# 4. Typography

## Interface Font

**Inter**

Use Inter as the default application typeface.

Use for:

- Headings
- Body text
- Navigation
- Buttons
- Forms
- Labels
- Help text
- Tables
- UI controls

Recommended weights:

- `400` — body text
- `500` — controls and labels
- `600` — headings and emphasized UI

Avoid excessive use of bold weights.

## Technical Font

**JetBrains Mono**

Use JetBrains Mono for technical or machine-oriented information.

Examples:

- Code
- JSON
- API responses
- Model identifiers
- Request IDs
- Token counts
- Latency
- URLs
- Logs
- Configuration values
- CLI commands

Do not use JetBrains Mono for ordinary body copy.

---

# 5. Typography Hierarchy

Keep the hierarchy compact.

### Page Title

Inter, semibold.

Use for the primary purpose or name of the current screen.

### Section Heading

Inter, semibold.

Clearly separates major functional areas.

### Component Heading

Inter, medium or semibold.

Use within cards and panels.

### Body

Inter, regular.

Optimize for readability rather than density.

### Labels

Inter, medium.

Keep labels concise.

### Technical Metadata

JetBrains Mono, regular or medium.

Technical metadata may use a slightly smaller size than surrounding interface text.

---

# 6. Layout

Demo applications should generally use a centered application container rather than stretching content across very wide screens.

Prefer:

- Clear page margins
- Consistent spacing
- Logical grouping
- Moderate content widths
- Responsive layouts
- Generous whitespace around major sections

Dense technical data may use wider containers where appropriate.

Avoid building a permanent sidebar unless the application genuinely requires multiple major sections.

---

# 7. Spacing

Use a consistent spacing scale rather than arbitrary values.

Recommended base scale:

```css
--space-1: 0.25rem;
--space-2: 0.5rem;
--space-3: 0.75rem;
--space-4: 1rem;
--space-6: 1.5rem;
--space-8: 2rem;
--space-12: 3rem;
--space-16: 4rem;
```

Prefer larger spacing between conceptual groups and smaller spacing between related elements.

---

# 8. Borders and Radius

Use moderate corner radii.

Recommended:

```css
--radius-sm: 6px;
--radius-md: 10px;
--radius-lg: 14px;
```

Use smaller radii for:

- Inputs
- Buttons
- Tags

Use medium or larger radii for:

- Cards
- Panels
- Dialogs

Avoid excessively rounded "pill" components unless the component naturally calls for them, such as tags or compact status indicators.

Borders should be subtle.

Avoid strong outlines around every container.

---

# 9. Shadows

Use shadows sparingly.

Prefer:

- Background contrast
- Borders
- Spacing

over large drop shadows.

Shadows are appropriate for elements that genuinely sit above the interface, such as:

- Dialogs
- Menus
- Popovers
- Floating controls

Avoid creating a "card floating on another card floating on another card" appearance.

---

# 10. Buttons

## Primary

Use:

- `--color-primary` background
- `--color-text-on-primary` text
- Inter medium or semibold

Reserve primary buttons for the main action within a context.

Examples:

- Run
- Submit
- Generate
- Send
- Save

A screen should generally have a clearly identifiable primary action.

## Secondary

Secondary actions should use a neutral or transparent treatment.

Use borders or subtle surface differentiation rather than another saturated color.

## Destructive

Destructive actions should use an appropriate semantic treatment and should never visually compete with the normal primary action unless immediate attention is required.

---

# 11. Forms

Forms should prioritize clarity.

Each input should have:

- A clear label
- Appropriate input type
- Visible focus state
- Helpful validation
- Optional supporting text when necessary

Use the primary purple for focus indicators.

Do not rely solely on placeholder text as a label.

Group advanced or uncommon settings separately from the primary workflow.

---

# 12. Cards and Panels

Cards should represent meaningful conceptual groups.

Good examples:

- Request configuration
- Response
- Model configuration
- Metrics
- Execution details
- Conversation
- Logs

Avoid wrapping every small piece of content in its own card.

Prefer spacing and typography for internal hierarchy.

---

# 13. Technical Content

Technical content is an important part of these demo applications and should be treated as a first-class design element.

Use JetBrains Mono for machine-generated or developer-oriented values.

Structured responses should be easy to scan.

Where appropriate, provide:

- Syntax formatting
- Copy controls
- Expand/collapse behavior
- Scrollable overflow
- Clear labels

Technical information should look intentionally exposed rather than like debugging output accidentally left on screen.

---

# 14. Loading and System States

Demo applications should clearly communicate what the system is doing.

Provide visible states for:

- Idle
- Loading
- Success
- Empty
- Error

For AI or API demos, consider exposing meaningful execution stages when available.

For example:

`Preparing request → Calling model → Processing response → Complete`

Avoid generic spinners when more informative progress can reasonably be shown.

---

# 15. Error Handling

Errors should explain:

1. What failed
2. What the user can do next

When useful for technical audiences, provide expandable technical details separately.

Do not replace the entire interface with an error screen when the user can reasonably recover without leaving the current workflow.

---

# 16. Motion

Motion should communicate state changes.

Appropriate uses include:

- Loading indicators
- Expanding advanced settings
- Opening dialogs
- Changing tabs
- Revealing results
- Updating status

Animations should be short and subtle.

Avoid decorative motion that distracts from the demo.

Respect `prefers-reduced-motion`.

---

# 17. Responsive Behavior

Demo applications should remain usable on smaller screens even when desktop is the primary target.

On narrow screens:

- Stack multi-column layouts
- Preserve readable padding
- Allow technical content to scroll horizontally when necessary
- Keep primary actions accessible
- Avoid shrinking text simply to preserve desktop layouts

---

# 18. Accessibility

At minimum:

- Maintain appropriate color contrast
- Provide visible keyboard focus
- Use semantic HTML
- Associate labels with inputs
- Do not communicate status through color alone
- Support keyboard interaction
- Respect reduced-motion preferences

Accessibility should be part of the component implementation rather than a later styling pass.

---

# 19. Agent Implementation Rules

When implementing interfaces from this design system:

- Reuse the defined design tokens.
- Use Inter for normal UI.
- Use JetBrains Mono for technical content.
- Use purple primarily to indicate interaction and emphasis.
- Prefer whitespace over additional containers.
- Prefer subtle borders over heavy shadows.
- Do not introduce gradients unless explicitly requested.
- Do not introduce new brand colors without a functional reason.
- Do not create oversized hero sections for functional applications.
- Do not use excessive rounded cards.
- Do not turn every piece of information into a badge.
- Do not hide useful technical information merely to make the interface appear simpler.
- Keep the demonstrated workflow visually dominant.

When requirements are ambiguous, choose the simpler interface.

---

# 20. Desired Character

The finished applications should feel:

**Technical without being sterile.  
Polished without being corporate.  
Distinct without being distracting.  
Simple without looking unfinished.**

The design exists to frame the demo—not become the demo.