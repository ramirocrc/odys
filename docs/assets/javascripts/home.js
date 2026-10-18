// Landing page behaviour (design "G · Orbit"). Loaded only by overrides/home.html.
// Renders the hero chart and code from assets/landing/data.json (written by
// tools/docs/generate_landing_data.py from real Odys runs), and wires up the tabs,
// code folds and copy button.
(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  // Brand colours come from brand.css (generated from tools/docs/brand/tokens.json).
  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(`--odys-${name}`).trim();
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
    legend.append(svg("tspan", { fill: token("mint-400") }, "▲ discharge"), "  ", svg("tspan", { fill: token("violet-300") }, "▼ charge"));

    chart.replaceChildren(
      svg("text", { x: 0, y: 18, class: "label-strong" }, tab === "deterministic" ? "Input · 1 price forecast" : "Input · 12 price scenarios"),
      svg("text", { x: 600, y: 18, "text-anchor": "end", class: "label" }, "€/MWh"),
      fan,
      svg("text", { x: 0, y: 340, class: "label-strong" }, "Output · 1 schedule"),
      legend,
      svg("line", { x1: 0, y1: 440, x2: 600, y2: 440, class: "axis" }),
      ...bars,
      svg("text", { x: 0, y: 552, class: "label" }, "00:00"),
      svg("text", { x: 300, y: 552, "text-anchor": "middle", class: "label" }, "12:00"),
      svg("text", { x: 600, y: 552, "text-anchor": "end", class: "label" }, "24:00"),
    );
  }

  function initHero(root, hero) {
    const tabs = [...root.querySelectorAll("[data-tab]")];
    const code = root.querySelector("[data-code]");
    const chart = root.querySelector("[data-chart]");
    const tag = root.querySelector("[data-tab-tag]");
    const kicker = root.querySelector("[data-caption-kicker]");
    const lead = root.querySelector("[data-caption-lead]");
    const rest = root.querySelector("[data-caption-rest]");
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
    };
    for (const button of tabs) button.addEventListener("click", () => select(button.dataset.tab));
    select(current);
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

  // ---- Boot ----

  async function init() {
    const root = document.querySelector(".odys-home");
    if (!root) return;
    initCopy(root);

    let data;
    try {
      const response = await fetch(root.dataset.landingData);
      data = await response.json();
    } catch {
      return; // Static content stays usable; only the data-driven parts are missing.
    }
    initHero(root, data.hero);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
