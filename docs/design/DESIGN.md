# Demo Application Design System

This document defines the shared visual language for demo applications. The goal is to create interfaces that feel polished and intentional while remaining focused on demonstrating the underlying product, API, workflow, or technical concept.

The design should feel **clean, technical, approachable, bold, and lightweight** rather than like a heavily branded production SaaS application.

The visual language favors **sharp geometry, visible structure, asymmetric composition, bold typography, and purposeful color**.

---

# 1. Design Principles

## Demo First

The interface exists to make the demonstrated concept easy to understand.

Prefer:

- Clear information hierarchy
- Obvious actions
- Visible system state
- Simple navigation
- Intentional asymmetric layouts
- Enough whitespace to understand the workflow
- Visible structure through grids, borders, and grouping

Avoid:

- Decorative UI that competes with the demo
- Excessive dashboard widgets
- Unnecessary navigation
- Marketing-style layouts inside functional demos
- Visual complexity added only to make the application look "finished"
- Generic AI-generated SaaS aesthetics

## Intentional, Not Generic

Demo applications should look designed rather than like framework defaults.

Use the shared color, typography, spacing, geometry, and component conventions in this document instead of introducing arbitrary values.

Prefer strong, simple visual decisions over layers of decoration.

## Technical Information Should Be Visible

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
  --color-hero: #1f96db;
  --color-accent: #ed7c3a;
  --color-accent-secondary: #ab80f3;

  --color-neutral-light: #dedbf1;
  --color-neutral-lightest: #FCFDFE;

  --color-neutral-dark: #525252;
  --color-neutral-darkest: #2a3139;
}
```

## Hero

`#1f96db`

The hero blue is the primary identifying color of the design system.

Use for:

- Major visual emphasis
- Key interface regions
- Selected states
- Important structural accents

It does not need to appear in every component.

## Accent

`#ed7c3a`

The orange accent communicates interaction and emphasis.

Use for:

- Primary actions
- Active indicators
- Important interactive elements
- Small high-attention details

Avoid using the accent as a large decorative background without a functional reason.

## Secondary Accent

`#ab80f3`

Use the secondary purple accent selectively when a second level of visual distinction is required.

Examples:

- Secondary data series
- Technical categorization
- Supporting highlights
- Distinct system states

It should remain secondary to the hero and primary accent colors.

## Neutrals

Use the neutral palette for the majority of the interface.

`#FCFDFE` — primary light surface or background  
`#dedbf1` — secondary light surface and structural contrast  
`#525252` — muted text and secondary UI  
`#2a3139` — primary dark text and dark surfaces

Do not use pure black (`#000000`).

---

# 3. Color Usage

Color should communicate hierarchy, interaction, or meaning rather than decorate every component.

A typical screen should be dominated by:

1. Light neutral backgrounds
2. Structured surfaces
3. Dark neutral text
4. Hero blue for visual identity
5. Orange accent for interaction
6. Secondary purple only where additional distinction is useful

Use the defined colors directly and confidently. Do not unnecessarily desaturate the core palette.

Do not introduce arbitrary brand colors into individual demo applications.

Semantic colors for success, warning, error, and informational states may be introduced when required, but they should remain visually secondary to the core palette.

Do not communicate semantic state through color alone.

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
- `500` — controls, labels, and navigation
- `600` — buttons and component headings
- `700+` — page titles, section headings, and major visual statements

Bold typography is an intentional part of the visual system.

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

Keep the hierarchy compact but visually decisive.

## Page Title

Inter, bold (`700+`).

Use for the primary purpose or name of the current screen.

## Section Heading

Inter, bold (`700`).

Clearly separates major functional areas.

## Component Heading

Inter, semibold (`600`).

Use within cards and panels.

## Body

Inter, regular (`400`).

Optimize for readability rather than density.

## Labels

Inter, medium (`500`).

Keep labels concise.

## Technical Metadata

JetBrains Mono, regular or medium (`400–500`).

Technical metadata may use a slightly smaller size than surrounding interface text.

---

# 6. Layout

## Grid

CSS Grid is the preferred layout system for primary page composition.

Use:

- Maximum content width: `1280px`
- Centered containment
- `1.5rem` minimum horizontal page padding
- Visible structural alignment
- Asymmetric compositions where appropriate

## Spacing Rhythm

Base unit: `0.5rem` / `8px`.

Use a balanced spacing rhythm with clear separation between conceptual groups.

## Section Spacing

For major page sections:

```css
gap: clamp(4rem, 8vw, 8rem);
```

Smaller functional application screens may reduce this spacing when necessary.

## Composition

Prefer:

- Asymmetric hero compositions
- Varied card sizes
- Offset content
- Intentional negative space
- Unequal columns where hierarchy benefits from them
- Visible grid relationships

Avoid:

- Three equal-width feature columns
- Repetitive card grids without hierarchy
- Perfectly symmetrical layouts by default
- Filling space simply because it is available

## Mobile Collapse

All multi-column layouts should collapse below `768px` unless a component has a specific reason to retain columns.

Do not allow page-level horizontal overflow.

## Viewport Height

Do not use:

```css
h-screen
```

Prefer:

```css
min-h-[100dvh]
```

## z-index Contract

```text
base        0
sticky-nav  100
overlay     200
modal       300
toast       500
```

Do not introduce arbitrary z-index values outside this hierarchy without a specific reason.

---

# 7. Spacing

Use a consistent spacing scale rather than arbitrary values.

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

The `8px` unit should form the default rhythm, with `4px` available for fine-grained adjustments.

---

# 8. Geometry, Borders & Radius

## Corner Radius

The default corner radius is:

```css
--radius-default: 0px;
```

Sharp corners are a defining characteristic of the design system.

Buttons, cards, inputs, panels, navigation elements, dialogs, and primary containers should use `0px` radius unless a component has a functional reason to require another shape.

Do not introduce rounded cards as decoration.

## Borders

Visible borders are encouraged when they help expose structure.

Prefer:

```css
border: 1px solid;
```

Use border color appropriate to the surrounding neutral palette.

Borders may be used to:

- Define application regions
- Separate technical information
- Establish grid structure
- Group related controls
- Create hierarchy without additional containers

---

# 9. Elevation & Depth

The interface should feel primarily **flat and structural**, not layered and floating.

Prefer:

- Borders
- Contrast
- Grid structure
- Typography
- Spacing

over elevation.

When elevation is necessary, keep it restrained.

Recommended card shadow:

```css
box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
```

Use shadows primarily for elements that genuinely sit above the interface:

- Modals
- Menus
- Popovers
- Floating controls

Do not use:

- Outer glows
- Large diffuse shadows
- Multiple stacked shadows
- Floating-card-on-floating-card compositions

---

# 10. Components

## Primary Button

- Accent color fill
- Sharp `0px` corners
- High-contrast text
- Inter `600`
- Clear border when useful
- No outer glow

Primary buttons represent the main action within their context.

Examples:

- Run
- Submit
- Generate
- Send
- Save

## Secondary / Ghost Button

Use:

- Transparent or neutral background
- `1px–1.5px` border
- Dark neutral or hero-colored text
- Sharp `0px` corners

Secondary actions should never visually compete with the primary action.

## Cards

Use:

- Sharp `0px` corners
- Neutral surface
- `1px` border
- Optional subtle shadow
- Clear internal spacing

Cards should represent meaningful conceptual groups rather than decorate individual pieces of information.

## Inputs

Use:

- Label above input
- `1px` border
- Sharp `0px` corners
- Clear keyboard focus state
- Error text below the field

Recommended focus treatment:

```css
outline: 2px solid var(--color-accent);
outline-offset: 2px;
```

Do not use floating labels.

## Navigation

Use:

- Neutral surface
- Visible structural alignment
- Active accent indicator
- Inter `500` for active items

Navigation should remain minimal in demo applications.

## Skeletons

Skeletons should match the dimensions of the content they represent.

Prefer structural loading placeholders over generic circular spinners.

If animated, respect the motion rules defined below.

## Empty States

Use:

- Icon from the established icon system
- Concise explanation
- Clear next action when one exists

Do not use decorative emoji.

---

# 11. Motion & Interaction

The default interface should feel immediate.

Avoid decorative transitions and excessive animation.

Simple interaction feedback may use short motion when it materially improves usability.

## Interaction Feedback

Recommended maximum duration:

```text
100–200ms
```

Appropriate uses:

- Hover feedback
- Focus changes
- Menus
- Dialogs
- Expand/collapse interactions
- State changes

Avoid animating ordinary layout changes.

## Entry Animation

Do not animate page content into view by default.

If an entry animation serves a specific demonstration purpose, use:

- Opacity
- Small translate-Y
- Ease-out timing
- No excessive staggering

## Performance

Only animate:

- `transform`
- `opacity`

Avoid animation of layout-triggering properties.

## Reduced Motion

Always respect:

```css
@media (prefers-reduced-motion: reduce)
```

Disable non-essential motion when reduced motion is requested.

---

# 12. Technical Content

Technical content is a first-class design element.

Use JetBrains Mono for machine-generated or developer-oriented values.

Structured responses should be easy to scan.

Where appropriate, provide:

- Syntax highlighting
- Copy controls
- Expand/collapse behavior
- Scrollable overflow
- Clear labels
- Request and response separation

Technical information should look intentionally exposed rather than like debugging output accidentally left on screen.

Do not hide useful technical information merely to make an interface appear simpler.

---

# 13. Loading & System States

Demo applications should clearly communicate what the system is doing.

Provide visible states for:

- Idle
- Loading
- Success
- Empty
- Error

For AI or API demos, expose meaningful execution stages when available.

For example:

```text
Preparing request → Calling model → Processing response → Complete
```

Prefer informative progress over an unexplained spinner.

---

# 14. Error Handling

Errors should explain:

1. What failed
2. What the user can do next

When useful for technical audiences, provide expandable technical details separately.

Preserve:

- Error codes
- Request IDs
- Provider responses
- Relevant debugging context

when exposing them would help explain the demonstrated system.

Do not replace the entire interface with an error screen when the user can reasonably recover within the current workflow.

---

# 15. Responsive Behavior

Demo applications should remain usable on smaller screens even when desktop is the primary target.

On narrow screens:

- Stack multi-column layouts
- Preserve readable padding
- Allow technical content to scroll horizontally when necessary
- Keep primary actions accessible
- Preserve clear hierarchy
- Avoid shrinking typography merely to preserve a desktop composition
- Prevent page-level horizontal overflow

Asymmetry should gracefully simplify rather than disappear into a cramped desktop layout.

---

# 16. Accessibility

At minimum:

- Maintain appropriate color contrast
- Provide visible keyboard focus
- Use semantic HTML
- Associate labels with inputs
- Do not communicate status through color alone
- Support keyboard interaction
- Respect reduced-motion preferences
- Provide accessible names for icon-only controls

Accessibility should be part of component implementation rather than a later styling pass.

---

# 17. Content & Iconography

## Icons

Use a consistent icon system such as:

- Lucide
- Heroicons

Do not use emoji as interface icons.

## Demo Content

Do not use generic lorem ipsum.

Use realistic example content that helps explain the demonstrated workflow.

Demo data should feel plausible without pretending to represent real production data.

## Copy

Keep interface language direct and specific.

Avoid generic AI and SaaS copywriting clichés such as:

- "Elevate"
- "Seamless"
- "Unleash"
- "Next-Gen"

Prefer labels that describe exactly what an action does.

## External Images

Do not depend on fragile or arbitrary external image URLs.

For placeholders, prefer:

- Inline SVG
- Locally controlled assets
- Reliable placeholder services when appropriate

---

# 18. Do's and Don'ts

## Do

- Use sharp `0px` corners
- Use bold typography for major hierarchy
- Use the core colors confidently
- Use visible grids and borders
- Use asymmetric composition intentionally
- Keep the demonstrated workflow visually dominant
- Expose useful technical information
- Use whitespace to separate concepts
- Use realistic demo content
- Keep interactions immediate and purposeful

## Don't

- Don't use emoji in the UI
- Don't use pure black (`#000000`)
- Don't introduce arbitrary oversaturated colors
- Don't use three equal-width feature columns by default
- Don't use `h-screen`
- Don't use generic lorem ipsum
- Don't use AI copywriting clichés
- Don't use rounded cards
- Don't introduce gradients unless explicitly required
- Don't use decorative glows
- Don't turn every piece of metadata into a badge
- Don't animate elements simply because they can be animated
- Don't hide useful technical details for aesthetic minimalism

---

# 19. Agent Implementation Rules

When implementing interfaces from this design system:

- Reuse the defined design tokens.
- Use Inter for normal UI.
- Use JetBrains Mono for technical content.
- Use hero blue for visual identity.
- Use orange accent primarily for interaction and emphasis.
- Use secondary purple sparingly.
- Use `0px` border radius by default.
- Prefer visible structure over decorative containers.
- Prefer whitespace and borders over heavy shadows.
- Prefer asymmetric composition over repetitive equal-column grids.
- Keep transitions minimal and functional.
- Do not introduce gradients unless explicitly requested.
- Do not introduce new brand colors without a functional reason.
- Do not create oversized marketing heroes for functional applications.
- Do not turn every piece of information into a card or badge.
- Do not hide useful technical information merely to make the interface appear simpler.
- Keep the demonstrated workflow visually dominant.

When requirements are ambiguous, choose the **simpler, sharper, more structural** interface.

---

# 20. Desired Character

The finished applications should feel:

**Technical without being sterile.**  
**Polished without being corporate.**  
**Bold without being loud.**  
**Distinct without being distracting.**  
**Structured without being rigid.**  
**Simple without looking unfinished.**

The design exists to frame the demo—not become the demo.