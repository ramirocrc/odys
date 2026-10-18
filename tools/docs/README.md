# Landing page

The docs home page is a custom landing page rendered by a zensical template
override. Its hero comes from design **G · Orbit**
(<https://claude.ai/artifact/46TRjeDJLGnbeJPeFtNwmn>, board "G · Orbit";
the "G · Mobile" board shows the phone layout). The sections below it use the
cards and section labels of board "A · Orbit (refined current)" on the
prototype canvas (<https://claude.ai/artifact/ALu2XjJhQg6iJmRFTJYh99>).

The page reads top to bottom: hero and "Built on" strip, planning problems
(one card per example), formulation and tooling, assets and markets, and a
closing call to action into the User Guide.

## Decisions

- **One site, one build.** The page is a Jinja template that overrides the
  docs layout for `docs/index.md` only, through `custom_dir = "overrides"` in
  `zensical.toml`. Zensical supports Material-style block overrides; the
  template uses the `hero`, `tabs`, `site_nav`, `container`, `extrahead` and
  `scripts` blocks of `base.html`.
- **Always dark.** The landing page uses its own fixed `--odys-*` colour
  tokens and ignores the light/dark toggle. Docs pages still follow it.
- **Zensical header and footer are kept**, restyled on the home page only, so
  search and the theme toggle still work.
- **Page-scoped assets.** `home.css` and `home.js` are linked from the
  template, not from `extra_css`/`extra_javascript`, so no docs page loads
  them.
- **Real data only.** Every number and chart in the hero comes from an Odys
  run at docs build time. Nothing is hand-drawn. The sections below the hero
  are static copy with no numbers.

## How it fits together

| Piece | File |
|---|---|
| Template (all static markup and copy) | `overrides/home.html` |
| Styles | `docs/assets/stylesheets/home.css` |
| Behaviour (hero tabs, code folds, chart, copy button) | `docs/assets/javascripts/home.js` |
| Selects the template | `docs/index.md` (front matter only) |
| Hero code snippets, run as written | `tools/docs/landing/snippets/{deterministic,stochastic}.py` |
| Data generation | `tools/docs/generate_landing_data.py` → `docs/assets/landing/data.json` (git-ignored) |
| Guard against the snippets drifting from the API | `tests/docs/test_landing_snippets.py` |

`just docs` and `just docs-build` regenerate `data.json` through the
`docs-assets` recipe before building.

### The hero snippets

Each snippet is a complete script. The landing page shows only the part
between the `# --8<-- [start:shown]` and `# --8<-- [end:shown]` markers. The
generator runs the snippets, diffs them to find the highlighted lines, and
computes the fold ranges. The setup fold covers the asset definitions, up to
the first commented block. The price data (`forecast`, `price_scenarios`) is
folded too.

Each snippet reads top to bottom: assets, then the price data, then
`scenarios` as their own variables, each under a one-line comment saying what
it is, then an `EnergySystem(...)` call that is the same in both tabs. The
highlight then lands on the blocks that make the tab different, not on lines
nested inside the system call.

The price data is written out in each snippet, so the code runs exactly as
shown: twelve price scenarios built from a typical day-ahead price shape with
varied solar dip and evening peak, rounded to whole €/MWh. The landing page
calls them scenarios, never days.

The hero keeps one height across tabs. `home.js` renders every tab's code
into one grid cell, and invisible copies of every caption sit in the
caption's cell; the inactive ones get `visibility: hidden`, so each cell
takes the height of its tallest tab at any width and with any folds open.

The deterministic tab optimizes against a single point forecast: one
plausible scenario, `forecast` in `deterministic.py`, which the snippet tests
check is one of the twelve scenarios. It must not be the scenario mean or
median. Expected profit is linear in prices and the market is
stage-fixed, so optimizing against the mean reproduces the stochastic
schedule exactly, and the two tabs would look identical. The snippet test
checks that the stochastic schedule differs from the deterministic one and
earns more in expectation.

The hero copy names neither the asset nor the number of scenarios: the
caption says "multiple price scenarios" and the chart's output label says
"1 schedule", because the point is one schedule for every scenario, for any
asset.

Snippets are formatted by ruff with magic trailing commas. Keep outer calls
exploded (one argument per line, trailing comma), and keep short inner calls
such as `PriceProfile(...)` on one line, so lines stay under about 70
characters and fit the page. The folded price rows are the exception: one
scenario per line, under the 120-character limit.

### Data in `data.json`

- `hero`: price scenarios, the point forecast and, per tab, the shown code,
  changed lines, folds and committed schedule

## Editing the page

- **Copy, planning-problem cards, feature cards, assets list:** edit
  `overrides/home.html`. Each problem card links to `examples/<slug>/`; its
  tag colour is a `odys-problem__tag--<tone>` modifier in `home.css`.
- **Hero captions:** the `data-lead` / `data-rest` attributes on the tab
  buttons in `overrides/home.html`.
- **Hero code:** edit the snippet files, then run `just docs-assets` and
  `just test`.
- **Breakpoints:** 1060px (code and chart stack), 760px (phone layout). The
  card grids wrap on their own (`auto-fit`, 340px minimum).

## Brand

`tools/docs/brand/tokens.json` is the single source of truth for Odys colours and
fonts. To change a colour, edit it there and run `just docs-assets`. Never
hard-code a colour elsewhere; `tests/docs/test_brand.py` fails on hex
or `rgb()` values in the landing files.

| Tokens | Read by | Used for |
|---|---|---|
| `color` | `tools/docs/generate_brand.py`, which writes `brand.css` (git-ignored) | Every colour becomes `--odys-<name>`. `home.css` uses these variables, and `home.js` reads them at runtime. |
| `scheme.light`, `scheme.dark` | `generate_brand.py` | Maps zensical's `--md-*` theme variables, so the docs follow the brand in both modes. |
| `font` | `generate_brand.py` | The Google Fonts import plus `--odys-font-*` and `--md-text-font` / `--md-code-font`. |
| `chart.roles`, `chart.chrome` | `tools/docs/generate_example_plots.py` | The example charts: a light and a dark value for every series role (solar, thermal, battery, …) and for text, gridlines, axes and background. |

Chart colours follow energy conventions where they exist: solar is gold and
thermal units are terracotta. Storage takes the brand violet, money (prices)
the brand mint, and load is a dashed ink line. Each role reaches 3:1 on its
scheme's background, apart from roles marked `fill`, which are only used for
areas. One light value always maps to one dark value.

The landing page's planning-problem tags reuse the same hues: `thermal-400`,
`solar-400`, `flex-400` and `ev-400` in `color` are the dark values of the
`thermal`, `solar`, `flexible_load` and `ev_2` chart roles. Change them together.

The charts are drawn with the light colours on a transparent background.
`_save_figure` derives the dark figure by swapping each light colour for its
dark counterpart and writes both into the chart page. A small script picks
one from the embedding docs page's `data-md-color-scheme`, and follows the
operating system's setting when the chart is opened on its own. It re-renders
when the reader toggles the scheme. The chart page declares
`color-scheme: light dark`; without it, the browser paints a white box behind
the iframe in dark mode.

## Verification

- `just docs-assets`, then `just docs`: check the landing page at desktop,
  about 900px and phone widths, in light, dark and system mode. The home page
  should stay dark; docs pages should follow the toggle.
- Switching tabs replays the chart and swaps the code without changing the
  window's height. Folds open and close. The card grids drop to one column
  on phones, and every card links to its page.
- Spot-check docs pages (user guide, API reference) for unchanged styling.
- `just docs-build` (strict), `just test` and `just check` pass.
