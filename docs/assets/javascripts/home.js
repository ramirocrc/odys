// Landing page behaviour (design "G · Orbit"). Loaded only by overrides/home.html.
// Renders the hero chart and code, the CVaR card and the example thumbnails from
// assets/landing/data.json (written by tools/docs/generate_landing_data.py from real Odys
// runs), and wires up the tabs, code folds, copy button and examples carousel.
(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  // Brand colours come from brand.css (generated from tools/docs/brand/tokens.json).
  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(`--odys-${name}`).trim();
  const TONES = {};
  const TAB_TAGS = {
    deterministic: "1 scenario",
    stochastic: "12 scenarios",
  };
  const FOLD_LABELS = {
    setup: "battery = StationaryStorage(…)  market = EnergyMarket(…)",
    forecast: "forecast = […]",
    price_scenarios: "price_scenarios = [[…], …]",
  };
  const KEYWORDS = new Set(["for", "in", "import", "from", "return", "None", "True", "False"]);
  const TOKEN_RE = /("[^"]*")|(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z0-9_]*)(=(?!=))?|(\s+)|(.)/g;

  function svg(tag, attrs = {}, text) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function span(className, text) {
    const node = document.createElement("span");
    if (className) node.className = className;
    node.textContent = text;
    return node;
  }

  function linePath(values, x0, width, y0, height, max) {
    const step = width / (values.length - 1);
    return values
      .map((v, i) => `${i ? "L" : "M"}${(x0 + i * step).toFixed(1)},${(y0 + height - (v / max) * height).toFixed(1)}`)
      .join(" ");
  }

  function euros(value) {
    return `€${Math.round(value / 1000)}k`;
  }

  function exactEuros(value) {
    return `€${Math.round(value).toLocaleString("en-US")}`;
  }

  // ---- Code panel ----

  function highlight(line) {
    const fragment = document.createDocumentFragment();
    if (!line) {
      fragment.append(" ");
      return fragment;
    }
    if (line.trimStart().startsWith("#")) {
      fragment.append(span("tk-cm", line));
      return fragment;
    }
    for (const m of line.matchAll(TOKEN_RE)) {
      if (m[1]) fragment.append(span("tk-s", m[1]));
      else if (m[2]) fragment.append(span("tk-n", m[2]));
      else if (m[3] && m[4]) fragment.append(span("tk-k", m[3]), span("tk-p", "="));
      else if (m[3] && KEYWORDS.has(m[3])) fragment.append(span("tk-kw", m[3]));
      else if (m[3] && /^[A-Z]/.test(m[3])) fragment.append(span("tk-c", m[3]));
      else if (m[3]) fragment.append(span("tk-v", m[3]));
      else if (m[5]) fragment.append(m[5]);
      else fragment.append(span("tk-p", m[6]));
    }
    return fragment;
  }

  // Every tab's code is rendered into one grid cell, and the inactive tabs are only made invisible,
  // so the panel always takes the height of the tallest tab and switching tabs never resizes it.
  function renderCode(container, current, tabs, openFolds, rerender) {
    container.replaceChildren(
      ...Object.entries(tabs).map(([tab, tabData]) => {
        const panel = document.createElement("div");
        panel.className = tab === current ? "odys-code__panel" : "odys-code__panel odys-code__panel--inactive";
        panel.append(...codeRows(tab, tabData, openFolds, rerender));
        return panel;
      }),
    );
  }

  function codeRows(tab, tabData, openFolds, rerender) {
    const marker = tab === "deterministic" ? "›" : "+";
    const changed = new Set(tabData.changed);
    const foldsByStart = new Map(tabData.folds.map((fold) => [fold.start, fold]));
    const rows = [];
    for (let i = 0; i < tabData.code.length; i += 1) {
      const fold = foldsByStart.get(i);
      if (fold) {
        const open = openFolds[fold.kind];
        const button = document.createElement("button");
        button.type = "button";
        button.className = "odys-fold";
        button.setAttribute("aria-expanded", String(open));
        button.append(
          span("odys-gutter", open ? "" : `${fold.start + 1}–${fold.end}`),
          span("odys-marker", open ? "▾" : "▸"),
          span(open ? "tk-kw" : "tk-p", open ? "hide" : FOLD_LABELS[fold.kind]),
        );
        const lineCount = fold.end - fold.start;
        if (!open) button.append(span("odys-fold__meta", `${lineCount} line${lineCount === 1 ? "" : "s"} · show`));
        button.addEventListener("click", () => {
          openFolds[fold.kind] = !open;
          rerender();
        });
        rows.push(button);
        if (!open) {
          i = fold.end - 1;
          continue;
        }
      }
      const row = document.createElement("div");
      const isChanged = changed.has(i);
      row.className = `odys-ln ${isChanged ? "odys-ln--changed" : "odys-ln--dim"}`;
      row.append(span("odys-gutter", String(i + 1)), span("odys-marker", isChanged ? marker : ""), highlight(tabData.code[i]));
      rows.push(row);
    }
    return rows;
  }

  // ---- Hero chart ----

  function renderChart(chart, hero, tab) {
    const tabData = hero.tabs[tab];
    const lines = tab === "deterministic" ? [hero.forecast] : hero.price_scenarios;
    const priceMax = Math.ceil(Math.max(...hero.price_scenarios.flat()) / 10) * 10;
    const scheduleMax = Math.max(...Object.values(hero.tabs).flatMap((t) => t.schedule.map(Math.abs)));
    const barScale = 78 / scheduleMax;
    const barWidth = 600 / tabData.schedule.length;
    const barDelay = tab === "deterministic" ? 1.2 : 1.9;

    const fan = svg("g", { class: "fan" });
    lines.forEach((values, i) => {
      const path = svg("path", { d: linePath(values, 0, 600, 40, 250, priceMax) });
      if (tab === "deterministic") path.classList.add("forecast");
      path.style.animationDelay = `${(i * 0.08).toFixed(2)}s`;
      fan.append(path);
    });

    const bars = tabData.schedule.map((value, i) => {
      const height = Math.max(Math.abs(value) * barScale, 0.8);
      const bar = svg("rect", {
        class: `bar ${value >= 0 ? "bar--up" : "bar--down"}`,
        x: (i * barWidth + 3).toFixed(1),
        y: (value >= 0 ? 440 - height : 440).toFixed(1),
        width: (barWidth - 6).toFixed(1),
        height: height.toFixed(1),
        rx: 2,
      });
      bar.style.animationDelay = `${(barDelay + i * 0.035).toFixed(2)}s`;
      return bar;
    });

    const legend = svg("text", { x: 600, y: 340, "text-anchor": "end", class: "label" });
    legend.append(svg("tspan", { fill: TONES.accent }, "▲ discharge"), "  ", svg("tspan", { fill: token("violet-300") }, "▼ charge"));

    chart.replaceChildren(
      svg("text", { x: 0, y: 18, class: "label-strong" }, tab === "deterministic" ? "Input · 1 price forecast" : "Input · 12 price scenarios"),
      svg("text", { x: 600, y: 18, "text-anchor": "end", class: "label" }, "€/MWh"),
      fan,
      svg("text", { x: 0, y: 340, class: "label-strong" }, "Output · 1 battery schedule"),
      legend,
      svg("line", { x1: 0, y1: 440, x2: 600, y2: 440, class: "axis" }),
      ...bars,
      svg("text", { x: 0, y: 552, class: "label" }, "00:00"),
      svg("text", { x: 300, y: 552, "text-anchor": "middle", class: "label" }, "12:00"),
      svg("text", { x: 600, y: 552, "text-anchor": "end", class: "label" }, "24:00"),
    );
  }

  // Expected profit of the tab's schedule, compared scenario by scenario with the other tab's.
  function renderOutcome(value, verdict, hero, tab) {
    const other = tab === "deterministic" ? "stochastic" : "deterministic";
    const mine = hero.tabs[tab];
    const theirs = hero.tabs[other];
    const ahead = mine.scenario_profits.filter((profit, i) => profit > theirs.scenario_profits[i]).length;
    const total = mine.scenario_profits.length;
    const gap = mine.expected_profit - theirs.expected_profit;
    value.textContent = exactEuros(mine.expected_profit);
    verdict.textContent =
      gap >= 0
        ? `+${exactEuros(gap)} vs ${other}, and ahead in ${ahead} of ${total} scenarios.`
        : `${exactEuros(-gap)} less than ${other}, and ahead in only ${ahead} of ${total} scenarios.`;
    verdict.classList.toggle("odys-outcome__verdict--ahead", gap >= 0);
  }

  function initHero(root, hero) {
    const tabs = [...root.querySelectorAll("[data-tab]")];
    const code = root.querySelector("[data-code]");
    const chart = root.querySelector("[data-chart]");
    const tag = root.querySelector("[data-tab-tag]");
    const kicker = root.querySelector("[data-caption-kicker]");
    const lead = root.querySelector("[data-caption-lead]");
    const rest = root.querySelector("[data-caption-rest]");
    const outcomeValue = root.querySelector("[data-outcome-value]");
    const outcomeVerdict = root.querySelector("[data-outcome-verdict]");
    const openFolds = { setup: false, forecast: false, price_scenarios: false };
    let current = tabs.find((t) => t.getAttribute("aria-selected") === "true")?.dataset.tab ?? "stochastic";

    const renderCurrentCode = () => renderCode(code, current, hero.tabs, openFolds, renderCurrentCode);
    // Invisible copies of every caption share the live caption's grid cell, so it keeps the tallest one's height.
    const caption = lead.closest(".odys-caption");
    for (const button of tabs) {
      const sizer = document.createElement("div");
      sizer.className = "odys-caption__text odys-caption__text--sizer";
      sizer.setAttribute("aria-hidden", "true");
      sizer.append(
        span("odys-caption__kicker", button.dataset.kicker),
        span("odys-caption__lead", button.dataset.lead),
        span("odys-caption__rest", button.dataset.rest),
      );
      caption.append(sizer);
    }
    const select = (tab) => {
      current = tab;
      for (const button of tabs) button.setAttribute("aria-selected", String(button.dataset.tab === tab));
      const active = tabs.find((t) => t.dataset.tab === tab);
      kicker.textContent = active.dataset.kicker;
      lead.textContent = active.dataset.lead;
      rest.textContent = active.dataset.rest;
      tag.textContent = TAB_TAGS[tab];
      renderCurrentCode();
      renderChart(chart, hero, tab);
      renderOutcome(outcomeValue, outcomeVerdict, hero, tab);
    };
    for (const button of tabs) button.addEventListener("click", () => select(button.dataset.tab));
    select(current);
  }

  // ---- Proof cards ----

  function renderFrontier(chart, legend, points) {
    const tones = [TONES.primary, TONES.accent];
    const names = ["No CVaR term", "With CVaR term"];
    const xs = points.map((p) => p.worst);
    const ys = points.map((p) => p.expected);
    const pad = (lo, hi) => [lo - (hi - lo) * 0.2, hi + (hi - lo) * 0.2];
    const [x0, x1] = pad(Math.min(...xs), Math.max(...xs));
    const [y0, y1] = pad(Math.min(...ys), Math.max(...ys));
    const px = (v) => 34 + ((v - x0) / (x1 - x0)) * 256;
    const py = (v) => 140 - ((v - y0) / (y1 - y0)) * 118;
    const coords = points.map((p) => ({ x: px(p.worst), y: py(p.expected) }));
    chart.replaceChildren(
      svg("line", { x1: 34, y1: 140, x2: 290, y2: 140, class: "axis" }),
      svg("line", { x1: 34, y1: 14, x2: 34, y2: 140, class: "axis" }),
      svg("line", {
        x1: coords[0].x,
        y1: coords[0].y,
        x2: coords[1].x,
        y2: coords[1].y,
        stroke: TONES.muted,
        "stroke-width": 2,
        "stroke-dasharray": "5 5",
      }),
      ...coords.map((c, i) => svg("circle", { cx: c.x, cy: c.y, r: 8, fill: tones[i] })),
      svg("text", { x: 290, y: 166, "text-anchor": "end", class: "label" }, "worst-case profit →"),
      svg("text", { x: 0, y: 10, class: "label" }, "E[profit] ↑"),
    );
    legend.replaceChildren(
      ...points.map((p, i) => {
        const item = document.createElement("li");
        const swatch = span("odys-legend__swatch", "");
        swatch.style.background = tones[i];
        item.append(
          swatch,
          span("odys-legend__name", names[i]),
          span("odys-legend__values", `expected ${euros(p.expected)} · worst ${euros(p.worst)}`),
        );
        return item;
      }),
    );
  }

  // ---- Example thumbnails ----

  function renderThumb(thumb, example) {
    const nodes = [];
    const lines = example.lines ?? [];
    const bars = example.bars ?? [];
    if (lines.length) {
      const max = Math.max(...lines.flatMap((l) => l.values), 1);
      const [top, height] = bars.length ? [12, 80] : [14, 120];
      for (const line of lines) {
        nodes.push(svg("path", { d: linePath(line.values, 8, 284, top, height, max), stroke: TONES[line.tone] }));
      }
    }
    if (bars.length) {
      const maxAbs = Math.max(...bars.map(Math.abs), 1);
      const hasNegative = bars.some((v) => v < 0);
      const base = hasNegative ? 118 : 140;
      const scale = (hasNegative ? 26 : 40) / maxAbs;
      const width = 284 / bars.length;
      bars.forEach((value, i) => {
        const height = Math.max(Math.abs(value) * scale, 0.5);
        nodes.push(
          svg("rect", {
            x: (8 + i * width + 1).toFixed(1),
            y: (value >= 0 ? base - height : base).toFixed(1),
            width: (width - 2).toFixed(1),
            height: height.toFixed(1),
            fill: value >= 0 ? TONES.accent : TONES.primary,
            rx: 1.5,
          }),
        );
      });
    }
    if (example.ranges) {
      const values = example.ranges.flatMap((r) => [r.worst, r.expected]);
      const lo = Math.min(...values) * 0.9;
      const hi = Math.max(...values) * 1.05;
      const py = (v) => 130 - ((v - lo) / (hi - lo)) * 110;
      example.ranges.forEach((range, i) => {
        const x = 100 + i * 100;
        const tone = i === 0 ? TONES.primary : TONES.accent;
        nodes.push(
          svg("line", { x1: x, y1: py(range.worst), x2: x, y2: py(range.expected), stroke: tone, "stroke-width": 10, "stroke-linecap": "round" }),
          svg("circle", { cx: x, cy: py(range.expected), r: 7, fill: tone }),
        );
      });
    }
    thumb.replaceChildren(...nodes);
  }

  // ---- Copy button ----

  function initCopy(root) {
    for (const button of root.querySelectorAll("[data-copy]")) {
      const state = button.querySelector("[data-copy-state]");
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(button.dataset.copy);
          button.dataset.copied = "true";
          state.textContent = "Copied";
        } catch {
          button.dataset.copied = "false";
          state.textContent = "Press ⌘C to copy";
        }
        setTimeout(() => {
          delete button.dataset.copied;
          state.textContent = "";
        }, 1600);
      });
    }
  }

  // ---- Examples carousel ----

  function initCarousel(root) {
    const track = root.querySelector("[data-carousel]");
    const prev = root.querySelector("[data-carousel-prev]");
    const next = root.querySelector("[data-carousel-next]");
    const range = root.querySelector("[data-carousel-range]");
    const dots = root.querySelector("[data-carousel-dots]");
    const cards = [...track.children];
    const gap = () => parseFloat(getComputedStyle(track).columnGap) || 0;
    const step = () => cards[0].getBoundingClientRect().width + gap();
    const visible = () => Math.max(1, Math.round((track.clientWidth + gap()) / step()));
    const positions = () => cards.length - visible() + 1;
    const index = () => Math.min(positions() - 1, Math.round(track.scrollLeft / step()));
    let update = () => {};
    const goTo = (i) => {
      track.scrollTo({ left: i * step() });
      setTimeout(update, 450); // In case no scroll event follows (e.g. already at the edge).
    };

    let dotCount = 0;
    update = () => {
      const count = positions();
      if (count !== dotCount) {
        dotCount = count;
        dots.replaceChildren(
          ...Array.from({ length: count }, (_, i) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = "odys-dot";
            dot.setAttribute("aria-label", `Show examples ${i + 1} to ${i + visible()}`);
            dot.append(document.createElement("span"));
            dot.addEventListener("click", () => goTo(i));
            return dot;
          }),
        );
      }
      const i = index();
      range.textContent = `${i + 1}–${Math.min(i + visible(), cards.length)} of ${cards.length}`;
      prev.disabled = i === 0;
      next.disabled = i >= count - 1;
      [...dots.children].forEach((dot, d) => dot.setAttribute("aria-current", String(d === i)));
    };

    prev.addEventListener("click", () => goTo(index() - 1));
    next.addEventListener("click", () => goTo(index() + 1));
    track.addEventListener("scroll", update, { passive: true });
    track.addEventListener("scrollend", update);
    window.addEventListener("resize", update);
    update();
  }

  // ---- Boot ----

  async function init() {
    const root = document.querySelector(".odys-home");
    if (!root) return;
    Object.assign(TONES, { primary: token("violet-400"), accent: token("mint-400"), muted: token("muted-deep") });
    initCopy(root);
    initCarousel(root);

    let data;
    try {
      const response = await fetch(root.dataset.landingData);
      data = await response.json();
    } catch {
      return; // Static content stays usable; only the data-driven parts are missing.
    }
    initHero(root, data.hero);
    renderFrontier(root.querySelector("[data-frontier]"), root.querySelector("[data-frontier-legend]"), data.cvar_frontier);
    root.querySelector("[data-validation-error]").textContent = data.validation_error;
    root.querySelector("[data-pandas-output]").textContent = data.pandas_output;
    for (const thumb of root.querySelectorAll("[data-thumb]")) {
      const example = data.examples[thumb.dataset.thumb];
      if (example) renderThumb(thumb, example);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
