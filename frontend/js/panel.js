/* Field Shift — tableau de bord « compris en 30 secondes ».
   1. La réponse du jour (semer / attendre / changer) · 2. risque, eau, quand semer
   3. actions · 4. données scientifiques repliées (indicateurs NASA + graphiques). */
(function () {
  const t = (k) => FSI18N.t(k);
  const $ = (id) => document.getElementById(id);
  const last = (a) => (a && a.length ? a[a.length - 1] : null);
  const PLANT = {
    plant_now: { color: "#2E7D32", icon: "solar:check-circle-bold", badge: "badge-green" },
    wait: { color: "#B85C10", icon: "solar:clock-circle-bold", badge: "badge-amber" },
    switch_crop: { color: "#C0392B", icon: "solar:danger-triangle-bold", badge: "badge-red" },
  };
  const LVL_BADGE = { low: "badge-green", moderate: "badge-amber", high: "badge-red" };
  const LVL_ICON = { low: "solar:check-circle-bold", moderate: "solar:danger-circle-bold", high: "solar:danger-triangle-bold" };
  const WATER = {
    enough_water: { badge: "badge-green", icon: "solar:check-circle-bold" },
    risky: { badge: "badge-amber", icon: "solar:danger-circle-bold" },
    not_enough_water: { badge: "badge-red", icon: "solar:danger-triangle-bold" },
  };
  let data = null;
  const charts = {};

  function render(d, res) {
    data = d;
    const field = FSStore.getField() || {};
    const pt = d.planting_timeline, wb = d.water_budget, P = PLANT[pt.recommendation] || PLANT.wait;

    // --- 1. Réponse du jour
    $("hero-field").innerHTML = `${FSUI.icon("mdi:sprout", 16)} ${FSI18N.f("dash.field_of", { crop: FSUI.cropLabel().toLowerCase() })}${field.area_ha ? " · " + field.area_ha + " ha" : ""}`;
    $("hero-place").innerHTML = `${FSUI.icon("solar:map-point-bold", 16)} ${field.latitude}, ${field.longitude}`;
    FSUI.stamp($("hero-stamp"), res, d);
    $("hero-date").textContent = FSUI.fmtDay(new Date());
    $("hero-reco").innerHTML = `${FSUI.icon(P.icon, 44)}<span>${t("plant." + pt.recommendation)}</span>`;
    $("hero-reco").style.color = P.color;
    $("hero-reason").textContent = pt.reason;

    // --- 2a. Risque
    const color = FSUI.RISK_COLOR[d.risk_level];
    $("risk-ring").innerHTML = FSUI.ring(d.risk_score, color, 170, 14);
    $("risk-score").textContent = d.risk_score;
    $("risk-score").style.color = color;
    $("risk-badge").className = "badge " + LVL_BADGE[d.risk_level];
    $("risk-badge").innerHTML = `${FSUI.icon(LVL_ICON[d.risk_level], 16)} ${t("risk." + d.risk_level)}`;
    $("risk-marker").style.left = `calc(${Math.max(0, Math.min(100, d.risk_score))}% - .6rem)`;

    // --- 2b. Eau
    const W = WATER[wb.status] || WATER.risky;
    $("water-status").className = "badge " + W.badge;
    $("water-status").innerHTML = `${FSUI.icon(W.icon, 16)} ${t("water." + wb.status)}`;
    $("w-need").textContent = wb.crop_water_need_mm + " mm";
    $("w-avail").textContent = wb.available_water_mm + " mm";
    const cov = Math.round((100 * wb.available_water_mm) / Math.max(1, wb.crop_water_need_mm));
    $("w-bar").style.width = Math.min(100, cov) + "%";
    $("w-bar").style.background = cov >= 100 ? "#2E7D32" : cov >= 65 ? "#D9731A" : "#C0392B";
    const diff = wb.available_water_mm - wb.crop_water_need_mm;
    $("w-delta").className = "water-delta " + (diff >= 0 ? "ok" : cov >= 65 ? "mid" : "bad");
    $("w-delta").innerHTML = `${FSUI.icon(diff >= 0 ? "solar:check-circle-bold" : "solar:waterdrop-bold", 22)}
      <span>${t(diff >= 0 ? "dash.surplus" : "dash.deficit")}</span><b>${Math.abs(diff)} mm</b>`;
    $("w-explain").textContent = wb.explanation || "";

    // --- 2c. Quand semer
    $("plant-badge").className = "badge " + P.badge;
    $("plant-badge").innerHTML = `${FSUI.icon(P.icon, 16)} ${t("plant." + pt.recommendation)}`;
    $("plant-window").textContent = FSUI.fmtWindow(pt.best_window);
    renderCalendar(pt, P);

    // --- 4. Détails scientifiques
    renderIndicators(d);
    renderWhy(d);
    $("ai-explain").textContent = d.ai_explanation || "";
    const det = $("details");
    if (det.open) drawCharts();
    det.ontoggle = () => { if (det.open) drawCharts(); };
    if (location.hash === "#details" && !det.dataset.opened) {
      det.dataset.opened = "1"; det.open = true;
      setTimeout(() => det.scrollIntoView({ behavior: "smooth" }), 300);
    }

    // --- Lecture à voix haute : la réponse en phrases simples
    const summary = () => [
      `${t("dash.today")} : ${t("plant." + pt.recommendation)}.`, pt.reason,
      `${t("panel.risk")} : ${d.risk_score} ${t("dash.out_of")}, ${t("risk." + d.risk_level)}.`,
      `${t("panel.water")} : ${t("water." + wb.status)}. ${t("panel.need")} ${wb.crop_water_need_mm} mm, ${t("panel.available")} ${wb.available_water_mm} mm.`,
      `${t("plant.window")} : ${FSUI.fmtWindow(pt.best_window)}.`,
    ].join(" ");
    FSUI.setSpeech(summary);
    $("hero-listen").onclick = () => FSUI.speak(summary());
  }

  function renderCalendar(pt, P) {
    const win = FSUI.parseWindow(pt.best_window);
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const monday = new Date(today); monday.setDate(today.getDate() - ((today.getDay() + 6) % 7));
    const weeks = Array.from({ length: 6 }, (_, i) => {
      const a = new Date(monday); a.setDate(monday.getDate() + i * 7);
      const b = new Date(a); b.setDate(a.getDate() + 6);
      return { a, on: !!(win && a <= win[1] && b >= win[0]) };
    });
    const firstOn = weeks.findIndex((w) => w.on);
    const lastOn = weeks.length - 1 - weeks.slice().reverse().findIndex((w) => w.on);
    const markerAt = firstOn >= 0 ? firstOn : 0;
    $("cal-weeks").innerHTML = weeks.map((w, i) => `<div class="wk${i === 0 ? " is-now" : ""}">${t("cal.week")}${i + 1}</div>`).join("");
    $("cal-area").innerHTML = weeks.map((w, i) => {
      const cls = w.on ? ` is-window${i === firstOn ? " first" : ""}${i === lastOn ? " last" : ""}` : "";
      const marker = i === markerAt ? `<div class="cal-marker"><div class="seed" style="color:${P.color}">${FSUI.icon(pt.recommendation === "switch_crop" ? "solar:danger-triangle-bold" : "mdi:sprout", 28)}</div></div>` : "";
      return `<div class="cal-col${cls}">${marker}</div>`;
    }).join("");
    $("cal-axis").innerHTML = weeks.map((w) => `<span>${FSUI.fmtShort(w.a)}</span>`).join("");
  }

  function renderIndicators(d) {
    const ind = d.nasa_indicators, s = d.series || {};
    const rainPct = Math.round((100 * ind.rainfall_60d_mm) / ind.rainfall_normal_mm);
    const lvl = (ok, warn) => (ok ? "ok" : warn ? "warn" : "bad");
    const cells = [
      { k: "ind.rainfall", help: "rain", icon: "solar:cloud-rain-bold", v: `${ind.rainfall_60d_mm} mm`, sub: `${rainPct} % · ${t("chart.normal")} ${ind.rainfall_normal_mm} mm`, l: lvl(rainPct >= 90, rainPct >= 70) },
      { k: "ind.soil_moisture", help: "soil", icon: "solar:waterdrops-bold", v: `${Math.round(ind.soil_moisture * 100)} %`, sub: "SMAP", l: lvl(ind.soil_moisture >= 0.2, ind.soil_moisture >= 0.12) },
      { k: "ind.ndvi", help: "ndvi", icon: "solar:leaf-bold", v: `${ind.ndvi_trend > 0 ? "+" : ""}${ind.ndvi_trend}`, sub: `${t(ind.ndvi_trend < -0.02 ? "lvl.declining" : ind.ndvi_trend > 0.02 ? "lvl.rising" : "lvl.stable")} · MODIS`, l: lvl(ind.ndvi_trend >= 0, ind.ndvi_trend >= -0.1) },
      { k: "ind.temp", help: "temp", icon: "solar:temperature-bold", v: `${ind.temperature_c != null ? ind.temperature_c : last(s.temperature_c)} °C`, sub: "NASA POWER", l: "ok" },
      { k: "ind.solar", help: "solar", icon: "solar:sun-2-bold", v: `${ind.solar_radiation} MJ/m²`, sub: "NASA POWER", l: "ok" },
      { k: "ind.et", help: "et", icon: "solar:wind-bold", v: `${ind.evapotranspiration} mm/d`, sub: "NASA POWER", l: lvl(ind.evapotranspiration <= 4.5, ind.evapotranspiration <= 5.5) },
    ];
    $("indicators").innerHTML = cells.map((c) => `
      <div class="ind lvl-${c.l}">
        <span class="ind-ico">${FSUI.icon(c.icon, 22)}</span>
        <p class="ind-k" data-help="${c.help}"><span>${t(c.k)}</span></p>
        <p class="ind-v num">${c.v}</p>
        <p class="xs muted">${c.sub}</p>
      </div>`).join("");
  }

  function renderWhy(d) {
    const ICON = { rainfall: "solar:cloud-rain-bold", soil_moisture: "solar:waterdrops-bold", ndvi: "solar:leaf-bold", heat: "solar:sun-2-bold" };
    $("risk-why").innerHTML = (d.risk_components || []).map((c) => `
      <div class="why-row">
        <span class="why-ico c-${c.level}">${FSUI.icon(ICON[c.factor] || "solar:info-circle-linear", 22)}</span>
        <div><p class="bold">${t("rc." + c.factor)}</p><p class="small c-${c.level}">${c.value}</p></div>
        <div class="xs faint" style="text-align:right">${c.source}<br>${t("rc.weight")} ${c.weight}</div>
      </div>`).join("");
  }

  /* Graphiques interactifs (dessinés à l'ouverture des détails : un canvas caché n'a pas de taille). */
  function mk(id, cfg) {
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart($(id), cfg);
  }
  function base(unit) {
    return {
      responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.dataset.label || ""} ${c.formattedValue} ${c.dataset.unit || unit || ""}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 12 } } },
        y: { grid: { color: "#EFE7D8" }, border: { display: false }, ticks: { font: { size: 12 }, maxTicksLimit: 5 } },
      },
    };
  }
  function drawCharts() {
    const s = data && data.series;
    if (!s) return;
    const rain = base("mm");
    rain.plugins.legend = { display: true, labels: { boxWidth: 12, font: { size: 13 } } };
    mk("rain-chart", { type: "bar", data: { labels: s.labels, datasets: [
      { type: "bar", label: t("var.rain"), data: s.rainfall_mm, backgroundColor: "#7FB6D9", hoverBackgroundColor: "#2B78B6", borderRadius: 8, maxBarThickness: 28 },
      { type: "line", label: t("chart.normal"), data: s.rainfall_normal_mm, borderColor: "#7A4E2D", borderDash: [6, 5], pointRadius: 0, borderWidth: 2.5 },
    ] }, options: rain });
    mk("soil-chart", { type: "line", data: { labels: s.labels, datasets: [
      { label: t("var.soil"), data: s.soil_moisture.map((v) => Math.round(v * 100)), unit: "%", borderColor: "#7A4E2D", backgroundColor: "rgba(167,132,90,.18)", fill: true, tension: 0.35, pointRadius: 4, pointBackgroundColor: "#7A4E2D" },
    ] }, options: base("%") });
    mk("ndvi-chart", { type: "line", data: { labels: s.labels, datasets: [
      { label: "NDVI", data: s.ndvi, borderColor: "#2E7D32", backgroundColor: "rgba(46,125,50,.14)", fill: true, tension: 0.35, pointRadius: 4, pointBackgroundColor: "#2E7D32" },
    ] }, options: base("") });
    const clim = base("");
    clim.plugins.legend = { display: true, labels: { boxWidth: 12, font: { size: 13 } } };
    clim.scales.y1 = { position: "right", grid: { drawOnChartArea: false }, border: { display: false }, ticks: { font: { size: 12 }, maxTicksLimit: 5 } };
    mk("climate-chart", { type: "line", data: { labels: s.labels, datasets: [
      { label: t("chart.solar"), data: s.solar_radiation, unit: "MJ/m²", borderColor: "#D9A21A", backgroundColor: "#D9A21A", tension: 0.35, pointRadius: 3, yAxisID: "y" },
      { label: t("chart.et"), data: s.evapotranspiration || [], unit: "mm/d", borderColor: "#1E4D2B", backgroundColor: "#1E4D2B", borderDash: [6, 4], tension: 0.35, pointRadius: 3, yAxisID: "y1" },
    ] }, options: clim });
  }

  FSUI.dataPage(render);
})();
