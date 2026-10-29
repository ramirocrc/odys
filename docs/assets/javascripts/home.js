// Landing page behaviour. Loaded only by overrides/home.html.
// Draws the figure (price scenarios, the optimize step and the committed schedule) from
// assets/landing/data.json (written by tools/docs/generate_landing_data.py from a real Odys
// run). Colours come from CSS classes in home.css, so the figure follows the theme.
(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  // The figure is drawn at its rendered width, one viewBox unit per CSS pixel, so its text keeps
  // the sizes home.css gives it on every screen. The schedule sits under the prices, sharing
  // their hours. Below COMPACT_WIDTH the plots are shorter and the legend moves under the
  // OUTPUT label. Positions are in viewBox units; each plot's unit sits UNIT_GAP above its top tick.
  const COMPACT_WIDTH = 600;
  const WIDE = {
    plotLeft: 40,
    plotRightMargin: 10,
    inputLabelY: 16,
    priceTop: 56,
    priceHeight: 140,
    stepTop: 244,
    stepWidth: 190,
    outputLabelY: 340,
    legendY: 340,
    scheduleZero: 448,
    scheduleHalfHeight: 60,
  };
  const COMPACT = {
    plotLeft: 30,
    plotRightMargin: 4,
    inputLabelY: 16,
    priceTop: 56,
    priceHeight: 150,
    stepTop: 230,
    stepWidth: 170,
    outputLabelY: 316,
    legendY: 342,
    scheduleZero: 429,
    scheduleHalfHeight: 45,
  };
  const STEP_HEIGHT = 34;
  const UNIT_GAP = 16;
  const PRICE_UNIT = "€/MWh";
  const SCHEDULE_UNIT = "MW";
  const LEGEND_WIDTH = 224;
  const LEGEND_ITEM_SPACING = 130;
  const HOUR_LABELS_GAP = 24;
  const BOTTOM_PADDING = 16;
  const HOUR_LABELS = 4;
  // Below this plot width, four hour intervals' labels run into each other, so only noon is labelled between the ends.
  const NARROW_PLOT_WIDTH = 280;
  const PRICE_GRID_LINES = 3;
  const PRICE_TICK_ROUNDING = 10;
  const BAR_FILL = 0.64;
  // Animation timeline in seconds: the price scenarios draw in one after another, then
  // the optimize step fades in (home.css), then the schedule's bars grow hour by hour. The
  // prices start once PLAY_THRESHOLD of the figure is in view; the bars wait until
  // SCHEDULE_VISIBLE of the schedule is, and start BARS_START after the prices, or
  // BARS_MIN_START after the schedule comes into view if the reader scrolls to it later.
  const LINE_STAGGER = 0.06;
  const BARS_START = 1.9;
  const BARS_MIN_START = 0.3;
  const BAR_STAGGER = 0.03;
  const PLAY_THRESHOLD = 0.4;
  const SCHEDULE_VISIBLE = 0.6;

  function svg(tag, attrs = {}, ...children) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
    node.append(...children);
    return node;
  }

  // A layout places every part of the figure. Each plot has its edges, the x of its unit label
  // and, when it shows them, the y of its hour labels.
  function layoutFor(width) {
    const base = width < COMPACT_WIDTH ? COMPACT : WIDE;
    const left = base.plotLeft;
    const right = width - base.plotRightMargin;
    const scheduleBottom = base.scheduleZero + base.scheduleHalfHeight;
    const hourLabelsY = scheduleBottom + HOUR_LABELS_GAP;
    return {
      width,
      height: hourLabelsY + BOTTOM_PADDING,
      input: { x: 0, y: base.inputLabelY },
      output: { x: 0, y: base.outputLabelY },
      legend: { x: width < COMPACT_WIDTH ? 0 : right - LEGEND_WIDTH, y: base.legendY },
      price: { left, right, top: base.priceTop, bottom: base.priceTop + base.priceHeight, unitX: 0, hourLabelsY: null },
      schedule: { left, right, top: base.scheduleZero - base.scheduleHalfHeight, bottom: scheduleBottom, unitX: 0, hourLabelsY },
      step: { x: left + (right - left) / 2, y: base.stepTop + STEP_HEIGHT / 2, width: base.stepWidth },
    };
  }

  const plotWidth = (plot) => plot.right - plot.left;
  const hourBoundary = (plot, hour, hours) => plot.left + (plotWidth(plot) * hour) / hours;
  const hourCenter = (plot, hour, hours) => hourBoundary(plot, hour + 0.5, hours);

  function sectionLabel({ x, y }, tag, text) {
    return svg(
      "text",
      { class: "odys-chart__label", x, y },
      svg("tspan", { class: `odys-chart__tag odys-chart__tag--${tag.toLowerCase()}` }, tag),
      svg("tspan", { dx: 10 }, text),
    );
  }

  // The optimize step between the plots: a line in, the step, and an arrow down to the schedule.
  function optimizeStep({ x, y, width }) {
    const half = width / 2;
    const top = y - STEP_HEIGHT / 2;
    const bottom = y + STEP_HEIGHT / 2;
    return svg(
      "g",
      { class: "odys-chart__optimize", "aria-hidden": "true" },
      svg("line", { class: "odys-chart__flow", x1: x, y1: top - 20, x2: x, y2: top }),
      svg("line", { class: "odys-chart__flow", x1: x, y1: bottom, x2: x, y2: bottom + 22 }),
      svg("path", { class: "odys-chart__arrowhead", d: `M${x - 6} ${bottom + 20} L${x} ${bottom + 30} L${x + 6} ${bottom + 20} Z` }),
      svg("rect", { class: "odys-chart__step", x: x - half, y: y - STEP_HEIGHT / 2, width, height: STEP_HEIGHT, rx: 8 }),
      svg("text", { class: "odys-chart__step-text", x, y: y + 5, "text-anchor": "middle" }, "system.optimize()"),
    );
  }

  function legend({ x, y }) {
    const items = [
      ["odys-chart__sell", "Sell (discharge)"],
      ["odys-chart__buy", "Buy (charge)"],
    ];
    return svg(
      "g",
      { class: "odys-chart__label" },
      ...items.flatMap(([swatch, text], i) => {
        const itemX = x + i * LEGEND_ITEM_SPACING;
        return [
          svg("rect", { class: swatch, x: itemX, y: y - 10, width: 12, height: 12, rx: 2 }),
          svg("text", { x: itemX + 18, y }, text),
        ];
      }),
    );
  }

  function unitLabel(plot, unit) {
    return svg("text", { class: "odys-chart__tick", x: plot.unitX, y: plot.top - UNIT_GAP }, unit);
  }

  // Labels hour boundaries: start, end and evenly spaced ones between, when they fall on whole hours.
  function hourLabels(plot, hours) {
    if (plot.hourLabelsY === null) return [];
    const count = plotWidth(plot) < NARROW_PLOT_WIDTH ? 2 : HOUR_LABELS;
    const spacing = hours % count === 0 ? hours / count : hours;
    const labels = [];
    for (let hour = 0; hour <= hours; hour += spacing) {
      const anchor = hour === 0 ? "start" : hour === hours ? "end" : "middle";
      labels.push(
        svg(
          "text",
          { class: "odys-chart__tick", x: hourBoundary(plot, hour, hours), y: plot.hourLabelsY, "text-anchor": anchor },
          `${String(hour).padStart(2, "0")}:00`,
        ),
      );
    }
    return labels;
  }

  function priceLines(plot, scenarios) {
    const hours = scenarios[0].length;
    const prices = scenarios.flat();
    // Grid lines every tickStep from priceMin, a round number, so every tick label is round too.
    const priceMin = Math.min(0, Math.floor(Math.min(...prices) / PRICE_TICK_ROUNDING) * PRICE_TICK_ROUNDING);
    const tickStep =
      Math.max(1, Math.ceil((Math.max(...prices) - priceMin) / PRICE_GRID_LINES / PRICE_TICK_ROUNDING)) * PRICE_TICK_ROUNDING;
    const priceMax = priceMin + tickStep * PRICE_GRID_LINES;
    const y = (price) => plot.bottom - (plot.bottom - plot.top) * ((price - priceMin) / (priceMax - priceMin));
    const grid = [];
    for (let i = 0; i <= PRICE_GRID_LINES; i += 1) {
      const price = priceMin + tickStep * i;
      grid.push(
        svg("line", { class: "odys-chart__grid", x1: plot.left, y1: y(price), x2: plot.right, y2: y(price) }),
        svg("text", { class: "odys-chart__tick", x: plot.left - 8, y: y(price) + 4, "text-anchor": "end" }, Math.round(price)),
      );
    }
    const lines = scenarios.map((scenario, i) => {
      const line = svg("path", {
        class: "odys-chart__price",
        d: scenario
          .map((price, hour) => `${hour ? "L" : "M"}${hourCenter(plot, hour, hours).toFixed(1)} ${y(price).toFixed(1)}`)
          .join(" "),
        pathLength: 1,
      });
      line.style.animationDelay = `${(i * LINE_STAGGER).toFixed(2)}s`;
      return line;
    });
    return [unitLabel(plot, PRICE_UNIT), ...grid, ...lines, ...hourLabels(plot, hours)];
  }

  function scheduleBars(plot, schedule) {
    const hours = schedule.length;
    const zero = (plot.top + plot.bottom) / 2;
    const halfHeight = (plot.bottom - plot.top) / 2;
    const scheduleMax = Math.max(...schedule.map(Math.abs)) || 1;
    const barWidth = (plotWidth(plot) / hours) * BAR_FILL;
    const ticks = [
      [scheduleMax, `+${Math.round(scheduleMax)}`],
      [0, "0"],
      [-scheduleMax, `−${Math.round(scheduleMax)}`],
    ].map(([volume, label]) =>
      svg("text", { class: "odys-chart__tick", x: plot.left - 8, y: zero - (volume / scheduleMax) * halfHeight + 4, "text-anchor": "end" }, label),
    );
    const bars = schedule.flatMap((volume, hour) => {
      if (volume === 0) return [];
      const height = (Math.abs(volume) / scheduleMax) * halfHeight;
      const bar = svg("rect", {
        class: `odys-chart__bar ${volume > 0 ? "odys-chart__sell" : "odys-chart__buy"}`,
        x: (hourCenter(plot, hour, hours) - barWidth / 2).toFixed(1),
        y: (volume > 0 ? zero - height : zero).toFixed(1),
        width: barWidth.toFixed(1),
        height: height.toFixed(1),
        rx: 2,
      });
      bar.style.animationDelay = `calc(var(--bars-start, ${BARS_START}s) + ${(hour * BAR_STAGGER).toFixed(2)}s)`;
      return [bar];
    });
    return [
      svg("rect", { class: "odys-chart__schedule-area", x: plot.left, y: plot.top, width: plotWidth(plot), height: plot.bottom - plot.top }),
      unitLabel(plot, SCHEDULE_UNIT),
      svg("line", { class: "odys-chart__axis", x1: plot.left, y1: zero, x2: plot.right, y2: zero }),
      ...ticks,
      ...bars,
      ...hourLabels(plot, hours),
    ];
  }

  function drawChart(chart, hero, width) {
    const layout = layoutFor(width);
    chart.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);
    chart.replaceChildren(
      sectionLabel(layout.input, "INPUT", "Several scenarios"),
      ...priceLines(layout.price, hero.price_scenarios),
      optimizeStep(layout.step),
      sectionLabel(layout.output, "OUTPUT", "Optimal battery schedule"),
      legend(layout.legend),
      ...scheduleBars(layout.schedule, hero.schedule),
    );
  }

  // Sizes the empty figure to the height it will be drawn at, so the page does not shift when
  // data.json arrives.
  function reserveSpace(chart) {
    const { width, height } = layoutFor(Math.round(chart.getBoundingClientRect().width));
    chart.setAttribute("viewBox", `0 0 ${width} ${height}`);
  }

  // Set before data.json is fetched, so the figure is drawn hidden and only appears when it plays.
  // With reduced motion it is drawn finished.
  function prepareAnimation(chart) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    chart.classList.add("odys-chart--animate");
  }

  const scheduleArea = (chart) => chart.querySelector(".odys-chart__schedule-area");

  // The figure plays once: the prices when it scrolls into view, the bars when the schedule
  // does. Returns the observer watching both, or null when the figure is drawn finished.
  function animateOnView(chart) {
    if (!chart.classList.contains("odys-chart--animate")) return null;
    if (!("IntersectionObserver" in window)) {
      chart.classList.add("odys-chart--play", "odys-chart--play-schedule");
      return null;
    }
    let playedAt = null;
    const play = () => {
      if (playedAt !== null) return;
      playedAt = performance.now();
      chart.classList.add("odys-chart--play");
    };
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.target === chart) {
            if (entry.intersectionRatio >= PLAY_THRESHOLD) play();
            continue;
          }
          if (entry.intersectionRatio < SCHEDULE_VISIBLE) continue;
          play();
          const elapsed = (performance.now() - playedAt) / 1000;
          chart.style.setProperty("--bars-start", `${Math.max(BARS_MIN_START, BARS_START - elapsed).toFixed(2)}s`);
          chart.classList.add("odys-chart--play-schedule");
          observer.disconnect();
          return;
        }
      },
      { threshold: [PLAY_THRESHOLD, SCHEDULE_VISIBLE] },
    );
    observer.observe(chart);
    observer.observe(scheduleArea(chart));
    return observer;
  }

  // Redraws at the new width when the figure is resized. A figure that has already started
  // playing is redrawn finished, so a resize or a phone rotation does not replay the
  // animation; one that has not yet played keeps waiting, now for the redrawn schedule.
  function redrawOnResize(chart, hero, drawnWidth, observer) {
    if (!("ResizeObserver" in window)) return;
    let width = drawnWidth;
    new ResizeObserver(() => {
      const newWidth = Math.round(chart.getBoundingClientRect().width);
      if (newWidth === width || newWidth === 0) return;
      width = newWidth;
      const started = chart.classList.contains("odys-chart--play");
      if (started) {
        observer?.disconnect();
        chart.classList.remove("odys-chart--animate", "odys-chart--play", "odys-chart--play-schedule");
      } else {
        observer?.unobserve(scheduleArea(chart));
      }
      drawChart(chart, hero, width);
      if (!started) observer?.observe(scheduleArea(chart));
    }).observe(chart);
  }

  function initChart(chart, hero) {
    const width = Math.round(chart.getBoundingClientRect().width);
    drawChart(chart, hero, width);
    redrawOnResize(chart, hero, width, animateOnView(chart));
  }

  async function init() {
    const root = document.querySelector(".odys-home");
    if (!root) return;
    const chart = root.querySelector("[data-chart]");
    prepareAnimation(chart);
    reserveSpace(chart);

    let data;
    try {
      const response = await fetch(root.dataset.landingData);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
    } catch {
      // The rest of the page stays usable; the figure section, caption included, is hidden.
      chart.closest(".odys-figure").style.display = "none";
      return;
    }
    initChart(chart, data.hero);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
