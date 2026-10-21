# Landing page

The docs home page is a custom landing page rendered by a zensical template
override. It follows design **C · Hero + chart** and its light counterpart,
**C · Hero + chart (light)**, on the prototype canvas
(<https://claude.ai/artifact/MMvA8pytifLrdhbSXf7sKM>). The layout, colours and
buttons follow vuejs.org's home page.

The page reads top to bottom: hero (title, lead, three buttons), a figure of
price scenarios going in and one schedule coming out, a "Built on" strip, and
six highlight boxes.

## Decisions

- **One site, one build.** The page is a Jinja template that overrides the
  docs layout for `docs/index.md` only, through `custom_dir = "overrides"` in
  `zensical.toml`. Zensical supports Material-style block overrides; the
  template uses the `tabs`, `site_nav`, `container`, `extrahead` and `scripts`
  blocks of `base.html`. The page goes in the `tabs` block after the tabs
  themselves (`{{ super() }}`): zensical renders the `hero` block above the
  tabs, which would push the tabs below the page.
- **Follows the light/dark toggle.** `home.css` maps a set of `--home-*`
  variables to brand colours per scheme: vuejs.org's dark theme under
  `slate`, its light theme under `default`. As on vuejs.org, the whole title
  carries the gradient in dark mode and only "every future" in light mode.
- **Zensical's header, navigation tabs and footer are kept** exactly as on
  the docs pages, so search, the theme toggle and the site sections are one
  click away.
- **Page-scoped assets.** `home.css` and `home.js` are linked from the
  template, not from `extra_css`/`extra_javascript`, so no docs page loads
  them.
- **Real data only.** The price lines and the schedule in the figure come from
  an Odys run at docs build time. Nothing is hand-drawn. The rest of the page
  is static copy with no numbers.

## How it fits together

| Piece | File |
|---|---|
| Template (all static markup and copy, the figure's labels) | `overrides/home.html` |
| Styles | `docs/assets/stylesheets/home.css` |
| Behaviour (figure lines and bars, copy button) | `docs/assets/javascripts/home.js` |
| Selects the template | `docs/index.md` (front matter only) |
| The run behind the figure | `tools/docs/landing/snippets/stochastic.py` |
| Its point-forecast baseline, used only by the tests | `tools/docs/landing/snippets/deterministic.py` |
| Data generation | `tools/docs/generate_landing_data.py` → `docs/assets/landing/data.json` (git-ignored) |
| Guard against the snippets drifting from the API or the page's claims | `tests/docs/test_landing_snippets.py` |
| Guard against `data.json` drifting from what `home.js` reads | `tests/docs/test_landing_data.py` |

`just docs` and `just docs-build` regenerate `data.json` through the
`docs-assets` recipe before building.

### The figure

`stochastic.py` runs a battery that bids once on a stage-fixed day-ahead
market against twelve price scenarios, built from a typical day-ahead price
shape with varied solar dip and evening peak, rounded to whole €/MWh. The
figure draws every scenario as a faint line (the input), then the one schedule
Odys commits to as bars (the output), sell above the axis and buy below. The
hours line up vertically, so the battery is seen selling into the price peaks.

The figure's copy names neither the number of scenarios nor the battery's
size ("Several scenarios", "A battery bids on the day-ahead market"): the
point is one schedule for every scenario.

`tests/docs/test_landing_snippets.py` checks that the snippet commits to one
schedule in every scenario, and that it beats optimizing against the single
forecast in `deterministic.py`, one of the twelve scenarios.

### Data in `data.json`

- `hero.price_scenarios`: the scenarios' hourly prices in €/MWh
- `hero.schedule`: the committed market position per hour in MW, sell positive

## Editing the page

- **Copy, buttons, highlight boxes:** edit `overrides/home.html`.
- **Figure labels:** the static `<text>` elements in the figure's `<svg>` in
  `overrides/home.html`. The axis ticks and hour labels follow the data and
  are drawn by `home.js`, whose geometry constants (top of the file) say which
  template positions depend on them.
- **Figure animation:** plays once when the figure scrolls into view: the price
  lines draw in, the optimize step fades in, then the bars grow hour by hour.
  The delays are constants at the top of `home.js`, the durations are in
  `home.css`. With reduced motion the figure is drawn finished.
- **Figure data:** edit the snippet, then run `just docs-assets` and
  `just test`.
- **Breakpoints:** vuejs.org's: 960px and 794px (smaller title) and 576px
  (phone layout). The highlight boxes wrap on their own (`auto-fit`, 240px
  minimum).

## Brand

`tools/docs/brand/tokens.json` is the single source of truth for Odys colours and
fonts. To change a colour, edit it there and run `just docs-assets`. Never
hard-code a colour elsewhere; `tests/docs/test_brand.py` fails on hex
or `rgb()` values in the landing files.

| Tokens | Read by | Used for |
|---|---|---|
| `color` | `tools/docs/generate_brand.py`, which writes `brand.css` (git-ignored) | Every colour becomes `--odys-<name>`. `home.css` uses these variables. |
| `scheme.light`, `scheme.dark` | `generate_brand.py` | Maps zensical's `--md-*` theme variables, so the docs follow the brand in both modes. |
| `font` | `generate_brand.py` | The Google Fonts import plus `--odys-font-*` and `--md-text-font` / `--md-code-font`. `ui` (Inter) is vuejs.org's font, used for the landing page's buttons and figure labels. |
| `chart.roles`, `chart.chrome` | `tools/docs/generate_example_plots.py` | The example charts: a light and a dark value for every series role (solar, thermal, battery, …) and for text, gridlines, axes and background. |

The colour scheme follows vuejs.org's light and dark themes, on the docs
pages and the landing page alike: the `gray-*`, `green-*`, `blue-400` and
`indigo-*` colours are Vue's. Vue's translucent text and divider colours are
flattened onto its backgrounds, so every token stays an opaque hex value; the
light muted grey (`gray-500`) is a shade darker than Vue's so it reaches 4.5:1
on white. Links stay the brand violet. The accent is Vue's green in the dark
scheme and the brand's darker `mint-700` in the light one, where Vue's green
falls short of 4.5:1 on white. `bg`, `text`, `mint-400` and `mint-700` are
the logo's colours (`tools/docs/generate_logo.py`).

Chart colours follow energy conventions where they exist: solar is gold and
thermal units are terracotta. Storage takes the brand violet, money (prices)
the brand mint, and load is a dashed ink line. Each role reaches 3:1 on its
scheme's background, apart from roles marked `fill`, which are only used for
areas. One light value always maps to one dark value.

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
  about 900px and phone widths, in light, dark and system mode. The page and
  its figure should follow the toggle; the header and tabs should look as on
  the docs pages.
- The figure shows twelve price lines and the schedule's bars. The copy
  button copies `pip install odys`. The highlight boxes drop to one column on
  phones.
- Spot-check docs pages (user guide, API reference) for unchanged styling.
- `just docs-build` (strict), `just test` and `just check` pass.
