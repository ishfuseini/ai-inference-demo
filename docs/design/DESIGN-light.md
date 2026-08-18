---
name: Vibrant Kinetic
colors:
  surface: '#FFFFFF'
  surface-dim: '#e1d7e1'
  surface-bright: '#fff7fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fbf0fa'
  surface-container: '#f5ebf4'
  surface-container-high: '#efe5ef'
  surface-container-highest: '#e9dfe9'
  on-surface: '#1f1a21'
  on-surface-variant: '#4c4354'
  inverse-surface: '#342f36'
  inverse-on-surface: '#f8eef7'
  outline: '#7e7386'
  outline-variant: '#cfc2d7'
  surface-tint: '#8422dc'
  primary: '#6e00c1'
  on-primary: '#ffffff'
  primary-container: '#8a2be2'
  on-primary-container: '#eed9ff'
  inverse-primary: '#dcb8ff'
  secondary: '#006d3e'
  on-secondary: '#ffffff'
  secondary-container: '#52fca1'
  on-secondary-container: '#007241'
  tertiary: '#4c4a55'
  on-tertiary: '#ffffff'
  tertiary-container: '#64626d'
  on-tertiary-container: '#e2dfeb'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#efdbff'
  primary-fixed-dim: '#dcb8ff'
  on-primary-fixed: '#2c0051'
  on-primary-fixed-variant: '#6700b5'
  secondary-fixed: '#58ffa4'
  secondary-fixed-dim: '#2be28a'
  on-secondary-fixed: '#00210f'
  on-secondary-fixed-variant: '#00522d'
  tertiary-fixed: '#e4e1ed'
  tertiary-fixed-dim: '#c8c5d1'
  on-tertiary-fixed: '#1b1b24'
  on-tertiary-fixed-variant: '#474650'
  background: '#FCFDFE'
  on-background: '#1f1a21'
  surface-variant: '#e9dfe9'
  ink-muted: '#4a4458'
  border-subtle: '#e5e0f0'
typography:
  headline-display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.02em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.04em
  stat-value:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '800'
    lineHeight: '1'
    letterSpacing: -0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

This design system embodies an **energetic, modern, and high-tech** persona. It is built for platforms that require high performance and technical sophistication without sacrificing visual excitement. The style is a hybrid of **Minimalism** and **High-Contrast**, using a clean, airy canvas to let hyper-saturated "electric" colors guide the user's focus.

The emotional response should be one of "controlled intensity"—precise enough for technical workflows, yet vibrant enough to feel forward-thinking. The visual hierarchy is driven by bold color blocks and crisp, functional typography rather than complex textures or skeuomorphic effects.

## Colors

The palette is anchored by **Vibrant Purple**, used for primary actions and brand presence. **Vibrant Green** serves as a high-visibility accent for status indicators, success states, and secondary highlights.

- **Core Contrast:** Deep black-purple (Ink) provides maximum legibility against the clean off-white background.
- **Tonal Support:** Soft purple-tinted white is used for large surface areas like sidebars or card backgrounds to maintain the brand's chromatic temperature without overwhelming the eye.
- **Functional Use:** Use the primary purple for the most important "call to action." Use the accent green sparingly to draw attention to growth, completion, or specialized technical features.

## Typography

Inter is utilized for its technical neutrality and excellent legibility at small sizes. To align with the "high-tech" narrative:
- **Headlines:** Use heavy weights (700+) and tight letter-spacing to create a "locked-in" architectural feel.
- **Data:** Statistical values should use the `stat-value` style, which emphasizes weight over size for a dense, information-rich look.
- **Labels:** Use uppercase for `label-md` when used in navigation or section headers to increase formal structure.

## Layout & Spacing

The layout follows a **fluid grid** system based on an 8px spacing rhythm. 

- **Desktop:** 12-column grid with a 1280px max-width container. Content should be centered with generous 40px external margins to evoke a premium feel.
- **Mobile:** Single column with 16px margins.
- **Rhythm:** Use increments of 8px (8, 16, 24, 32, 48, 64) for all padding and margins. This mathematical consistency reinforces the technical nature of the product.

## Elevation & Depth

This system avoids traditional heavy shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**.

- **Level 0 (Background):** `#FCFDFE`.
- **Level 1 (Cards/Surfaces):** White background with a 1px border using `#e5e0f0`.
- **Level 2 (Modals/Popovers):** White background with a very soft, diffused purple-tinted shadow (`rgba(138, 43, 226, 0.08)`) and a slightly stronger border.
- **Interaction:** On hover, interactive elements like cards should transition their border color to the primary purple at low opacity rather than increasing shadow depth.

## Shapes

The architectural language uses **Rounded (8px)** corners as the standard. This provides a balance between the precision of a sharp grid and the approachability of modern software.

- **Standard (8px):** Buttons, Input fields, and small UI components.
- **Large (16px):** Primary cards and main content containers.
- **Full (Pill):** Reserved exclusively for Status Chips and Tags to differentiate them from actionable buttons.

## Components

- **Buttons:** Primary buttons use a solid `#8a2be2` fill with white text. Secondary buttons use a transparent background with a 1px border of the primary color.
- **Inputs:** Use a 1px `#e5e0f0` border that transforms to a 2px `#8a2be2` border on focus. 
- **Chips:** Status-dependent. Success chips use the accent green (`#2be28a`) at 10% opacity for the background and 100% opacity for the text.
- **Cards:** White surfaces with 16px corner radius and a subtle purple-tinted border. Internal padding should be a minimum of 24px.
- **Data Tables:** Use thin `#f0ecf9` horizontal dividers. Header rows should use `label-md` in uppercase for a professional, technical aesthetic.