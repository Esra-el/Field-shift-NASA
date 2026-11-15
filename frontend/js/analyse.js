/* Field Shift — analyse du terrain (maquette « scan »).
   Scan satellite de la parcelle (Esri) + vraie couche NDVI NASA GIBS (MODIS). */
(function () {
  const t = (k) => FSI18N.t(k);
  const $ = (id) => document.getElementById(id);
  const last = (a) => (a && a.length ? a[a.length - 1] : null);
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  const SAT_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const NDVI_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_NDVI_8Day/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.png";

  let data = null, map = null, ndviLayer = null, shape = null, layer = "sat", growth = null;

  // ---------------- Carte du scan ----------------
  function initMap() {
    const f = FSStore.getField();
    map = L.map("scan-map", {
      zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false,
      doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false,
    });
    L.tileLayer(SAT_URL, { maxZoom: 18 }).addTo(map);
    ndviLayer = L.tileLayer(NDVI_URL, { maxNativeZoom: 9, maxZoom: 18, opacity: 0.85 });
    if (f.polygon && f.polygon.length) {
      shape = L.polygon(f.polygon, { color: "#CDE8F6", weight: 2, fillOpacity: 0.08 }).addTo(map);
    } else {
      shape = L.circleMarker([f.latitude, f.longitude], { radius: 7, color: "#fff", weight: 2, fillColor: "#CDE8F6", fillOpacity: 1 }).addTo(map);
    }
    frame();
    $("layer-seg").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => setLayer(b.dataset.layer)));
    setLayer("sat");
  }
  function frame() {
    const f = FSStore.getField();
    if (layer === "ndvi") { map.setView([f.latitude, f.longitude], 11); return; }
    if (shape.getBounds) map.fitBounds(shape.getBounds(), { padding: [24, 24], maxZoom: 16 });
    else map.setView([f.latitude, f.longitude], 15);
  }
  function setLayer(l) {
    layer = l;
    if (l === "ndvi") map.addLayer(ndviLayer); else map.removeLayer(ndviLayer);
    $("layer-seg").querySelectorAll("button").forEach((b) => b.classList.toggle("is-active", b.dataset.layer === l));
    $("layer-note").textContent = t(l === "ndvi" ? "an.note_ndvi" : "an.note_sat");
    frame();
  }

  // ---------------- Rendu ----------------
  function render(d) {
    data = d;
    const f = FSStore.getField() || {};
    const ind = d.nasa_indicators, s = d.series || {}, wb = d.water_budget;

    $("an-title").textContent = cap(FSI18N.f("an.title", { crop: FSUI.cropLabel().toLowerCase() }));
    $("an-sub").textContent = `${f.area_ha ? f.area_ha + " ha · " : ""}${f.latitude}, ${f.longitude} · ${FSUI.fmtDay(new Date())}`;
    $("co-ndvi").textContent = Number(last(s.ndvi)).toFixed(2);
    $("co-soil").textContent = `${Number(ind.soil_moisture).toFixed(2)} m³/m³`;

    if (!map) initMap(); else setLayer(layer);
    scan();

    // Santé du champ
    const light = ind.solar_radiation >= 22 ? "lvl.high" : ind.solar_radiation >= 18 ? "lvl.mid" : "lvl.low";
    const trend = ind.ndvi_trend < -0.02 ? "lvl.declining" : ind.ndvi_trend > 0.02 ? "lvl.rising" : "lvl.stable";
    const tiles = [
      { icon: "solar:waterdrops-bold", label: t("h.water"), val: t("water." + wb.status) },
      { icon: "solar:cloud-rain-bold", label: t("h.soil"), val: `${Math.round(ind.soil_moisture * 100)} %` },
      { icon: "solar:sun-2-bold", label: t("h.light"), val: `${t(light)} · ${ind.solar_radiation} MJ/m²` },
      { icon: "solar:leaf-bold", label: t("h.veg"), val: `${t(trend)} (${ind.ndvi_trend})` },
    ];
    $("health").innerHTML = tiles.map((x) => `
      <div class="h-tile"><span class="h-ico">${FSUI.icon(x.icon, 20)}</span>
        <div><div class="h-label">${x.label}</div><div class="h-val">${x.val}</div></div></div>`).join("");

    drawGrowth(s);
    renderUpdates(d);
    setupVoice();

    if (location.hash === "#alerts") setTimeout(() => $("alerts").scrollIntoView({ behavior: "smooth" }), 300);
  }

  function scan() {
    const box = $("scan");
    box.classList.add("is-scanning");
    $("scan-state").textContent = t("an.scanning");
    clearTimeout(scan._t);
    scan._t = setTimeout(() => {
      box.classList.remove("is-scanning");
      $("scan-state").innerHTML = `${FSUI.icon("solar:check-circle-bold", 18)} ${t("an.done")}`;
    }, 1800);
  }

  function drawGrowth(s) {
    const vals = s.ndvi || [];
    if (growth) growth.destroy();
    const bubble = $("growth-delta");
    const first = vals[0], lst = last(vals);
    const pct = first ? Math.round(((lst - first) / first) * 100) : 0;
    bubble.textContent = `${pct >= 0 ? "↗ +" : "↘ "}${pct}%`;
    growth = new Chart($("growth-chart"), {
      type: "line",
      data: { labels: s.labels || [], datasets: [{
        data: vals, borderColor: "#fff", borderWidth: 2.5, tension: 0.35, fill: true,
        backgroundColor: "rgba(255,255,255,.28)",
        pointRadius: (c) => (c.dataIndex === vals.length - 1 ? 5 : 0),
        pointBackgroundColor: "#3A2B1F", pointBorderColor: "#fff", pointBorderWidth: 2,
      }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { tooltip: { enabled: true } },
        scales: {
          x: { grid: { display: false }, border: { display: false }, ticks: { color: "#5B4626", font: { size: 10 } } },
          y: { display: false },
        },
        animation: { onComplete: placeBubble },
      },
      plugins: [{ id: "bubble", afterRender: placeBubble }],
    });
    function placeBubble() {
      if (!growth) return;
      const meta = growth.getDatasetMeta(0);
      const p = meta && meta.data[meta.data.length - 1];
      if (!p) return;
      bubble.style.left = p.x + "px";
      bubble.style.top = p.y + "px";
      bubble.classList.remove("hidden");
    }
  }

  function renderUpdates(d) {
    const ind = d.nasa_indicators;
    const today = FSUI.fmtShort(new Date());
    const ORDER = { bad: 0, warn: 1, ok: 2 };
    const META = {
      rainfall: { icon: "solar:cloud-rain-linear", tag: "tag.rain", cls: "badge-yellow",
        text: () => FSI18N.f("upd.rain", { v: Math.round((100 * ind.rainfall_60d_mm) / ind.rainfall_normal_mm) }) },
      soil_moisture: { icon: "solar:waterdrops-linear", tag: "tag.water", cls: "badge-dark",
        text: (c) => FSI18N.f("upd.soil", { v: c.value }) },
      ndvi: { icon: "solar:leaf-linear", tag: "tag.veg", cls: "badge-gray",
        text: (c) => FSI18N.f("upd.ndvi", { v: c.value }) },
      heat: { icon: "solar:sun-2-linear", tag: "tag.heat", cls: "badge-amber",
        text: (c) => FSI18N.f("upd.heat", { v: c.value }) },
    };
    const rows = (d.risk_components || []).slice().sort((a, b) => ORDER[a.level] - ORDER[b.level]);
    $("upd-list").innerHTML = rows.map((c) => {
      const m = META[c.factor];
      if (!m) return "";
      return `<a class="row" href="/panel.html#details">
        <span class="u-ico c-${c.level}">${FSUI.icon(m.icon, 18)}</span>
        <span class="bold">${m.text(c)}</span>
        <span class="badge ${m.cls}">${t(m.tag)}</span>
        <span class="u-date">${today}</span>
        ${FSUI.icon("solar:alt-arrow-right-linear", 16)}
      </a>`;
    }).join("");
  }

  // ---------------- Analyse vocale (Web Speech API) ----------------
  const SPEEDS = [1, 1.25, 0.75];
  let speedIdx = 0, voiceReady = false;
  const canSpeak = "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";

  function voiceText() {
    return [data.ai_explanation, data.planting_timeline && data.planting_timeline.reason].filter(Boolean).join(" ");
  }
  function fmtDur(sec) { const s = Math.max(1, Math.round(sec)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; }
  function updateDur() {
    const words = voiceText().split(/\s+/).length;
    $("voice-dur").textContent = fmtDur(words / (2.6 * SPEEDS[speedIdx]));
  }
  function setPlaying(on) {
    $("voice-box").classList.toggle("is-playing", on);
    $("voice-icon").setAttribute("icon", on ? "solar:pause-bold" : "solar:play-bold");
  }
  function speak() {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(voiceText());
    u.lang = FSI18N.locale;
    u.rate = SPEEDS[speedIdx];
    u.onend = () => setPlaying(false);
    u.onerror = () => setPlaying(false);
    speechSynthesis.speak(u);
    setPlaying(true);
  }

  function setupVoice() {
    // Forme d'onde décorative, stable pour un même texte.
    let seed = voiceText().length;
    $("wave").innerHTML = Array.from({ length: 52 }, () => {
      seed = (seed * 9301 + 49297) % 233280;
      return `<span style="height:${18 + (seed / 233280) * 82}%;animation-delay:${(seed % 9) / 10}s"></span>`;
    }).join("");
    updateDur();
    if (!canSpeak) {
      $("voice-na").classList.remove("hidden");
      ["voice-play", "voice-stop", "voice-speed"].forEach((id) => { $(id).disabled = true; $(id).style.opacity = 0.4; });
      return;
    }
    if (voiceReady) { speechSynthesis.cancel(); setPlaying(false); return; }
    voiceReady = true;
    $("voice-play").addEventListener("click", () => {
      if (speechSynthesis.speaking && !speechSynthesis.paused) { speechSynthesis.pause(); setPlaying(false); }
      else if (speechSynthesis.paused) { speechSynthesis.resume(); setPlaying(true); }
      else speak();
    });
    $("voice-stop").addEventListener("click", () => { speechSynthesis.cancel(); setPlaying(false); });
    $("voice-speed").addEventListener("click", () => {
      speedIdx = (speedIdx + 1) % SPEEDS.length;
      $("voice-speed").textContent = SPEEDS[speedIdx] + "x";
      updateDur();
      if (speechSynthesis.speaking) speak();
    });
    window.addEventListener("pagehide", () => speechSynthesis.cancel());
  }

  FSUI.dataPage(render);
})();
