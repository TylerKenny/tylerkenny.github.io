# tylerkenny.github.io

Plain HTML + one Python script. No dependencies, no build tool to install.

## Writing

1. Add `content/posts/YYYY-MM-DD-your-slug.html`:

   ```
   ---
   title: Post title
   date: 2026-08-27
   summary: Optional. Used in the listing and the feed; otherwise the first ~280 characters of body text.
   ---

   <p>Body is raw HTML. No markdown parser here on purpose — nothing to learn,
   nothing to break.</p>
   ```

   The filename slug becomes the URL (`/posts/your-slug/`), so keep it lowercase-hyphenated.
   The `date` in the header is what sorts the listing; the filename prefix is just convention.

2. `python3 build.py`

3. `git add -A && git commit && git push`

Preview locally: `python3 -m http.server 8000` then open <http://localhost:8000>.

## Layout

| path | role |
| --- | --- |
| `site.toml` | title, description, author, `base_url` |
| `content/posts/` | one file per post |
| `templates/page.html` | the single layout every page uses |
| `templates/style.css` | copied to `style.css` at the root |
| `images/` | static assets, referenced with absolute paths (`/images/foo.png`) |
| `build.py` | the generator |

Everything else at the repo root is **generated** — commit it (GitHub Pages serves it
straight out of the branch), but never edit it by hand. `build.py` deletes and rewrites
it on every run, including anything the old Hugo build left behind.

## What build.py does

Reads `site.toml`, sorts posts newest-first, then writes `index.html`, one
`posts/<slug>/index.html` per post, `404.html`, `index.xml` (RSS) and `sitemap.xml`.
That's all. Post bodies are inserted verbatim; only titles, dates and excerpts are
escaped.

## Theming

`templates/style.css` is hand-written, Everforest Dark Hard:

| token | hex | | token | hex |
| --- | --- | --- | --- | --- |
| `bg0-hard` | `#1d2021` | page | `fg` | `#d3c6aa` |
| `bg0` | `#272e33` | code blocks | `fg-dim` | `#9da9a0` |
| `bg1` | `#343f44` | rules | `green` | `#83c092` |
| `blue` | `#7fbbb3` | links | `aqua` | `#8ec07c` |

All in one file, all as CSS custom properties at the top. Fonts are the system
monospace stack — no webfonts shipped.
