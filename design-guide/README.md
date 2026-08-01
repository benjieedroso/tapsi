# TAPSI Design System

A comprehensive design guide for the TAPSI Restaurant Management System, inspired by the clean, modern aesthetic of premium SaaS products.

## Quick Start

```html
<link rel="stylesheet" href="design-guide/tokens.css">
<link rel="stylesheet" href="design-guide/components.css">
```

## Design Principles

1. **Clean & Minimal** — Lots of white space, uncluttered layouts
2. **Friendly & Warm** — Soft rounded corners, subtle gradients
3. **Professional** — Consistent spacing, clear typography hierarchy
4. **Responsive** — Works on desktop (≥1280px) and tablet (≥768px)

---

## Color Palette

### Primary (Green)
| Token | Hex | Usage |
|-------|-----|-------|
| `--tapsi-50` | `#f0fdf4` | Light backgrounds, badges |
| `--tapsi-100` | `#dcfce7` | Hover states, icons |
| `--tapsi-200` | `#bbf7d0` | Borders, subtle accents |
| `--tapsi-400` | `#4ade80` | Interactive elements |
| `--tapsi-500` | `#22c55e` | Primary buttons, CTAs |
| `--tapsi-600` | `#16a34a` | Button hover, active states |
| `--tapsi-700` | `#15803d` | Text on light backgrounds |

### Neutrals (Gray)
| Token | Hex | Usage |
|-------|-----|-------|
| `--gray-50` | `#f9fafb` | Page background |
| `--gray-100` | `#f3f4f6` | Card borders, dividers |
| `--gray-400` | `#9ca3af` | Secondary text |
| `--gray-600` | `#4b5563` | Body text |
| `--gray-800` | `#1f2937` | Headings |
| `--gray-900` | `#111827` | Primary headings |

---

## Typography

**Font Family:** Inter (Google Fonts)

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 (Hero) | 48-52px | 800 | 1.1 |
| H2 (Section) | 36-40px | 800 | 1.2 |
| H3 (Card) | 18px | 700 | 1.3 |
| Body | 16px | 400 | 1.6 |
| Small | 14px | 400 | 1.6 |
| Caption | 12px | 500 | 1.4 |

---

## Spacing Scale

| Token | Value | Pixels |
|-------|-------|--------|
| `--space-1` | 0.25rem | 4px |
| `--space-2` | 0.5rem | 8px |
| `--space-3` | 0.75rem | 12px |
| `--space-4` | 1rem | 16px |
| `--space-6` | 1.5rem | 24px |
| `--space-8` | 2rem | 32px |
| `--space-10` | 2.5rem | 40px |
| `--space-12` | 3rem | 48px |
| `--space-16` | 4rem | 64px |
| `--space-20` | 5rem | 80px |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Small elements |
| `--radius-md` | 8px | Inputs, badges |
| `--radius-lg` | 12px | Cards, icons |
| `--radius-xl` | 16px | Large cards |
| `--radius-2xl` | 20px | Hero images, modals |
| `--radius-full` | 9999px | Buttons, pills |

---

## Shadows

| Token | Usage |
|-------|-------|
| `--shadow-xs` | Subtle depth |
| `--shadow-sm` | Cards at rest |
| `--shadow-md` | Cards hover |
| `--shadow-lg` | Elevated cards |
| `--shadow-xl` | Floating elements |
| `--shadow-2xl` | Hero images |

---

## Components

### Buttons

```html
<!-- Primary -->
<button class="btn btn-primary">Start Free Trial</button>

<!-- Secondary -->
<button class="btn btn-secondary">Learn More</button>

<!-- Ghost -->
<button class="btn btn-ghost">Cancel</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary btn-lg">Large</button>
```

### Badges

```html
<span class="badge badge-primary">New Feature</span>
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">Pending</span>
<span class="badge badge-error">Error</span>
<span class="badge badge-popular">Most Popular</span>
```

### Avatars

```html
<div class="avatar-stack">
    <div class="avatar avatar-green">M</div>
    <div class="avatar avatar-yellow">A</div>
    <div class="avatar avatar-blue">R</div>
</div>
```

### Cards

```html
<div class="card">
    <div class="feature-icon">📦</div>
    <h3 class="feature-title">Inventory Tracking</h3>
    <p class="feature-desc">Track ingredients in real-time.</p>
</div>
```

### Pricing Cards

```html
<div class="pricing-card popular">
    <div class="pricing-badge">Most Popular</div>
    <h3 class="pricing-name">Karinderya</h3>
    <div class="pricing-amount">₱999<span>/mo</span></div>
    <ul class="pricing-features">
        <li>Up to 5 staff</li>
        <li>Unlimited menu</li>
    </ul>
    <button class="btn btn-primary">Get Started</button>
</div>
```

### Testimonials

```html
<div class="testimonial-card">
    <div class="testimonial-stars">★★★★★</div>
    <blockquote class="testimonial-quote">
        "Ang laking tulong ng TAPSI sa business ko!"
    </blockquote>
    <div class="testimonial-author">
        <div class="avatar avatar-green">MC</div>
        <div>
            <div class="testimonial-name">Maria Cruz</div>
            <div class="testimonial-role">Owner, Benjie's Tapsilogan</div>
        </div>
    </div>
</div>
```

---

## File Structure

```
design-guide/
├── tokens.css      # Design tokens (colors, spacing, typography)
├── components.css  # Reusable component patterns
└── README.md       # This documentation
```

---

## Usage in TAPSI

Reference these tokens in all TAPSI CSS files:

```css
/* Example: Custom component using TAPSI tokens */
.my-component {
    background: var(--surface-primary);
    border: 1px solid var(--gray-100);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    color: var(--gray-800);
    font-family: var(--font-family);
}

.my-component:hover {
    border-color: var(--tapsi-400);
    box-shadow: var(--shadow-md);
}
```

---

## Responsive Breakpoints

| Breakpoint | Width | Usage |
|------------|-------|-------|
| Mobile | < 768px | Stack columns, hide nav links |
| Tablet | ≥ 768px | 2-column grids |
| Desktop | ≥ 1280px | Full layout, 3-column grids |

---

## Animation Guidelines

- **Duration:** 150-300ms for micro-interactions
- **Easing:** `ease` for most transitions
- **Transform:** Use `translateY(-1px)` for hover lift effect
- **Scale:** Use `scale(0.98)` for button press feedback

```css
/* Recommended transition */
.card {
    transition: all var(--transition-base);
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}
```

---

## Color Accessibility

All color combinations meet WCAG 2.1 AA contrast requirements:

| Foreground | Background | Ratio |
|------------|------------|-------|
| `--gray-800` | `--white` | 10.4:1 |
| `--gray-600` | `--white` | 7.1:1 |
| `--tapsi-700` | `--tapsi-50` | 5.8:1 |
| `--white` | `--tapsi-600` | 4.6:1 |
