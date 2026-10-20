// Landing page behaviour (design "C · Hero + chart"). Loaded only by overrides/home.html.
// Draws the figure's price scenarios and committed schedule from assets/landing/data.json
// (written by tools/docs/generate_landing_data.py from a real Odys run), and wires up the
// copy button. Colours come from CSS classes in home.css, so the figure follows the theme.
(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  // Chart geometry in viewBox units (960 × 570). Inside its group, which overrides/home.html
  // shifts down by 36: the price plot. Inside its group, shifted down by 140: the schedule's
  // zero line, bars and hour labels. The template's static parts sit in the gaps: the INPUT
  // label above y = 36, the optimize step at y = 284–368 and the OUTPUT row at y = 400.
  // Changing PRICE_TOP + PRICE_HEIGHT or SCHEDULE_ZERO ± SCHEDULE_HALF_HEIGHT moves the plots
  // into those parts.
  const PLOT_LEFT = 40;
  const PLOT_WIDTH = 910;
  const PRICE_TOP = 20;
  const PRICE_HEIGHT = 200;
  const PRICE_GRID_LINES = 3;
  const PRICE_TICK_ROUNDING = 10;
  const SCHEDULE_ZERO = 330;
  const SCHEDULE_HALF_HEIGHT = 60;
  const HOUR_LABELS_Y = 414;
  const HOUR_LABELS = 4;
  const BAR_FILL = 0.64;
  // Animation timeline in seconds: the price scenarios draw in one after another, then
  // the optimize step fades in (home.css), then the schedule's bars grow hour by hour.
  const LINE_STAGGER = 0.06;
  const BARS_START = 1.9;
  const BAR_STAGGER = 0.03;
  const COPY_FEEDBACK_MS = 1600;

  function svg(tag, attrs = {}, text) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  const hourBoundary = (hour, hours) => PLOT_LEFT + (PLOT_WIDTH * hour) / hours;
  const hourCenter = (hour, hours) => hourBoundary(hour + 0.5, hours);

  function priceLines(group, scenarios) {
    const hours = scenarios[0].length;
    const prices = scenarios.flat();
    // Grid lines every tickStep from priceMin, a round number, so every tick label is round too.
    const priceMin = Math.min(0, Math.floor(Math.min(...prices) / PRICE_TICK_ROUNDING) * PRICE_TICK_ROUNDING);
    const tickStep =
      Math.max(1, Math.ceil((Math.max(...prices) - priceMin) / PRICE_GRID_LINES / PRICE_TICK_ROUNDING)) * PRICE_TICK_ROUNDING;
    const priceMax = priceMin + tickStep * PRICE_GRID_LINES;
    const y = (price) => PRICE_TOP + PRICE_HEIGHT * (1 - (price - priceMin) / (priceMax - priceMin));
    const grid = [];
    for (let i = 0; i <= PRICE_GRID_LINES; i += 1) {
      const price = priceMin + tickStep * i;
      grid.push(
        svg("line", { class: "odys-chart__grid", x1: PLOT_LEFT, y1: y(price), x2: PLOT_LEFT + PLOT_WIDTH, y2: y(price) }),
        svg("text", { class: "odys-chart__tick", x: PLOT_LEFT - 8, y: y(price) + 4, "text-anchor": "end" }, Math.round(price)),
      );
    }
    const lines = scenarios.map((scenario, i) => {
      const line = svg("path", {
        class: "odys-chart__price",
        d: scenario.map((price, hour) => `${hour ? "L" : "M"}${hourCenter(hour, hours).toFixed(1)} ${y(price).toFixed(1)}`).join(" "),
        pathLength: 1,
      });
      line.style.animationDelay = `${(i * LINE_STAGGER).toFixed(2)}s`;
      return line;
    });
    group.replaceChildren(...grid, ...lines);
  }

  // Labels hour boundaries: start, end and HOUR_LABELS - 1 evenly spaced ones between, when they fall on whole hours.
  function hourLabels(hours) {
    const spacing = hours % HOUR_LABELS === 0 ? hours / HOUR_LABELS : hours;
    const labels = [];
    for (let hour = 0; hour <= hours; hour += spacing) {
      const anchor = hour === 0 ? "start" : hour === hours ? "end" : "middle";
      labels.push(
        svg(
          "text",
          { class: "odys-chart__tick", x: hourBoundary(hour, hours), y: HOUR_LABELS_Y, "text-anchor": anchor },
          `${String(hour).padStart(2, "0")}:00`,
        ),
      );
    }
    return labels;
  }

  function scheduleBars(group, schedule) {
    const hours = schedule.length;
    const scheduleMax = Math.max(...schedule.map(Math.abs)) || 1;
    const barWidth = (PLOT_WIDTH / hours) * BAR_FILL;
    const ticks = [
      [scheduleMax, `+${Math.round(scheduleMax)}`],
      [0, "0"],
      [-scheduleMax, `−${Math.round(scheduleMax)}`],
    ].map(([volume, label]) =>
      svg("text", { class: "odys-chart__tick", x: PLOT_LEFT - 8, y: SCHEDULE_ZERO - (volume / scheduleMax) * SCHEDULE_HALF_HEIGHT + 4, "text-anchor": "end" }, label),
    );
    const bars = schedule.flatMap((volume, hour) => {
      if (volume === 0) return [];
      const height = (Math.abs(volume) / scheduleMax) * SCHEDULE_HALF_HEIGHT;
      const bar = svg("rect", {
        class: `odys-chart__bar ${volume > 0 ? "odys-chart__sell" : "odys-chart__buy"}`,
        x: (hourCenter(hour, hours) - barWidth / 2).toFixed(1),
        y: (volume > 0 ? SCHEDULE_ZERO - height : SCHEDULE_ZERO).toFixed(1),
        width: barWidth.toFixed(1),
        height: height.toFixed(1),
        rx: 2,
      });
      bar.style.animationDelay = `${(BARS_START + hour * BAR_STAGGER).toFixed(2)}s`;
      return [bar];
    });
    group.replaceChildren(
      svg("line", { class: "odys-chart__axis", x1: PLOT_LEFT, y1: SCHEDULE_ZERO, x2: PLOT_LEFT + PLOT_WIDTH, y2: SCHEDULE_ZERO }),
      ...ticks,
      ...bars,
      ...hourLabels(hours),
    );
  }

  // The figure starts hidden before data.json is fetched, so the static optimize step never
  // shows, hides and fades back in. With reduced motion it is drawn finished.
  function prepareAnimation(chart) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    chart.classList.add("odys-chart--animate");
  }

  // The figure plays once, when it scrolls into view.
  function animateOnView(chart) {
    if (!chart.classList.contains("odys-chart--animate")) return;
    if (!("IntersectionObserver" in window)) {
      chart.classList.add("odys-chart--play");
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        chart.classList.add("odys-chart--play");
        observer.disconnect();
      },
      { threshold: 0.4 },
    );
    observer.observe(chart);
  }

  function initChart(chart, hero) {
    priceLines(chart.querySelector("[data-prices]"), hero.price_scenarios);
    scheduleBars(chart.querySelector("[data-schedule]"), hero.schedule);
    animateOnView(chart);
  }

  function initCopy(root) {
    for (const button of root.querySelectorAll("[data-copy]")) {
      const state = button.querySelector("[data-copy-state]");
      let reset;
      button.addEventListener("click", async () => {
        clearTimeout(reset);
        try {
          await navigator.clipboard.writeText(button.dataset.copy);
          button.dataset.copied = "true";
          state.textContent = "Copied";
        } catch {
          button.dataset.copied = "false";
          state.textContent = "Copy failed: type pip install odys";
        }
        reset = setTimeout(() => {
          delete button.dataset.copied;
          state.textContent = "";
        }, COPY_FEEDBACK_MS);
      });
    }
  }

  async function init() {
    const root = document.querySelector(".odys-home");
    if (!root) return;
    initCopy(root);
    const chart = root.querySelector("[data-chart]");
    prepareAnimation(chart);

    let data;
    try {
      const response = await fetch(root.dataset.landingData);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      data = await response.json();
    } catch {
      // Static content stays usable; only the data-driven parts are missing.
      chart.classList.remove("odys-chart--animate");
      return;
    }
    initChart(chart, data.hero);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
