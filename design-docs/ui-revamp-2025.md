# Nexus UI/UX Revamp - Design System 2026

## Overview

This document outlines the complete UI/UX revamp of the Nexus application, transforming it into a professional, modern, dark-mode-only interface while maintaining all existing functionality.

**Design Philosophy:**
- **Professional**: Clean, sophisticated, business-ready aesthetic
- **Simple**: Remove clutter, focus on content and usability
- **Smooth**: Subtle animations, polished transitions (200-300ms)
- **Engaging**: Modern design that keeps users interested
- **Consistent**: Unified design system across all components

---

## 1. Color Palette

### Primary Background Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-base` | `#0a0a0f` | Main app background |
| `--bg-elevated` | `#12121a` | Cards, sidebars, elevated surfaces |
| `--bg-surface` | `#1a1a24` | Input fields, interactive elements |
| `--bg-hover` | `#22222e` | Hover states for surfaces |
| `--bg-active` | `#2a2a38` | Active/selected states |

### Accent Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--accent-primary` | `#6366f1` | Primary actions, links (Indigo) |
| `--accent-primary-hover` | `#818cf8` | Primary hover state |
| `--accent-secondary` | `#22c55e` | Success, confirmations (Green) |
| `--accent-tertiary` | `#3b82f6` | Info, secondary accent (Blue) |

### Text Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--text-primary` | `#f4f4f5` | Headings, important text |
| `--text-secondary` | `#a1a1aa` | Body text, descriptions |
| `--text-tertiary` | `#71717a` | Captions, placeholder text |
| `--text-muted` | `#52525b` | Disabled text |

### Border Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--border-subtle` | `rgba(255,255,255,0.06)` | Subtle dividers |
| `--border-default` | `rgba(255,255,255,0.10)` | Standard borders |
| `--border-strong` | `rgba(255,255,255,0.15)` | Emphasized borders |

### Semantic Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `--success` | `#22c55e` | Success states |
| `--error` | `#ef4444` | Error states |
| `--warning` | `#f59e0b` | Warning states |
| `--info` | `#3b82f6` | Information states |

---

## 2. Typography

### Font Family
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Type Scale
| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Display | 48px | 800 | 1.1 | Hero headlines |
| H1 | 32px | 700 | 1.2 | Page titles |
| H2 | 24px | 600 | 1.3 | Section headers |
| H3 | 18px | 600 | 1.4 | Card titles |
| Body | 15px | 400 | 1.6 | Main content |
| Small | 13px | 400 | 1.5 | Captions, metadata |
| Micro | 11px | 500 | 1.4 | Labels, badges |

---

## 3. Spacing System

Based on 4px grid:
- `xs`: 4px
- `sm`: 8px  
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `2xl`: 48px
- `3xl`: 64px

### Component Spacing
- **Card padding**: 20-24px
- **Button padding**: 10px 20px (default), 12px 24px (large)
- **Input padding**: 12px 16px
- **Section margin**: 48-64px

---

## 4. Border Radius

| Size | Value | Usage |
|------|-------|-------|
| `sm` | 6px | Buttons, inputs |
| `md` | 10px | Cards, modals |
| `lg` | 14px | Large containers |
| `xl` | 20px | Feature cards |
| `full` | 9999px | Pills, avatars |

---

## 5. Shadows

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
--shadow-md: 0 4px 12px rgba(0,0,0,0.5);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.6);
--shadow-glow: 0 0 20px rgba(99,102,241,0.3); /* Accent glow */
```

---

## 6. Component Patterns

### Buttons

**Primary Button**
```css
background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
color: white;
padding: 10px 20px;
border-radius: 8px;
font-weight: 600;
transition: all 0.2s ease;
box-shadow: 0 2px 8px rgba(99,102,241,0.25);
```

**Secondary Button**
```css
background: rgba(255,255,255,0.06);
border: 1px solid rgba(255,255,255,0.10);
color: #f4f4f5;
```

**Ghost Button**
```css
background: transparent;
color: #a1a1aa;
/* hover: background: rgba(255,255,255,0.06) */
```

### Input Fields
```css
background: rgba(255,255,255,0.04);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 10px;
padding: 12px 16px;
color: #f4f4f5;
/* focus: border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.15) */
```

### Cards
```css
background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 14px;
padding: 20px;
```

### Sidebar
```css
background: linear-gradient(180deg, #12121a 0%, #0a0a0f 100%);
border-right: 1px solid rgba(255,255,255,0.06);
width: 260px;
```

---

## 7. Animations & Transitions

### Timing
- **Fast**: 150ms (micro-interactions)
- **Normal**: 200ms (hover states)
- **Smooth**: 300ms (modals, sidebars)

### Easing
```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### Standard Animations
```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Slide In */
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

/* Pulse (for loading) */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

---

## 8. Page-Specific Guidelines

### Landing Page
- Hero section with gradient text
- Feature cards with icon accents
- Subtle background glow effects
- Clear CTA buttons

### Login Page
- Centered card layout
- Minimal distractions
- Clear form validation feedback
- Brand-consistent styling

### Chat Interface
- Two-column layout (sidebar + main)
- Clear message distinction (user vs AI)
- Smooth scroll behavior
- Floating input area with subtle elevation

### Admin Dashboard
- Data-focused layout
- Clear stats cards with color coding
- User cards with action buttons
- Modal for detailed views

---

## 9. Accessibility

- Minimum contrast ratio: 4.5:1 for normal text
- Focus states: 2px solid accent outline with offset
- Interactive elements: Minimum 44x44px touch target
- Screen reader support via ARIA labels

---

## 10. Before/After Summary

### Changes Made

| Area | Before | After |
|------|--------|-------|
| Theme System | Light/Dark toggle | Dark-only, cleaner code |
| Primary Accent | Green/Emerald mix | Consistent Indigo (#6366f1) |
| Background | Multiple gradient variations | Unified dark palette |
| Typography | Inconsistent weights | Systematic type scale |
| Animations | Various durations | Standardized timing |
| Borders | Mixed opacity values | Consistent tokens |
| Cards | Heavy gradients | Subtle, elegant surfaces |
| Buttons | Multiple styles | Unified button system |

### Files Modified

1. `/static/css/theme.css` - Complete dark-mode redesign
2. `/static/js/theme.js` - Simplified (no toggle needed)
3. `/templates/index.html` - Landing page
4. `/chat/templates/registration/login.html` - Login page
5. `/chat/templates/chat/index.html` - Main chat interface
6. `/chat/templates/chat/dashboard.html` - Admin dashboard
7. `/chat/templates/chat/partials/*.html` - All partial components
8. `/templates/404.html` - Error page
9. `/templates/500.html` - Error page

---

## 11. Implementation Notes

### Removed Features
- Theme toggle button (data-theme-toggle)
- Light mode CSS rules (html.light selectors)
- System preference detection
- Theme persistence logic

### Key CSS Variables
All components should use CSS variables for consistency:
```css
/* Usage Example */
.component {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}
```

---

**Document Version**: 2.0
**Last Updated**: January 2026
**Author**: Frontend Design Team
