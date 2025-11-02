# The Planner's Assistant - Frontend

Modern React frontend for The Planner's Assistant, a comprehensive planning analysis toolkit powered by AI reasoning and dynamic panel-based interfaces.

## Overview

This is the web interface for TPA, featuring:

- **6 Specialized Tools**: Evidence Base, Vision & Concepts, Policy Drafter, Strategy Modeler, Site Assessment, and Feedback Analysis
- **Dynamic UI**: Tool selection grid that hides when a tool is active, with smooth animations
- **Real-time Streaming**: SSE-based reasoning stream with live panel updates
- **Responsive Design**: Mobile-first, production-ready Tailwind CSS
- **Type-safe**: Full TypeScript with strict mode

## Tech Stack

- **React 19** with hooks
- **Vite 6** for blazing-fast dev and build
- **TypeScript 5.8** for type safety
- **Tailwind CSS 3.4** (local build, not CDN)
- **Framer Motion 12** for smooth animations
- **Lucide React** for icons
- **MapLibre GL** for spatial visualizations
- **Playwright** for E2E testing

## Quick Start

### Prerequisites

- Node.js 18+ (or use the project's pnpm)
- Backend services running (kernel on :8081, proxy on :8082)
- PostgreSQL with sample data loaded

### Installation

```bash
# Install dependencies
pnpm install

# Run dev server (http://localhost:5173)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview

# Run E2E tests
pnpm test:e2e
```

## Project Structure

```
website/
├── components/
│   ├── app/
│   │   ├── AppWorkspace.tsx      # Main tool interface with module switching
│   │   ├── PanelHost.tsx         # Dynamic panel renderer
│   │   ├── RunControls.tsx       # Analysis controls (deprecated, integrated)
│   │   ├── ErrorBoundary.tsx     # React error boundary
│   │   └── panels/               # Panel components (ApplicablePolicies, etc.)
│   ├── Layout.tsx                # App shell with header/footer
│   ├── Header.tsx, Footer.tsx    # Navigation and branding
│   └── [marketing components]    # Landing page components
├── pages/
│   ├── AppPage.tsx               # /app route - tool workspace
│   ├── HomePage.tsx              # / route - marketing landing
│   └── [other pages]             # Architecture, Pillars, etc.
├── hooks/
│   ├── useReasoningStream.ts     # SSE client for kernel streaming
│   └── [other hooks]
├── App.tsx                       # Router setup (HashRouter)
├── index.tsx                     # React root mount
└── vite.config.ts                # Vite configuration

```

## Configuration

### Environment Variables

Create `.env.local`:

```bash
# Backend kernel URL (defaults to http://localhost:8081)
VITE_KERNEL_URL=http://localhost:8081

# Optional: Gemini API key (if using Vision module with client-side calls)
VITE_GEMINI_API_KEY=your_key_here
```

### Tailwind Configuration

- **Config**: `tailwind.config.ts` - narrowed content globs for performance
- **PostCSS**: `postcss.config.js` - Tailwind + Autoprefixer
- **Entry**: `index.css` - `@tailwind` directives

## Key Features

### Dynamic Module Switching

The UI has two states:

1. **Module Selector** (default): 6-card grid with tool descriptions
2. **Tool Interface**: Input panel + results panel, with "Back to Tools" button

Navigation is managed via `selectedModule` state (null → show grid, Module → show tool).

### Real-time Streaming

`useReasoningStream` hook connects to kernel `/reason` endpoint:

- Handles SSE events: `token`, `intent`, `final`
- Builds panel array from `show_panel` intents
- Streams reasoning text to UI

### Panel System

Panels are React components rendered dynamically:

- **Registry**: `PanelHost` maps panel types to components
- **Props**: Each panel receives `data` from kernel intent
- **Empty State**: Friendly "Ready to Analyze" message when no panels

Available panels:
- `ApplicablePolicies` - Policy search results
- `EvidenceSnapshot` - Constraints and context
- `KeyIssuesMatrix` - Issues table
- `Precedents` - Precedent cases
- `PlanningBalance` - Balance summary
- `DraftDecision` - Decision recommendation
- `PolicyEditor` - Policy editing
- `ConflictHeatmap` - Policy conflicts
- `ScenarioCompare` - Strategy comparison
- `VisualCompliance` - Design code check
- `ConsultationThemes` - Feedback themes
- `MapView` - Spatial visualization

## Testing

### E2E Tests (Playwright)

```bash
# Run all tests
pnpm test:e2e

# Run in UI mode
pnpm test:e2e -- --ui

# Run specific test
pnpm test:e2e tests/e2e/app.spec.ts
```

Tests cover:
- Module grid rendering
- Tool selection and navigation
- Example prompt interaction
- Back button navigation
- Empty state display

## Development

### Adding a New Panel

1. Create component in `components/app/panels/YourPanel.tsx`:

```tsx
export function YourPanel({ data }: { data: any }) {
  return <div>Your panel content</div>;
}
```

2. Register in `PanelHost.tsx`:

```tsx
const PANEL_COMPONENTS = {
  your_panel: YourPanel,
  // ... existing panels
};
```

3. Kernel emits intent with `type: 'your_panel'`

### Adding a New Module

1. Add to `MODULES` array in `AppWorkspace.tsx`
2. Add example prompts to `EXAMPLE_PROMPTS`
3. Update kernel to handle new module type

## Performance

- **Tailwind**: Local build with purged unused styles (~5KB gzipped)
- **Code splitting**: Vite auto-splits routes and heavy components
- **Lazy loading**: MapLibre and heavy panels lazy-loaded
- **File watchers**: Optimized via `.vscode/settings.json` (excludes node_modules, dist, .git)

## Troubleshooting

### VS Code Freezing

Already configured in `.vscode/settings.json`:
- Limited to 5 open editors
- Excluded heavy folders from file watching
- Disabled local history and Git auto-fetch

### Frontend Not Updating

```bash
# Clear Vite cache and rebuild
rm -rf node_modules/.vite
pnpm install
pnpm dev
```

### SSE Connection Issues

- Check `VITE_KERNEL_URL` env var
- Verify kernel is running on :8081
- Check browser console for CORS errors
- Kernel should allow origin `http://localhost:5173`

## Deployment

### Build

```bash
pnpm build
# Output: dist/
```

### Serve Static

```bash
# Option 1: Vite preview
pnpm preview

# Option 2: Any static server
npx serve dist -p 5173

# Option 3: Nginx
# Point root to dist/, configure SPA fallback
```

### Environment Variables

For production, set `VITE_KERNEL_URL` at build time or use runtime config injection.

## Contributing

- Follow TypeScript strict mode
- Use Tailwind utility classes (no custom CSS unless necessary)
- Test with Playwright before committing
- Keep components small and focused
- Use Framer Motion for animations

## License

See parent project LICENSE.
