// Dashboard: Chart.js visualisations of the stored analysis + filters + delete.
(function () {
  "use strict";
  const css = getComputedStyle(document.documentElement);
  const token = (n) => css.getPropertyValue(n).trim();
  const SERIES = token("--series-1") || "#2a78d6";
  const TEXT2 = token("--text-2") || "#52586e";
  const GRID = "rgba(20,33,61,.07)";

  // Local time display
  document.querySelectorAll(".js-local-time").forEach((el) => {
    const d = new Date(el.dataset.iso);
    if (!isNaN(d)) el.textContent = d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  });

  const dataEl = document.getElementById("analysis-data");
  if (dataEl && window.Chart) {
    const data = JSON.parse(dataEl.textContent);
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    Chart.defaults.color = TEXT2;

    // Single-series horizontal bars (one colour, no legend): % of each parameter's max.
    const barOpts = (tooltipLabel) => ({
      indexAxis: "y",
      maintainAspectRatio: false,
      responsive: true,
      animation: { duration: 700 },
      layout: { padding: { left: 8 } },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: tooltipLabel }, displayColors: false, padding: 10 },
      },
      scales: {
        x: { min: 0, max: 100, grid: { color: GRID }, border: { display: false },
             ticks: { callback: (v) => v + "%", stepSize: 25 } },
        y: { grid: { display: false }, border: { display: false } },
      },
    });

    const paramCtx = document.getElementById("paramChart");
    if (paramCtx) {
      new Chart(paramCtx, {
        type: "bar",
        data: {
          labels: data.keys.map((k, i) => `${k.charAt(0).toUpperCase() + k.slice(1)} (${data.max[i]})`),
          datasets: [{ data: data.percent, backgroundColor: SERIES, borderRadius: 4, borderSkipped: "start",
                       barThickness: 18, maxBarThickness: 22 }],
        },
        options: barOpts((ctx) => `${data.scores[ctx.dataIndex]} / ${data.max[ctx.dataIndex]} points (${ctx.raw}%)`),
      });
    }

    const atsCtx = document.getElementById("atsChart");
    if (atsCtx) {
      new Chart(atsCtx, {
        type: "bar",
        data: {
          labels: data.ats_labels,
          datasets: [{ data: data.ats_scores, backgroundColor: SERIES, borderRadius: 4, borderSkipped: "start",
                       barThickness: 16 }],
        },
        options: barOpts((ctx) => `${ctx.raw} / 100`),
      });
    }
  }

  // Recommendation priority filter
  const filter = document.getElementById("fb-filter");
  if (filter) {
    filter.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-filter]");
      if (!btn) return;
      filter.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
      const f = btn.dataset.filter;
      document.querySelectorAll(".fb-col").forEach((col) => {
        col.classList.toggle("d-none", f !== "all" && col.dataset.priority !== f);
      });
    });
  }

  // Delete analysis
  const del = document.getElementById("confirm-delete");
  if (del) {
    del.addEventListener("click", async () => {
      del.disabled = true;
      del.textContent = "Deleting…";
      try {
        const res = await fetch(del.dataset.url, { method: "DELETE" });
        if (!res.ok) throw new Error();
        window.location.assign(del.dataset.home + "?deleted=1");
      } catch (_) {
        del.disabled = false;
        del.textContent = "Delete failed - retry";
      }
    });
  }
})();
