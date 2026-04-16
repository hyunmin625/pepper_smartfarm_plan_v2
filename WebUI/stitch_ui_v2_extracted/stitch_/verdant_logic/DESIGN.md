# Design System: Smart Farm Monitoring & Control

## 1. Overview & Creative North Star

### Creative North Star: "The Digital Agronomist"
This design system is built to transform complex agricultural data into an intuitive, high-end editorial experience. We reject the "industrial dashboard" trope of heavy lines and cluttered grids. Instead, we embrace **The Digital Agronomist**—a philosophy of clarity, organic breathability, and precision. 

The system utilizes a "Soft-Focus Layout" strategy. By leveraging asymmetric widget sizes and overlapping tonal surfaces, we guide the user's eye toward critical environmental shifts without overstimulating them. It is clean enough for the laboratory, but vibrant enough to reflect the vitality of the crops it monitors.

---

## 2. Colors & Surface Philosophy

### Color Palette
The palette is anchored in agricultural vitality (`primary: #006a26`) and balanced by a sophisticated neutral foundation.

*   **Primary (Growth):** `#006a26` (Primary) / `#87ff94` (Container). Use for active monitoring states and successful growth metrics.
*   **Secondary (Harvest):** `#00693e`. Used for device controls and manual overrides.
*   **Tertiary (Atmosphere):** `#006571`. Reserved for auxiliary data like humidity or climate history.
*   **Neutral (Soil & Sky):** `#f5f7f9` (Background) to `#ffffff` (Surface Lowest).

### The "No-Line" Rule
**Prohibit 1px solid borders for sectioning.** To achieve a premium feel, boundaries must be defined solely through:
1.  **Background Shifts:** Place a `surface-container-low` card against a `background` page.
2.  **Negative Space:** Use the spacing scale to create groupings.
3.  **Soft Shadows:** Use ambient, tinted depth for elevation.

### Surface Hierarchy & Nesting
Treat the UI as a series of nested, physical layers:
*   **Level 0 (Base):** `background` (`#f5f7f9`).
*   **Level 1 (Sections):** `surface-container-low` (`#eef1f3`).
*   **Level 2 (Interactive Widgets):** `surface-container-lowest` (`#ffffff`).
*   **Level 3 (Overlays/Pop-ups):** Glassmorphism (Semi-transparent `surface` with 20px backdrop-blur).

### The "Glass & Gradient" Rule
Standard cards are static. For hero metrics (e.g., "Yield Forecast"), apply a subtle linear gradient from `primary` to `primary_container` at a 15-degree angle. For floating navigation or top bars, use `surface` at 80% opacity with a blur to create a "frosted glass" effect that allows the agricultural map or data underneath to bleed through softly.

---

## 3. Typography

The typography strategy pairs a technical, high-legibility sans-serif with an authoritative display face.

*   **Display & Headlines (Manrope):** Chosen for its modern, geometric structure. Large `display-lg` (3.5rem) should be used for critical environment readings (e.g., current Temperature).
*   **Body & Titles (Inter):** The "Workhorse." Inter provides exceptional readability for dense sensor logs and device status lists.
*   **The Editorial Hook:** Use `headline-sm` for widget titles, but pair it with a `label-sm` in all-caps (0.05em letter spacing) to provide a professional, structured hierarchy.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering**. Avoid shadows for standard layout elements. A widget is "raised" simply by being `surface-container-lowest` (#FFFFFF) against the `background` (#f5f7f9).

### Ambient Shadows
For active states or modal device controls:
*   **Color:** Tint the shadow with `on-surface` at 6% opacity.
*   **Blur:** Use a high diffusion (e.g., 30px-50px) to mimic natural, soft-box lighting.

### The "Ghost Border" Fallback
If high-density data requires containment (e.g., a complex data table), use a **Ghost Border**: `outline-variant` at 15% opacity. Never use high-contrast solid lines.

---

## 5. Components

### Cards & Widgets
The core of the dashboard.
*   **Style:** `roundness-lg` (1rem). No borders.
*   **Interaction:** On hover, shift background from `surface-container-lowest` to `surface-bright`.
*   **Content:** Forbid dividers. Use 24px of vertical white space to separate sensor headers from data visualizations.

### Buttons
*   **Primary:** Solid `primary` with `on_primary` text. `roundness-full` for a modern, organic feel.
*   **Secondary:** `surface-container-high` background with `on_surface` text.
*   **Ghost:** Transparent background with `primary` text; only for low-priority actions.

### Status Indicators (Chips)
*   **Good:** `primary_container` background with a small `primary` dot.
*   **Warning:** `yellow` (use custom tonal variant) with a soft pulse animation.
*   **Alert:** `error_container` background with `on_error_container` text.

### Sensor Input Fields
*   **Visuals:** Bottom-aligned labels using `label-md`. The input container should be `surface-container-low` with a `roundness-sm`.
*   **Focus State:** A "Ghost Border" of `primary` at 40% opacity.

### Navigation Sidebar
*   **Width:** Narrow (80px) for icons or Expanded (260px).
*   **Style:** `surface_container_low` with no right-side border. Active states use a `primary` vertical "pill" indicator (4px wide) on the far left.

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use `primary_fixed_dim` for background elements of graphs to ensure the green doesn't become overwhelming.
*   **Do** use asymmetrical layouts. A "Weather" widget can be twice as wide as a "Humidity" widget to create visual interest.
*   **Do** prioritize whitespace. If it feels crowded, increase padding by 8px.

### Don't:
*   **Don't** use black (`#000000`) for text. Use `on_surface` (`#2c2f31`) to maintain a soft, high-end editorial tone.
*   **Don't** use traditional "Drop Shadows" with 20%+ opacity. They look dated and heavy.
*   **Don't** use icons with varying line weights. Stick to a 2px stroke weight to match the Inter/Manrope typeface balance.