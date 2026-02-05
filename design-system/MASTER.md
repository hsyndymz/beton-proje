# Design System: Beton Proje (UI/UX Pro Max)

## Brand Identity & Style
- **Name:** Industrial Engineering Swiss Style
- **Core Concept:** Technical precision, high readability, and safety-first industrial aesthetics.
- **Keywords:** Clean, functional, grid-based, industrial, precise.

## Color Palette
| Role | Hex | Tailwind Equivalent | Description |
|------|-----|-------------------|-------------|
| **Primary** | `#64748B` | `slate-500` | Main industrial grey |
| **Secondary** | `#94A3B8` | `slate-400` | Supporting grey |
| **CTA / Action** | `#F97316` | `orange-500` | Safety Orange for alerts/buttons |
| **Background** | `#F8FAFC` | `slate-50` | Clean workspace background |
| **Text (Body)** | `#334155` | `slate-700` | High-contrast technical text |
| **Green (Success)** | `#10B981` | `emerald-500` | Compliant results |
| **Red (Warning)** | `#EF4444` | `red-500` | Non-compliant / Risk |

## Typography
- **Heading:** `Fira Code` (Technical character, monospaced for data)
- **Body:** `Fira Sans` (Highly readable, modern Swiss feel)
- **Google Fonts Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

## UI Components Guidelines
### Cards
- **Background:** `#FFFFFF`
- **Border:** `1px solid #E2E8F0`
- **Shadow:** `0 1px 3px rgba(0,0,0,0.1)` (Subtle industrial shadow)
- **Radius:** `4px` (Sharp, professional edges)

### Buttons
- **Primary:** `bg-[#F97316]` with `text-white`
- **Secondary:** `border-[#64748B]` with `text-[#64748B]`
- **Transitions:** `duration-200 ease-in-out`

### Icons
- **Source:** SVG (Lucide or Heroicons)
- **Size:** `w-5 h-5` (20px) for standard UI actions.

## Layout
- **Pattern:** Grid-based Dashboard
- **Spacing:** Large whitespace between logical sections to reduce cognitive load in complex engineering data.
