/* Field Shift — backtesting : « l'outil aurait-il prévenu lors des sécheresses passées ? ». */
(function () {
  const t = (k) => FSI18N.t(k);
  const BADGE = { low: "badge-green", moderate: "badge-amber", high: "badge-red" };

  async function load() {
    const loading = document.getElementById("loading");
    try {
      const res = await FSApi.getBacktesting(FSStore.buildPayload());
      loading.classList.add("hidden");
      document.getElementById("content").classList.remove("hidden");
      render(res.data, res);
    } catch (e) {
      loading.innerHTML = `<p class="c-red" style="margin-bottom:16px">${t("panel.error")}</p>
        <button class="btn btn-dark" onclick="location.reload()">${t("panel.retry")}</button>`;
    }
  }

  function render(data, res) {
    const sum = document.getElementById("bt-summary");
    sum.removeAttribute("data-i18n");
    sum.textContent = data.summary;
    FSUI.stamp(document.getElementById("bt-stamp"), res, data);

    const seasons = data.seasons || [];
    const total = data.total || seasons.length;
    const warned = data.warned_count != null ? data.warned_count : seasons.filter((s) => s.warned).length;
    const pct = total ? Math.round((warned / total) * 100) : 0;
    const avgRain = seasons.length ? Math.round(seasons.reduce((a, s) => a + s.rainfall_pct, 0) / seasons.length) : 0;
    document.getElementById("bt-ring").innerHTML = FSUI.ring(pct, "#2E7D32", 150, 12);
    document.getElementById("bt-pct").textContent = pct + " %";
    document.getElementById("bt-total").textContent = total;
    document.getElementById("bt-warned").textContent = warned;
    document.getElementById("bt-rain").textContent = avgRain + " %";
    document.getElementById("bt-badge").textContent = `${warned}/${total}`;

    document.getElementById("bt-list").innerHTML = seasons.map((s) => {
      const color = FSUI.RISK_COLOR[s.risk_level] || "#64705F";
      const nino = s.tag && s.tag !== "—";
      const anom = s.rainfall_anomaly_pct != null ? s.rainfall_anomaly_pct : s.rainfall_pct - 100;
      const ndvi = s.ndvi_trend != null ? s.ndvi_trend : 0;
      const lv = (ok, warn) => (ok ? "ok" : warn ? "warn" : "bad");
      return `<li class="bt-item${s.warned ? " warned" : ""}">
        <span class="bt-dot" style="background:${color}"></span>
        <article class="card">
          <div class="card-head">
            <div><h3 class="card-title">${s.season}</h3><p class="card-sub">${s.alert || t("risk." + s.risk_level)}</p></div>
            ${nino ? `<span class="badge badge-amber">${FSUI.icon("solar:sun-fog-bold", 16)} ${s.tag}</span>` : ""}
          </div>
          <div class="bt-metrics">
            <div class="ind lvl-${lv(anom >= -10, anom >= -30)}"><p class="ind-k">${FSUI.icon("solar:cloud-rain-bold", 18)} ${t("bt.anomaly")}</p><p class="ind-v num">${anom > 0 ? "+" : ""}${anom} %</p></div>
            <div class="ind lvl-${lv(s.soil_moisture >= 0.2, s.soil_moisture >= 0.12)}"><p class="ind-k">${FSUI.icon("solar:waterdrops-bold", 18)} ${t("bt.soil")}</p><p class="ind-v num">${s.soil_moisture != null ? Math.round(s.soil_moisture * 100) + " %" : "—"}</p></div>
            <div class="ind lvl-${lv(ndvi >= 0, ndvi >= -0.1)}"><p class="ind-k">${FSUI.icon("solar:leaf-bold", 18)} ${t("bt.ndvi")}</p><p class="ind-v num">${ndvi > 0 ? "+" : ""}${ndvi}</p></div>
            <div class="ind bt-score"><p class="ind-k">${FSUI.icon("solar:danger-triangle-bold", 18)} ${t("bt.score_label")}</p>
              <div class="bt-ring">${FSUI.ring(s.risk_score, color, 64, 7)}<div class="ring-label"><div class="num">${s.risk_score}</div></div></div></div>
          </div>
          <div class="bt-verdict">
            <div class="outcome ${s.warned ? "warn" : "ok"}">${FSUI.icon(s.warned ? "solar:bell-bing-bold" : "solar:check-circle-bold", 20)}
              <span><span class="xs" style="display:block;font-weight:400">${t("bt.warned_q")}</span>${t(s.warned ? "bt.yes" : "bt.no")}</span></div>
            <div class="outcome" style="background:var(--surface-2);color:var(--ink)">${FSUI.icon("solar:clipboard-check-bold", 20)}
              <span><span class="xs" style="display:block;font-weight:400;color:var(--ink-2)">${t("bt.action")}</span>${s.action || s.outcome}</span></div>
          </div>
        </article>
      </li>`;
    }).join("");
    drawChart(seasons);
  }

  let chart = null;
  function drawChart(seasons) {
    if (!window.Chart) return;
    if (chart) chart.destroy();
    chart = new Chart(document.getElementById("bt-chart"), {
      data: {
        labels: seasons.map((s) => s.season),
        datasets: [
          { type: "bar", label: t("bt.anomaly") + " (%)", data: seasons.map((s) => (s.rainfall_anomaly_pct != null ? s.rainfall_anomaly_pct : s.rainfall_pct - 100)),
            backgroundColor: seasons.map((s) => (s.tag && s.tag !== "—" ? "#D9731A" : "#7FB6D9")), borderRadius: 8, maxBarThickness: 48, yAxisID: "y" },
          { type: "line", label: t("bt.score_label"), data: seasons.map((s) => s.risk_score), borderColor: "#1E4D2B", backgroundColor: "#1E4D2B",
            pointRadius: 6, pointHoverRadius: 8, borderWidth: 3, tension: 0.3, yAxisID: "y1" },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
        plugins: { legend: { display: true, labels: { boxWidth: 12, font: { size: 13 } } } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#EFE7D8" }, border: { display: false }, ticks: { callback: (v) => v + " %" } },
          y1: { position: "right", min: 0, max: 100, grid: { drawOnChartArea: false }, border: { display: false } },
        },
      },
    });
  }

  document.addEventListener("fs:langchange", load);
  load();
})();
