/* Field Shift — tableau de bord : la parcelle vue du satellite + chiffres réels (API en direct). */
(function () {
  const T = Terra.t;
  const $ = (id) => document.getElementById(id);
  let reco = null, map = null, sigView = "now", chartView = "soil";

  FSI18N.extend({
    fr: {
      "d.back": "Retour au site", "d.rain16": "Pluie prévue 16 j", "d.location": "Localisation", "d.full": "Plein écran",
      "d.risk": "Risque sécheresse", "d.ndvi": "NDVI actuel", "d.soil": "Humidité du sol",
      "d.water_cov": "Besoin en eau couvert", "d.details": "Voir le détail", "d.new": "Nouvelle analyse",
      "d.ask_ph": "Comment puis-je t'aider ?", "d.send": "Envoyer", "d.mic": "Parler",
      "d.signals": "Signaux du champ", "d.this_week": "Cette semaine", "d.tab_now": "Actuel", "d.tab_norm": "Il y a 2 mois",
      "d.rain_vs": "Pluie vs normale", "d.soil_row": "Humidité du sol", "d.veg_row": "Végétation",
      "d.veg": "Végétation (NDVI)", "d.w4": "Il y a 4 sem.", "d.wnow": "Cette semaine", "d.trend": "Tendance",
      "d.soil_chart": "Humidité du sol", "d.rain_chart": "Pluie prévue", "d.8w": "8 semaines", "d.16d": "16 prochains jours",
      "d.tab_8w": "8 sem.", "d.tab_16d": "16 jours", "d.max": "Max",
      "d.water_save": "−{n} % d'eau",
      "d.adv.plant_now": "Les conditions sont <span class=\"soft\">idéales pour semer</span> {crop} <span class=\"soft\">maintenant.</span>",
      "d.adv.wait": "Mieux vaut <span class=\"soft\">attendre la pluie</span> avant de semer {crop}.",
      "d.adv.switch_crop": "Trop sec pour {crop} : <span class=\"soft\">choisissez une culture</span> plus résistante.",
      "d.credit": "Imagerie © Esri, Maxar · Données NASA POWER, MODIS, Open-Meteo",
    },
    en: {
      "d.back": "Back to site", "d.rain16": "Rain next 16 d", "d.location": "Location", "d.full": "Full screen",
      "d.risk": "Drought risk", "d.ndvi": "Current NDVI", "d.soil": "Soil moisture",
      "d.water_cov": "Water need covered", "d.details": "See details", "d.new": "New analysis",
      "d.ask_ph": "How can I help you?", "d.send": "Send", "d.mic": "Speak",
      "d.signals": "Field signals", "d.this_week": "This week", "d.tab_now": "Now", "d.tab_norm": "2 months ago",
      "d.rain_vs": "Rain vs normal", "d.soil_row": "Soil moisture", "d.veg_row": "Vegetation",
      "d.veg": "Vegetation (NDVI)", "d.w4": "4 weeks ago", "d.wnow": "This week", "d.trend": "Trend",
      "d.soil_chart": "Soil moisture", "d.rain_chart": "Rain forecast", "d.8w": "8 weeks", "d.16d": "Next 16 days",
      "d.tab_8w": "8 wks", "d.tab_16d": "16 days", "d.max": "Max",
      "d.water_save": "−{n}% water",
      "d.adv.plant_now": "Conditions are <span class=\"soft\">ideal for planting</span> {crop} <span class=\"soft\">now.</span>",
      "d.adv.wait": "Better <span class=\"soft\">wait for the rain</span> before planting {crop}.",
      "d.adv.switch_crop": "Too dry for {crop}: <span class=\"soft\">pick a more resilient</span> crop.",
      "d.credit": "Imagery © Esri, Maxar · Data NASA POWER, MODIS, Open-Meteo",
    },
    it: {
      "d.back": "Torna al sito", "d.rain16": "Pioggia 16 gg", "d.location": "Località", "d.full": "Schermo intero",
      "d.risk": "Rischio siccità", "d.ndvi": "NDVI attuale", "d.soil": "Umidità del suolo",
      "d.water_cov": "Fabbisogno d'acqua coperto", "d.details": "Vedi dettagli", "d.new": "Nuova analisi",
      "d.ask_ph": "Come posso aiutarti?", "d.send": "Invia", "d.mic": "Parla",
      "d.signals": "Segnali del campo", "d.this_week": "Questa settimana", "d.tab_now": "Ora", "d.tab_norm": "2 mesi fa",
      "d.rain_vs": "Pioggia vs normale", "d.soil_row": "Umidità del suolo", "d.veg_row": "Vegetazione",
      "d.veg": "Vegetazione (NDVI)", "d.w4": "4 sett. fa", "d.wnow": "Questa sett.", "d.trend": "Tendenza",
      "d.soil_chart": "Umidità del suolo", "d.rain_chart": "Pioggia prevista", "d.8w": "8 settimane", "d.16d": "Prossimi 16 giorni",
      "d.tab_8w": "8 sett.", "d.tab_16d": "16 giorni", "d.max": "Max",
      "d.water_save": "−{n}% d'acqua",
      "d.adv.plant_now": "Le condizioni sono <span class=\"soft\">ideali per seminare</span> {crop} <span class=\"soft\">ora.</span>",
      "d.adv.wait": "Meglio <span class=\"soft\">aspettare la pioggia</span> prima di seminare {crop}.",
      "d.adv.switch_crop": "Troppo secco per {crop}: <span class=\"soft\">scegli una coltura</span> più resistente.",
      "d.credit": "Immagini © Esri, Maxar · Dati NASA POWER, MODIS, Open-Meteo",
    },
  });

  /* ---------- Images (photos libres du projet) ---------- */
  const IMG = { maize: "cornfield.jpg", beans: "seedlings.jpg", sorghum: "rows.jpg", millet: "rows.jpg", cover: "mulch.jpg", other: "seedlings.jpg" };
  function cropImg(word) {
    const w = String(word || "").toLowerCase();
    if (/ma[iï]s|maize|corn|maíz/.test(w)) return IMG.maize;
    if (/haricot|bean|fagiol|frijol|légum|legum|niébé/.test(w)) return IMG.beans;
    if (/sorgh|sorgo|mil|miglio|millet|céréale|cereal|cereale/.test(w)) return IMG.sorghum;
    if (/couvert|cover|copertura|jachère|fallow|maggese/.test(w)) return IMG.cover;
    return IMG.other;
  }

  /* ---------- Carte satellite de la parcelle ---------- */
  function initMap(lat, lng) {
    if (!window.maplibregl || !Terra.hasWebGL()) return;
    const style = Terra.satStyle(false);
    style.projection = { type: "mercator" };
    delete style.sky;
    map = new maplibregl.Map({
      container: "d-map", style, center: [lng, lat], zoom: 15.4, attributionControl: false,
      scrollZoom: false, dragRotate: false, pitchWithRotate: false, touchZoomRotate: false, fadeDuration: 0,
    });
    map.on("load", drawContours);
    map.on("move", drawContours);
    new ResizeObserver(() => { map.resize(); drawContours(); }).observe($("d-map"));
    $("d-zin").onclick = () => map.zoomIn();
    $("d-zout").onclick = () => map.zoomOut();
  }
  $("d-full").onclick = () => {
    const el = document.querySelector(".d-main");
    if (document.fullscreenElement) document.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen();
  };

  /* Courbes de niveau autour de la parcelle (repère visuel, comme un relevé de terrain). */
  function rings(cx, cy, base, n, seed) {
    let out = "";
    for (let k = 1; k <= n; k++) {
      const r = base * k;
      let d = "";
      for (let i = 0; i <= 72; i++) {
        const a = (i / 72) * Math.PI * 2;
        const w = 1 + 0.09 * Math.sin(3 * a + seed) + 0.05 * Math.sin(5 * a + seed * 2) + 0.03 * k * Math.sin(2 * a + seed / 2) / n;
        d += (i ? "L" : "M") + (cx + Math.cos(a) * r * w).toFixed(1) + " " + (cy + Math.sin(a) * r * w * 0.82).toFixed(1);
      }
      out += `<path d="${d}Z"/>`;
    }
    return out + `<circle class="hub" cx="${cx}" cy="${cy}" r="11"/><circle class="hub-dot" cx="${cx}" cy="${cy}" r="4"/>`;
  }
  function drawContours() {
    const svg = $("d-contours");
    const w = svg.clientWidth, h = svg.clientHeight;
    if (!w || !h) return;
    let main = [w * 0.55, h * 0.47];
    if (map) { const p = map.project(map.getCenter()); main = [p.x, p.y]; }
    const s = Math.min(w, h);
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.innerHTML = rings(main[0], main[1], s * 0.022, 8, 1.3) + rings(w * 0.66, h * 0.17, s * 0.016, 7, 2.6) + rings(w * 0.2, h * 0.52, s * 0.015, 6, 4.1);
  }

  /* ---------- En-tête ---------- */
  function paintHead() {
    const place = Terra.getPlace();
    const f = FSStore.buildPayload();
    const name = place && place.name ? place.name : T("home.example");
    $("d-field").textContent = name.split(",")[0];
    const lat = f.latitude, lng = f.longitude;
    $("d-coords").textContent = `${Math.abs(lat).toFixed(4)}°${lat >= 0 ? "N" : "S"},\n${Math.abs(lng).toFixed(4)}°${lng >= 0 ? "E" : "W"}`;
    const parts = name.split(",").map((s) => s.trim()).filter(Boolean);
    $("d-place").textContent = parts.length > 1 ? parts[parts.length - 1] : place && place.name ? parts[0] : `${lat.toFixed(2)}°, ${lng.toFixed(2)}°`;
  }

  /* ---------- Chiffres ---------- */
  function ndviNow(r) {
    const n = r.nasa_indicators || {};
    if (n.ndvi != null) return n.ndvi;
    const s = (r.series && r.series.ndvi) || [];
    return s.length ? s[s.length - 1] : null;
  }
  function paintStats(r) {
    const n = r.nasa_indicators || {}, wb = r.water_budget || {};
    $("d-risk").textContent = r.risk_score;
    const nd = ndviNow(r);
    $("d-ndvi").textContent = nd != null ? Number(nd).toFixed(2) : "—";
    $("d-soil").textContent = n.soil_moisture != null ? Math.round(n.soil_moisture * 100) : "—";
    const fc = r.forecast || [];
    const r16 = n.forecast_rain_16d_mm != null ? n.forecast_rain_16d_mm : fc.reduce((a, x) => a + (x.rain_mm || 0), 0);
    $("d-rain16").textContent = fc.length || n.forecast_rain_16d_mm != null ? Math.round(r16) + " mm" : "—";
    $("d-water").textContent = wb.coverage_pct != null ? wb.coverage_pct : "—";
    const cls = Terra.wsClass(wb.status);
    $("d-water-pill").className = "d-pill " + (cls === "ok" ? "" : cls);
    $("d-water-pill").textContent = T("ws." + wb.status);
    const bad = (r.risk_components || []).filter((c) => c.level === "bad").length;
    if (window.FSSide) FSSide.setAlerts(bad);
  }

  /* ---------- Carte culture : culture actuelle + 3 rotations conseillées ---------- */
  function paintCrop(r) {
    const p = FSStore.getProfile() || {};
    $("d-crop-img").style.backgroundImage = `url('/img/photos/${cropImg(p.crop_label || p.crop || "maize")}')`;
    const rots = (r.rotations || []).slice(0, 3);
    $("d-crop-grid").innerHTML = rots.map((rt) => {
      const first = String(rt.name || "").split(/→|->/)[0].replace(/\(.*\)/, "").trim();
      const pct = rt.water_saving_pct != null ? rt.water_saving_pct : { high: 35, medium: 20, low: 5 }[rt.water_saving] || 0;
      return `<a class="d-tile" href="/globo.html#rotations" title="${rt.name}"><i style="background-image:url('/img/photos/${cropImg(first)}')"></i>
        <span>${first}<small>${T("d.water_save", { n: pct })}</small></span></a>`;
    }).join("") + `<a class="d-tile add" href="/globo.html"><b>+</b>${T("d.new")}</a>`;
  }

  /* ---------- Conseil ---------- */
  function paintAdvice(r) {
    const pt = r.planting_timeline || {};
    const key = { plant_now: "plant_now", wait: "wait", switch_crop: "switch_crop" }[pt.recommendation] || "wait";
    const crop = Terra.cropLabel(FSStore.getProfile() || {});
    $("d-advice").innerHTML = T("d.adv." + key).replace("{crop}", crop);
  }

  /* ---------- Signaux (barres segmentées) ---------- */
  function seg(pct) {
    const v = Math.max(0, Math.min(100, pct)) / 12.5;
    return `<div class="d-seg">${Array.from({ length: 8 }, (_, i) => `<i class="${v >= i + 1 ? "on" : v > i + 0.4 ? "half" : ""}"></i>`).join("")}</div>`;
  }
  function paintBars(r) {
    const n = r.nasa_indicators || {}, s = r.series || {};
    let rain, soil, veg;
    if (sigView === "now") {
      rain = n.rainfall_normal_mm ? (n.rainfall_60d_mm / n.rainfall_normal_mm) * 100 : 0;
      soil = (n.soil_moisture || 0) * 100;
      veg = (ndviNow(r) || 0) * 100;
    } else {
      const rn = (s.rainfall_normal_mm || [])[0] || 0;
      rain = rn ? (((s.rainfall_mm || [])[0] || 0) / rn) * 100 : 0;
      soil = ((s.soil_moisture || [])[0] || 0) * 100;
      veg = ((s.ndvi || [])[0] || 0) * 100;
    }
    const rows = [["d.rain_vs", rain], ["d.soil_row", soil], ["d.veg_row", veg]];
    $("d-bars").innerHTML = rows.map(([k, v]) => `<div class="d-bar-row"><header><span>${T(k)}</span><b>${Math.round(v)}<small>/100</small></b></header>${seg(v)}</div>`).join("");
  }

  /* ---------- Végétation : trois cercles ---------- */
  function paintCircles(r) {
    const nd = (r.series && r.series.ndvi) || [];
    const now = ndviNow(r);
    const w4 = nd.length >= 5 ? nd[nd.length - 5] : null;
    const tr = (r.nasa_indicators || {}).ndvi_trend;
    const f = (v) => (v == null ? "—" : "~" + Number(v).toFixed(2));
    $("d-circles").innerHTML = `
      <div class="d-circ c1"><b>${f(w4)}</b><small>${T("d.w4")}</small></div>
      <div class="d-circ c2"><b>${f(now)}</b><small>${T("d.wnow")}</small></div>
      <div class="d-circ c3"><b>${tr == null ? "—" : (tr > 0 ? "+" : "") + Number(tr).toFixed(2)}</b><small>${T("d.trend")}</small></div>`;
  }

  /* ---------- Courbe : humidité du sol (8 sem.) ou pluie prévue (16 j) ---------- */
  function paintChart(r) {
    const el = $("d-chart");
    let vals, labels, unit, title, sub;
    if (chartView === "soil") {
      const s = r.series || {};
      vals = (s.soil_moisture || []).map(Number); labels = s.labels || [];
      unit = ""; title = "d.soil_chart"; sub = "d.8w";
    } else {
      const fc = r.forecast || [];
      vals = fc.map((x) => x.rain_mm || 0);
      labels = fc.map((x) => new Date(x.date + "T12:00:00").toLocaleDateString(FSI18N.locale, { day: "numeric", month: "short" }).replace(".", ""));
      unit = " mm"; title = "d.rain_chart"; sub = "d.16d";
    }
    $("ch-title").textContent = T(title); $("ch-sub").textContent = T(sub);
    if (!vals.length) { el.innerHTML = ""; return; }
    const W = el.clientWidth || 360, H = el.clientHeight || 140, padB = 22, padT = 26;
    const mx = Math.max(...vals), mn = Math.min(...vals);
    const span = mx - mn || 1;
    const x = (i) => (vals.length === 1 ? W / 2 : (i / (vals.length - 1)) * W);
    const y = (v) => padT + (1 - (v - mn) / span) * (H - padT - padB - 10);
    const pts = vals.map((v, i) => [x(i), y(v)]);
    const line = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
    const area = line + ` L ${W} ${H - padB} L 0 ${H - padB} Z`;
    const iMax = vals.indexOf(mx);
    const step = Math.ceil(labels.length / 6);
    const xl = labels.map((l, i) => (i % step === 0 || i === iMax ? `<text class="xl ${i === iMax ? "on" : ""}" x="${Math.min(W - 18, Math.max(18, x(i)))}" y="${H - 6}" text-anchor="middle">${l}</text>` : "")).join("");
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      <defs><linearGradient id="d-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E3A2F" stop-opacity=".28"/><stop offset="1" stop-color="#2E3A2F" stop-opacity="0"/></linearGradient></defs>
      <path class="ar" d="${area}"/><path class="ln" d="${line}"/>
      <line class="vl" x1="${pts[iMax][0]}" y1="${pts[iMax][1]}" x2="${pts[iMax][0]}" y2="${H - padB}"/>
      <circle class="pk" cx="${pts[iMax][0]}" cy="${pts[iMax][1]}" r="3.5"/>${xl}</svg>
      <span class="d-tip" style="left:${Math.min(W - 50, Math.max(50, pts[iMax][0]))}px;top:${pts[iMax][1]}px">${T("d.max")}<b>${chartView === "soil" ? mx.toFixed(2) : Math.round(mx) + unit}</b></span>`;
  }

  /* ---------- Onglets, barre IA, micro ---------- */
  function tabs(id, cb) {
    $(id).addEventListener("click", (e) => {
      const b = e.target.closest("button[data-v]");
      if (!b) return;
      $(id).querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      cb(b.dataset.v);
    });
  }
  tabs("sig-tabs", (v) => { sigView = v; if (reco) paintBars(reco); });
  tabs("ch-tabs", (v) => { chartView = v; if (reco) paintChart(reco); });

  $("d-ask").addEventListener("submit", (e) => {
    e.preventDefault();
    const q = $("d-ask-in").value.trim();
    if (!window.FSAssistant) return;
    if (q) { FSAssistant.ask(q); $("d-ask-in").value = ""; } else FSAssistant.open();
  });
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  $("d-mic").onclick = () => {
    if (!SR) { $("d-ask-in").focus(); return; }
    const rec = new SR();
    rec.lang = FSI18N.locale; rec.interimResults = false;
    $("d-mic").classList.add("rec");
    rec.onresult = (e) => { $("d-ask-in").value = e.results[0][0].transcript; $("d-ask").requestSubmit(); };
    rec.onend = () => $("d-mic").classList.remove("rec");
    rec.start();
  };

  function paintAll() {
    paintHead();
    if (!reco) return;
    paintStats(reco); paintCrop(reco); paintAdvice(reco); paintBars(reco); paintCircles(reco); paintChart(reco);
  }

  async function load() {
    const payload = FSStore.buildPayload();
    paintHead();
    initMap(payload.latitude, payload.longitude);
    reco = FSStore.getLastReco();
    if (reco) paintAll();
    try {
      const { data } = await FSApi.getRecommendation(payload);
      reco = data;
    } catch (e) {
      if (!reco) { Terra.toast(T("an.error")); return; }
    }
    paintAll();
    if (window.FSAssistant && reco) FSAssistant.setContext(reco);
  }

  window.addEventListener("resize", () => { if (reco) paintChart(reco); });
  document.addEventListener("DOMContentLoaded", load);
  document.addEventListener("fs:langchange", async () => {
    paintAll();
    try { const { data } = await FSApi.getRecommendation(FSStore.buildPayload()); reco = data; paintAll(); } catch (e) {}
  });
})();
