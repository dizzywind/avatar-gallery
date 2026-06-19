# Apollo Avatar Gallery

A responsive, theme-filterable gallery showcasing 25 AI-generated avatars across 5 themes.

## Features

- **Responsive Grid Layout** — CSS Grid with `auto-fill/minmax` for fluid responsiveness
- **Theme Filtering** — Filter by Fantasy, Sci-Fi, Nature, Abstract, Mythology (or show All)
- **Lightbox Preview** — Click any avatar for a full-size view with navigation
- **Keyboard Accessible** — Full keyboard navigation (Tab, Enter, Escape, Arrow keys)
- **Touch Support** — Swipe navigation in lightbox on mobile
- **Dark/Light Mode** — Automatic via `prefers-color-scheme`
- **Reduced Motion** — Respects `prefers-reduced-motion`
- **Zero Dependencies** — Pure HTML/CSS/JS, no build step required

## Themes

| Theme | Count | Description |
|-------|-------|-------------|
| Fantasy | 5 | Mystical dragons, elven queens, arcane portals, storm wizards, phoenixes |
| Sci-Fi | 5 | Cyberpunk cities, astronauts, chrome robots, generation ships, alien worlds |
| Nature | 5 | Mountain lakes, wildflower fields, ancient oaks, coral reefs, wolves & auroras |
| Abstract | 5 | Fluid marble, sacred geometry, glitch art, pastel gradients, fractal galaxies |
| Mythology | 5 | Divine figures, Eye of Providence, Yggdrasil, Egyptian ankh, cosmic lotus |

## Deployment

This site is deployed on **GitHub Pages** at:
`https://dizzywind.github.io/avatar-gallery/`

To deploy your own:
1. Fork or clone this repository
2. Enable GitHub Pages in Settings → Pages → Deploy from branch → `main` / `root`
3. Your gallery will be live at `https://<your-username>.github.io/avatar-gallery/`

## Local Development

Simply open `index.html` in a browser, or serve with any static server:

```bash
# Python 3
python -m http.server 8000

# Node.js (npx)
npx serve

# PHP
php -S localhost:8000
```

## Attribution

Images generated via [Pollinations.ai](https://pollinations.ai) (Flux model) — free AI image generation API.

## License

MIT License — feel free to use, modify, and distribute.