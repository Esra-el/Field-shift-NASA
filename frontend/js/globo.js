/* Field Shift — Analyse : formulaire → rapport, globe satellite réel (vol jusqu'à la parcelle),
   couches NASA GIBS réelles une à une, réponses simples, rotations. L'assistant est flottant (assistant.js). */
(function () {
  FSI18N.extend({
    fr: { "src.est": "Données en direct indisponibles : estimation", "src.live": "Données en direct", "src.offline": "Hors ligne : dernière analyse enregistrée", "src.estimate": "estimation (source indisponible)",
      "fc.title": "Pluie prévue · 16 jours", "fc.sub": "Maintenant : {t} °C · humidité {h} % · vent {v} km/h — prévision Open-Meteo", "adv.root": "Humidité zone racinaire" },
    en: { "src.est": "Live data unavailable: estimate", "src.live": "Live data", "src.offline": "Offline: last saved analysis", "src.estimate": "estimate (source unavailable)",
      "fc.title": "Rain forecast · 16 days", "fc.sub": "Now: {t} °C · humidity {h}% · wind {v} km/h — Open-Meteo forecast", "adv.root": "Root-zone wetness" },
    it: { "src.est": "Dati in tempo reale non disponibili: stima", "src.live": "Dati in tempo reale", "src.offline": "Offline: ultima analisi salvata", "src.estimate": "stima (fonte non disponibile)",
      "fc.title": "Pioggia prevista · 16 giorni", "fc.sub": "Ora: {t} °C · umidità {h}% · vento {v} km/h — previsione Open-Meteo", "adv.root": "Umidità zona radicale" },
  });
  FSI18N.extend({
    fr: {
      "f.kicker": "Analyse satellite gratuite",
      "f.crop_q": "Que cultivez-vous ?", "f.crop_ph": "Ex. : maïs, niébé, arachide, manioc…",
      "f.soil_q": "Comment est votre terre ?", "f.water_q": "Avez-vous de l'eau pour arroser ?",
      "f.have_q": "Ce dont vous disposez", "f.optional": "facultatif",
      "f.have_ph": "Ex. : un puits, 2 hectares, un réservoir, des animaux…",
      "f.need_loc": "Indiquez d'abord où se trouve votre parcelle.",
      "soil.unknown": "Je ne sais pas",
      "soil.sandy.d": "L'eau part vite", "soil.sandy_loam.d": "Un peu de tout", "soil.clay_loam.d": "Garde bien l'eau", "soil.clay.d": "Lourde, collante", "soil.unknown.d": "On choisit pour vous",
      "irr.none.l": "Non, seulement la pluie", "irr.limited.l": "Un peu", "irr.available.l": "Oui, régulièrement",
      "irr.none.d": "Pas de puits ni de pompe", "irr.limited.d": "Puits, bidons, petit bassin", "irr.available.d": "Pompe, canal, goutte-à-goutte",
      "ld.title": "Le satellite observe votre parcelle…",
      "ld.s1": "Localisation de votre terrain", "ld.s2": "Lecture de la pluie et de l'humidité du sol (NASA)", "ld.s3": "Calcul de votre budget d'eau", "ld.s4": "Préparation de vos conseils",
      "rp.edit": "Modifier", "rp.advice": "Notre conseil", "rp.window": "Fenêtre de semis", "rp.sat_sees": "Ce que voit le satellite",
      "rp.signals": "Ce qu'il faut retenir", "rp.season": "Votre saison, étape par étape", "rp.ask": "Une question ? Demandez à l'assistant",
      "rp.date": "Rapport du {d}", "rp.score": "risque", "wb.gap": "Il manque", "wb.surplus": "En plus", "rp.days": "{n} jours",
      "sc.covered": "des besoins en eau couverts", "sc.have": "Disponible", "sc.need": "Besoin", "sc.missing": "Il manque {n} mm d'eau pour finir la saison.", "sc.surplus": "{n} mm de marge : l'eau suffit pour la saison.",
      "rot.pick": "Le plan conseillé pour votre priorité est marqué « Pour vous ».", "rot.steps": "Par où commencer",
    },
    en: {
      "f.kicker": "Free satellite analysis",
      "f.crop_q": "What do you grow?", "f.crop_ph": "E.g. maize, cowpea, groundnut, cassava…",
      "f.soil_q": "What is your soil like?", "f.water_q": "Do you have water to irrigate?",
      "f.have_q": "What you have", "f.optional": "optional",
      "f.have_ph": "E.g. a well, 2 hectares, a water tank, animals…",
      "f.need_loc": "First tell us where your field is.",
      "soil.unknown": "I don't know",
      "soil.sandy.d": "Water drains fast", "soil.sandy_loam.d": "A bit of everything", "soil.clay_loam.d": "Holds water well", "soil.clay.d": "Heavy, sticky", "soil.unknown.d": "We choose for you",
      "irr.none.l": "No, only rain", "irr.limited.l": "A little", "irr.available.l": "Yes, regularly",
      "irr.none.d": "No well or pump", "irr.limited.d": "Well, cans, small pond", "irr.available.d": "Pump, canal, drip",
      "ld.title": "The satellite is looking at your field…",
      "ld.s1": "Locating your land", "ld.s2": "Reading rain and soil moisture (NASA)", "ld.s3": "Computing your water budget", "ld.s4": "Preparing your advice",
      "rp.edit": "Edit", "rp.advice": "Our advice", "rp.window": "Planting window", "rp.sat_sees": "What the satellite sees",
      "rp.signals": "Key takeaways", "rp.season": "Your season, step by step", "rp.ask": "A question? Ask the assistant",
      "rp.date": "Report of {d}", "rp.score": "risk", "wb.gap": "Missing", "wb.surplus": "Extra", "rp.days": "{n} days",
      "sc.covered": "of water needs covered", "sc.have": "Available", "sc.need": "Needed", "sc.missing": "{n} mm of water missing to finish the season.", "sc.surplus": "{n} mm to spare: water is enough for the season.",
      "rot.pick": "The plan suited to your priority is marked “For you”.", "rot.steps": "Where to start",
    },
    it: {
      "f.kicker": "Analisi satellitare gratuita",
      "f.crop_q": "Cosa coltivi?", "f.crop_ph": "Es.: mais, fagiolo dall'occhio, arachidi, manioca…",
      "f.soil_q": "Com'è la tua terra?", "f.water_q": "Hai acqua per irrigare?",
      "f.have_q": "Cosa hai a disposizione", "f.optional": "facoltativo",
      "f.have_ph": "Es.: un pozzo, 2 ettari, una cisterna, animali…",
      "f.need_loc": "Indica prima dove si trova il tuo campo.",
      "soil.unknown": "Non lo so",
      "soil.sandy.d": "L'acqua scappa via", "soil.sandy_loam.d": "Un po' di tutto", "soil.clay_loam.d": "Trattiene bene l'acqua", "soil.clay.d": "Pesante, appiccicosa", "soil.unknown.d": "Scegliamo noi",
      "irr.none.l": "No, solo pioggia", "irr.limited.l": "Un po'", "irr.available.l": "Sì, regolarmente",
      "irr.none.d": "Niente pozzo né pompa", "irr.limited.d": "Pozzo, taniche, piccolo bacino", "irr.available.d": "Pompa, canale, goccia a goccia",
      "ld.title": "Il satellite osserva il tuo campo…",
      "ld.s1": "Localizzazione del terreno", "ld.s2": "Lettura di pioggia e umidità del suolo (NASA)", "ld.s3": "Calcolo del bilancio idrico", "ld.s4": "Preparazione dei consigli",
      "rp.edit": "Modifica", "rp.advice": "Il nostro consiglio", "rp.window": "Finestra di semina", "rp.sat_sees": "Cosa vede il satellite",
      "rp.signals": "Da ricordare", "rp.season": "La tua stagione, passo per passo", "rp.ask": "Una domanda? Chiedi all'assistente",
      "rp.date": "Rapporto del {d}", "rp.score": "rischio", "wb.gap": "Mancano", "wb.surplus": "In più", "rp.days": "{n} giorni",
      "sc.covered": "del fabbisogno d'acqua coperto", "sc.have": "Disponibile", "sc.need": "Fabbisogno", "sc.missing": "Mancano {n} mm d'acqua per finire la stagione.", "sc.surplus": "{n} mm di margine: l'acqua basta per la stagione.",
      "rot.pick": "Il piano adatto alla tua priorità è segnato «Per te».", "rot.steps": "Da dove iniziare",
    },
  });

  const T = Terra.t;
  const $ = (id) => document.getElementById(id);

  const state = {
    lat: null, lng: null, name: "",
    crop: "", soil: "sandy_loam", irr: "none", prio: "save_water",
    reco: null, layer: "sat", picking: false, tour: null, rot: 0,
  };

  /* =====================================================
     Formulaire
     ===================================================== */
  const SUGGEST = {
    fr: ["Maïs", "Haricot", "Niébé", "Sorgho", "Mil", "Arachide", "Manioc", "Riz", "Tomate", "Café"],
    en: ["Maize", "Beans", "Cowpea", "Sorghum", "Millet", "Groundnut", "Cassava", "Rice", "Tomato", "Coffee"],
    it: ["Mais", "Fagioli", "Fagiolo dall'occhio", "Sorgo", "Miglio", "Arachidi", "Manioca", "Riso", "Pomodoro", "Caffè"],
  };
  const SOILS = [["sandy", "#E8D3A8"], ["sandy_loam", "#C9A675"], ["clay_loam", "#9A6B47"], ["clay", "#6B4329"], ["unknown", null]];
  const IRR = [["none", "lucide:cloud-rain"], ["limited", "lucide:droplet"], ["available", "lucide:waves"]];
  const PRIOS = [["save_water", "lucide:droplets"], ["protect_soil", "lucide:shield"], ["max_yield", "lucide:wheat"], ["food_security", "lucide:utensils"]];

  function paintForm() {
    const sug = SUGGEST[FSI18N.lang] || SUGGEST.fr;
    $("crop-list").innerHTML = sug.map((s) => `<option value="${s}"></option>`).join("");
    $("crop-suggest").innerHTML = sug.slice(0, 6).map((s) => `<button type="button" class="sug">${s}</button>`).join("");

    $("soil").innerHTML = SOILS.map(([v, c]) => `
      <button type="button" class="tile" data-v="${v}" aria-pressed="${state.soil === v}">
        <span class="swatch" style="${c ? `background:${c}` : ""}">${c ? "" : '<iconify-icon icon="lucide:circle-help" width="18" height="18"></iconify-icon>'}</span>
        <b>${T("soil." + v)}</b><small>${T("soil." + v + ".d")}</small>
      </button>`).join("");
    $("irr").innerHTML = IRR.map(([v, ic]) => `
      <button type="button" class="tile" data-v="${v}" aria-pressed="${state.irr === v}">
        <span class="tile-ic"><iconify-icon icon="${ic}" width="22" height="22"></iconify-icon></span>
        <b>${T("irr." + v + ".l")}</b><small>${T("irr." + v + ".d")}</small>
      </button>`).join("");
    $("prio").innerHTML = PRIOS.map(([v, ic]) => `<button type="button" class="chip" data-v="${v}" aria-pressed="${state.prio === v}"><iconify-icon icon="${ic}" width="18" height="18"></iconify-icon>${T("prio." + v)}</button>`).join("");
  }

  function pickIn(el, key) {
    el.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-v]"); if (!b) return;
      state[key] = b.dataset.v;
      el.querySelectorAll("button[data-v]").forEach((x) => x.setAttribute("aria-pressed", x === b));
    });
  }

  function prefill() {
    const f = FSStore.getField(), p = FSStore.getProfile(), place = Terra.getPlace();
    if (f) { state.lat = f.latitude; state.lng = f.longitude; }
    if (place && place.name) { state.name = place.name; $("loc").value = place.name; }
    else if (f) $("loc").value = `${f.latitude.toFixed(4)}, ${f.longitude.toFixed(4)}`;
    if (p) {
      $("crop").value = p.crop_label || (p.crop ? Terra.cropLabel(p) : "");
      if (p.soil_choice || p.soil_type) state.soil = p.soil_choice || p.soil_type;
      if (IRR.some(([v]) => v === p.irrigation_level)) state.irr = p.irrigation_level;
      if (PRIOS.some(([v]) => v === p.priority)) state.prio = p.priority;
      if (p.resources) $("have").value = p.resources;
    }
  }

  function parseCoords(q) {
    const m = q.trim().match(/^(-?\d+(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d+(?:[.,]\d+)?)$/);
    if (!m) return null;
    const lat = parseFloat(m[1].replace(",", ".")), lng = parseFloat(m[2].replace(",", "."));
    if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
    return { lat, lng };
  }
  async function geocode(q) {
    const c = parseCoords(q);
    if (c) return { ...c, name: await reverse(c.lat, c.lng) };
    const url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(q) + "&accept-language=" + FSI18N.lang;
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    const js = await res.json();
    if (!js.length) return null;
    return { lat: +js[0].lat, lng: +js[0].lon, name: shortName(js[0].display_name) };
  }
  async function reverse(lat, lng) {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&zoom=10&lat=${lat}&lon=${lng}&accept-language=${FSI18N.lang}`);
      const js = await res.json();
      return js && js.display_name ? shortName(js.display_name) : "";
    } catch (e) { return ""; }
  }
  function shortName(s) { const p = String(s).split(",").map((x) => x.trim()); return p.length > 2 ? `${p[0]}, ${p[p.length - 1]}` : p.join(", "); }

  function setLocation(lat, lng, name) {
    state.lat = lat; state.lng = lng; state.name = name || "";
    $("g-name").textContent = name || T("home.your_field");
    $("g-coords").textContent = Terra.fmtCoords(lat, lng);
    placeMarker(lat, lng);
  }

  /* ---------- Vues : formulaire → chargement → rapport ---------- */
  function showView(v) {
    ["form", "loading", "report"].forEach((k) => $(k + "-view").classList.toggle("hidden", k !== v));
    const panel = $("panel");
    if (window.matchMedia("(min-width: 1000px)").matches) panel.scrollTo({ top: 0, behavior: "smooth" });
    else if (v !== "form") panel.scrollIntoView({ behavior: "smooth", block: "start" });
    document.body.dataset.view = v;
  }

  let ldTimer = null;
  function runLoadingSteps() {
    const items = [...$("scan-steps").children];
    items.forEach((li) => li.className = "");
    let i = 0;
    clearInterval(ldTimer);
    items[0].className = "is-now";
    ldTimer = setInterval(() => {
      items[i].className = "is-done"; i++;
      if (i < items.length) items[i].className = "is-now"; else clearInterval(ldTimer);
    }, 900);
  }

  async function onSubmit(e) {
    e.preventDefault();
    const q = $("loc").value.trim();
    if (!q && state.lat == null) { Terra.toast(T("f.need_loc")); $("loc").focus(); return; }
    const btn = $("go");
    btn.disabled = true; $("go-label").textContent = T("an.analysing"); $("g-status").textContent = T("an.analysing");
    try {
      if (q && q !== state.name) {
        const g = await geocode(q).catch(() => null);
        if (!g) { Terra.toast(T("an.not_found")); return; }
        setLocation(g.lat, g.lng, g.name || q);
      }
      const cropText = $("crop").value.trim() || T("crop.maize");
      const profile = {
        crop: Terra.cropKey(cropText), crop_label: cropText,
        soil_type: state.soil === "unknown" ? "sandy_loam" : state.soil, soil_choice: state.soil,
        irrigation: state.irr !== "none", irrigation_level: state.irr, priority: state.prio,
        resources: $("have").value.trim(),
      };
      FSStore.setField({ latitude: state.lat, longitude: state.lng });
      FSStore.setProfile(profile);
      Terra.setPlace({ name: state.name, lat: state.lat, lng: state.lng });

      showView("loading"); runLoadingSteps();
      stopTour();
      showLayer("sat", { silent: true });
      const flight = flyToField(state.lat, state.lng);
      const [{ data, offline }] = await Promise.all([FSApi.getRecommendation(FSStore.buildPayload()), flight, new Promise((r) => setTimeout(r, 3600))]);
      state.offline = !!offline;
      if (offline) Terra.toast(T("an.offline"));
      state.reco = data;
      renderResults();
      showView("report");
      $("g-status").textContent = T("an.live");
      if (window.FSAssistant) FSAssistant.setContext(data);
      startTour();
    } catch (err) {
      console.error(err);
      showView("form");
      Terra.toast(T("an.error"));
    } finally {
      btn.disabled = false; $("go-label").textContent = T("cta.analyse");
    }
  }

  /* =====================================================
     Globe satellite (MapLibre)
     ===================================================== */
  let map = null, spinner = null, marker = null, mapReady = null;

  /* Couches NASA GIBS réelles — palettes officielles GIBS pour les légendes. */
  const GIBS = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/";
  const LAYERS = {
    sat:   { icon: "lucide:satellite" },
    rain:  { icon: "lucide:cloud-rain", id: "IMERG_Precipitation_Rate", tms: "GoogleMapsCompatible_Level6", z: 6, period: "day", src: "NASA GPM IMERG",
             ramp: ["#00764E", "#1EB200", "#EFED00", "#FF532A", "#BB0000"] },
    wind:  { icon: "lucide:wind", id: "MERRA2_Surface_Wind_Speed_Monthly", tms: "GoogleMapsCompatible_Level6", z: 6, period: "month", src: "NASA MERRA-2",
             ramp: ["#5E4FA2", "#8FD2A4", "#EBF79F", "#FEE492", "#F89053", "#9E0142"] },
    temp:  { icon: "lucide:thermometer", id: "MERRA2_2m_Air_Temperature_Monthly", tms: "GoogleMapsCompatible_Level6", z: 6, period: "month", src: "NASA MERRA-2",
             ramp: ["#5E4FA2", "#8ED1A4", "#EBF7A0", "#FEE28F", "#F88A50", "#9E0142"] },
    solar: { icon: "lucide:sun", id: "MERRA2_Incident_Shortwave_Over_Land_Monthly", tms: "GoogleMapsCompatible_Level6", z: 6, period: "month", src: "NASA MERRA-2",
             ramp: ["#5E4FA2", "#8DD1A4", "#EAF69F", "#FEE594", "#F99254", "#9E0142"] },
    soil:  { icon: "lucide:layers", id: "SMAP_L4_Analyzed_Root_Zone_Soil_Moisture", tms: "GoogleMapsCompatible_Level6", z: 6, period: "day", src: "NASA SMAP L4",
             ramp: ["#FFA200", "#CAE400", "#00B46A", "#0071FF", "#00008C"] },
    ndvi:  { icon: "lucide:leaf", id: "VIIRS_NOAA20_NDVI_8Day", tms: "GoogleMapsCompatible_Level8", z: 8, period: "day", src: "NASA VIIRS NOAA-20",
             ramp: ["#C8B5A5", "#9A6E59", "#64A601", "#1D7501", "#001801"] },
  };
  const ORDER = ["sat", "rain", "wind", "temp", "solar", "soil", "ndvi"];
  const tileUrl = (L) => `${GIBS}${L.id}/default/default/${L.tms}/{z}/{y}/{x}.png`;

  function initMap() {
    const el = $("globe");
    if (!window.maplibregl || !Terra.hasWebGL()) {
      el.innerHTML = `<div class="g-fallback"><div><iconify-icon icon="lucide:earth" width="48" height="48"></iconify-icon><p style="margin-top:8px">${T("no3d")}</p></div></div>`;
      return;
    }
    const start = state.lat != null ? [state.lng + 40, state.lat] : [-50, 12];
    map = new maplibregl.Map({
      container: el, style: Terra.satStyle(true), center: start, zoom: window.innerWidth < 700 ? 1.1 : 1.7,
      attributionControl: { compact: true }, maxPitch: 75, renderWorldCopies: false,
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true, showCompass: true }), "top-right");
    spinner = Terra.spinGlobe(map, { speed: 6 });
    mapReady = new Promise((r) => map.once("load", r));
    mapReady.then(() => {
      // Zone de la parcelle (≈ 400 m autour du point).
      map.addSource("field", { type: "geojson", data: circle(0, 0, 0.0001) });
      map.addLayer({ id: "field-fill", type: "fill", source: "field", paint: { "fill-color": "#A9CFA0", "fill-opacity": 0.12 } });
      map.addLayer({ id: "field-line", type: "line", source: "field", paint: { "line-color": "#EEF3EE", "line-width": 2, "line-dasharray": [2, 1.5] } });
      if (state.lat != null) placeMarker(state.lat, state.lng);
    });
    map.on("click", (e) => {
      if (!state.picking) return;
      togglePick(false);
      const { lat, lng } = e.lngLat;
      setLocation(lat, lng, "");
      $("loc").value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
      reverse(lat, lng).then((n) => { if (n) { state.name = n; $("loc").value = n; $("g-name").textContent = n; } });
      map.flyTo({ center: [lng, lat], zoom: Math.max(map.getZoom(), 13), duration: 1500 });
    });
  }

  function circle(lat, lng, km) {
    const pts = [], n = 64, dLat = km / 111.32, dLng = km / (111.32 * Math.cos((lat * Math.PI) / 180));
    for (let i = 0; i <= n; i++) { const a = (i / n) * Math.PI * 2; pts.push([lng + dLng * Math.cos(a), lat + dLat * Math.sin(a)]); }
    return { type: "Feature", geometry: { type: "Polygon", coordinates: [pts] } };
  }

  function placeMarker(lat, lng) {
    if (!map) return;
    if (!marker) {
      const d = document.createElement("div");
      d.className = "pin";
      d.innerHTML = `<span class="tag" id="pin-tag">${T("home.your_field")}</span><span class="dot"><i></i></span>`;
      marker = new maplibregl.Marker({ element: d, anchor: "bottom" });
    }
    marker.setLngLat([lng, lat]).addTo(map);
    const src = map.getSource && map.getSource("field");
    if (src) src.setData(circle(lat, lng, 0.4));
  }

  /* Vol « observatoire » : on recule pour voir la planète, puis on plonge sur la parcelle. */
  function flyToField(lat, lng) {
    if (!map) return new Promise((r) => setTimeout(r, 600));
    spinner.pause();
    return mapReady.then(() => new Promise((resolve) => {
      placeMarker(lat, lng);
      map.flyTo({ center: [lng, lat], zoom: 2.2, pitch: 0, bearing: 0, duration: 1600, essential: true });
      map.once("moveend", () => {
        map.flyTo({ center: [lng, lat], zoom: 14.6, pitch: 52, bearing: -18, speed: 0.9, curve: 1.6, essential: true });
        map.once("moveend", () => {
          // Petite orbite lente autour du champ, puis arrêt.
          map.easeTo({ bearing: 12, duration: 5200, easing: (t) => t * (2 - t) });
          resolve();
        });
      });
    }));
  }

  /* =====================================================
     Couches
     ===================================================== */
  function renderLayerButtons() {
    $("layers").innerHTML = ORDER.map((k) => `<button class="layer-btn" data-layer="${k}" aria-pressed="${state.layer === k}" ${state.reco || k === "sat" ? "" : "disabled"}><iconify-icon icon="${LAYERS[k].icon}" width="18" height="18"></iconify-icon>${T("layer." + k)}</button>`).join("");
  }

  async function ensureGibs(k) {
    await mapReady;
    const L = LAYERS[k], id = "gibs-" + k;
    if (!map.getSource(id)) {
      map.addSource(id, { type: "raster", tiles: [tileUrl(L)], tileSize: 256, maxzoom: L.z, attribution: "NASA EOSDIS GIBS" });
      map.addLayer({ id, type: "raster", source: id, layout: { visibility: "none" }, paint: { "raster-opacity": 0.72, "raster-fade-duration": 400, "raster-resampling": "linear" } }, "labels");
    }
    return id;
  }

  const dateCache = {};
  async function layerDate(k) {
    if (dateCache[k] !== undefined) return dateCache[k];
    const L = LAYERS[k], z = 3, n = 2 ** z;
    const x = Math.floor(((state.lng + 180) / 360) * n);
    const r = (state.lat * Math.PI) / 180;
    const y = Math.floor(((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * n);
    try {
      const res = await fetch(tileUrl(L).replace("{z}", z).replace("{y}", y).replace("{x}", x));
      dateCache[k] = (res.headers.get("layer-time-actual") || "").slice(0, 10) || null;
    } catch (e) { dateCache[k] = null; }
    return dateCache[k];
  }

  async function showLayer(k, opts) {
    state.layer = k;
    document.querySelectorAll(".layer-btn").forEach((b) => b.setAttribute("aria-pressed", b.dataset.layer === k));
    wind(k === "wind");
    if (map) {
      await mapReady;
      Object.keys(LAYERS).forEach((o) => { if (o !== "sat" && map.getLayer("gibs-" + o)) map.setLayoutProperty("gibs-" + o, "visibility", "none"); });
      if (k !== "sat") {
        const id = await ensureGibs(k);
        if (state.layer === k) map.setLayoutProperty(id, "visibility", "visible");
        // Les données NASA couvrent une région : on recule pour voir la tendance autour du champ.
        if (state.lat != null && map.getZoom() > 7.2) map.flyTo({ center: [state.lng, state.lat], zoom: 6.2, pitch: 20, bearing: 0, duration: 2200, essential: true });
      } else if (!(opts && opts.silent) && state.lat != null && map.getZoom() < 11) {
        map.flyTo({ center: [state.lng, state.lat], zoom: 14.6, pitch: 52, bearing: -10, duration: 2600, essential: true });
      }
    }
    paintLegend(k);
    renderInsight(k);
  }

  async function paintLegend(k) {
    const L = LAYERS[k], box = $("legend");
    box.classList.remove("hidden");
    $("lg-title").textContent = T("layer." + k);
    if (k === "sat") {
      box.classList.add("is-sat");
      $("lg-min").textContent = T("lg.sat"); $("lg-max").textContent = ""; $("lg-date").textContent = "Esri · Maxar";
      return;
    }
    box.classList.remove("is-sat");
    const lg = T("lg." + k);
    $("lg-min").textContent = lg[0]; $("lg-max").textContent = lg[1];
    $("lg-ramp").style.background = `linear-gradient(90deg, ${L.ramp.join(",")})`;
    $("lg-date").textContent = L.src;
    if (state.lat == null) return;
    const d = await layerDate(k);
    if (d && state.layer === k) {
      const txt = L.period === "month" ? T("lg.month", { d: Terra.fmtDate(d, { month: "long", year: "numeric" }) }) : T("lg.date", { d: Terra.fmtDate(d, { day: "numeric", month: "long", year: "numeric" }) });
      $("lg-date").textContent = `${L.src} · ${txt}`;
    }
  }

  /* Vent : particules animées dans la vraie direction du vent (NASA POWER), au-dessus de la carte MERRA-2. */
  let windRAF = null;
  function wind(on) {
    const cv = $("wind");
    cancelAnimationFrame(windRAF); windRAF = null;
    const ctx = cv.getContext("2d");
    if (!on || !state.reco) { ctx.clearRect(0, 0, cv.width, cv.height); cv.classList.add("hidden"); return; }
    cv.classList.remove("hidden");
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const resize = () => { cv.width = cv.clientWidth * dpr; cv.height = cv.clientHeight * dpr; };
    resize();
    const w = state.reco.weather || { wind_speed_kmh: 10, wind_dir_deg: 90 };
    const speed = 0.6 + Math.min(1, w.wind_speed_kmh / 30) * 1.8;
    const parts = Array.from({ length: 260 }, () => ({ x: Math.random() * cv.width, y: Math.random() * cv.height, age: Math.random() * 120 }));
    function frame() {
      const bearing = map ? map.getBearing() : 0;
      const toward = ((w.wind_dir_deg + 180 - bearing) * Math.PI) / 180;
      const dx = Math.sin(toward) * speed * dpr, dy = -Math.cos(toward) * speed * dpr;
      ctx.globalCompositeOperation = "destination-in";
      ctx.fillStyle = "rgba(0,0,0,0.92)"; ctx.fillRect(0, 0, cv.width, cv.height);
      ctx.globalCompositeOperation = "source-over";
      ctx.strokeStyle = "rgba(238,248,255,0.85)"; ctx.lineWidth = 1.3 * dpr;
      ctx.beginPath();
      for (const p of parts) {
        const wob = Math.sin((p.y / cv.height) * 6 + p.age * 0.02) * 0.35;
        const nx = p.x + dx + wob * dy * 0.3, ny = p.y + dy - wob * dx * 0.3;
        ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny);
        p.x = nx; p.y = ny; p.age++;
        if (p.age > 140 || p.x < 0 || p.y < 0 || p.x > cv.width || p.y > cv.height) { p.x = Math.random() * cv.width; p.y = Math.random() * cv.height; p.age = 0; }
      }
      ctx.stroke();
      windRAF = requestAnimationFrame(frame);
    }
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) frame();
    window.addEventListener("resize", resize, { once: true });
  }

  /* Visite guidée : chaque couche quelques secondes, puis retour au satellite. */
  function startTour() {
    stopTour();
    renderLayerButtons();
    const seq = ["rain", "wind", "temp", "solar", "soil", "ndvi", "sat"];
    let i = 0;
    const step = () => {
      showLayer(seq[i]); i++;
      if (i < seq.length) state.tour = setTimeout(step, 3200);
      else { state.tour = null; Terra.toast(T("an.ready")); }
    };
    state.tour = setTimeout(step, 1800);
  }
  function stopTour() { if (state.tour) { clearTimeout(state.tour); state.tour = null; } }


  /* =====================================================
     Textes simples
     ===================================================== */
  function compass(deg) { return T("dir")[Math.round((deg % 360) / 45) % 8]; }

  function layerInsight(k) {
    const r = state.reco, n = r.nasa_indicators || {}, w = r.weather || {};
    switch (k) {
      case "sat": return { lead: T("in.sat"), more: T("in.sat.more"), lvl: "info" };
      case "rain": {
        const below = n.rainfall_60d_mm < n.rainfall_normal_mm * 0.85;
        return { lead: T(below ? "in.rain.below" : "in.rain.ok"), more: T("in.rain.more", { a: n.rainfall_60d_mm, b: n.rainfall_normal_mm }), lvl: below ? "warn" : "ok" };
      }
      case "wind": {
        const strong = w.wind_speed_kmh > 20;
        return { lead: T("in.wind", { s: Math.round(w.wind_speed_kmh), d: compass(w.wind_dir_deg) }), more: T(strong ? "in.wind.more" : "in.wind.calm"), lvl: strong ? "warn" : "ok" };
      }
      case "temp": {
        const hot = w.heat_stress || n.temperature_c > 30;
        return { lead: T(hot ? "in.temp.hot" : "in.temp.ok", { t: n.temperature_c }), more: T("in.temp.more"), lvl: hot ? "bad" : "ok" };
      }
      case "solar": {
        const high = n.solar_radiation >= 20;
        return { lead: T(high ? "in.solar.high" : "in.solar.ok"), more: T("in.solar.more", { et: n.evapotranspiration }), lvl: high ? "warn" : "ok" };
      }
      case "soil": {
        const low = n.soil_moisture < 0.2;
        return { lead: T(low ? "in.soil.low" : "in.soil.ok"), more: T("in.soil.more", { p: Math.round(n.soil_moisture * 100) }), lvl: low ? "warn" : "ok" };
      }
      case "ndvi": {
        const stress = n.ndvi_trend < -0.04;
        return { lead: T(stress ? "in.ndvi.stress" : "in.ndvi.ok"), more: T(stress ? "in.ndvi.more" : "in.ndvi.more_ok"), lvl: stress ? "warn" : "ok" };
      }
    }
  }

  function renderInsight(k) {
    if (!state.reco) return;
    const ins = layerInsight(k);
    $("in-layer").textContent = T("layer." + k);
    $("in-icon").setAttribute("icon", LAYERS[k].icon);
    $("in-lead").textContent = ins.lead;
    $("in-more").textContent = ins.more;
    $("insight").dataset.lvl = ins.lvl;
    const card = $("insight"); card.classList.remove("fade-in"); void card.offsetWidth; card.classList.add("fade-in");
  }

  /* Anneau de score (SVG) */
  function ring(score, cls) {
    const r = 46, c = 2 * Math.PI * r, off = c * (1 - Math.max(0, Math.min(100, score)) / 100);
    return `<svg viewBox="0 0 110 110" role="img" aria-label="${score}/100">
      <circle cx="55" cy="55" r="${r}" class="r-track"/>
      <circle cx="55" cy="55" r="${r}" class="r-val ${cls}" stroke-dasharray="${c}" stroke-dashoffset="${c}" data-off="${off}" transform="rotate(-90 55 55)"/>
    </svg><div class="r-num"><b>${score}</b><span>/100</span><small>${T("rp.score")}</small></div>`;
  }

  const LVL_ICON = { bad: "lucide:circle-alert", warn: "lucide:triangle-alert", ok: "lucide:circle-check" };
  const STAGE_ICON = { planting: "lucide:sprout", growing: "lucide:leaf", flowering: "lucide:flower-2", harvest: "lucide:wheat" };
  const VERDICT_ICON = { plant_now: "lucide:sprout", wait: "lucide:hourglass", switch_crop: "lucide:refresh-cw" };

  function renderResults() {
    const r = state.reco, p = FSStore.getProfile() || {};
    const rc = Terra.riskClass(r.risk_level);
    const wb = r.water_budget || {}, pt = r.planting_timeline || {};

    // En-tête du rapport
    $("rp-date").textContent = T("rp.date", { d: Terra.fmtDate(new Date().toISOString().slice(0, 10), { day: "numeric", month: "long", year: "numeric" }) });
    $("rp-place").textContent = state.name || Terra.fmtCoords(state.lat, state.lng);
    const soilTxt = T("soil." + (p.soil_choice || p.soil_type || "sandy_loam"));
    $("rp-tags").innerHTML = [
      ["lucide:sprout", Terra.cropLabel(p)], ["lucide:layers", soilTxt], ["lucide:droplet", T("irr." + (p.irrigation_level || "none") + ".l")],
    ].map(([ic, tx]) => `<span class="tag"><iconify-icon icon="${ic}" width="14" height="14"></iconify-icon>${tx}</span>`).join("");

    // Verdict
    const plc = Terra.plClass(pt.recommendation);
    $("verdict").className = "verdict has-photo v-" + plc;
    $("verdict").style.setProperty("--bg", `url('/img/photos/${{ plant_now: "seedlings.jpg", wait: "rain.jpg", switch_crop: "cornfield.jpg" }[pt.recommendation] || "rows.jpg"}')`);
    $("v-ring").innerHTML = ring(r.risk_score, rc);
    requestAnimationFrame(() => setTimeout(() => { const v = document.querySelector("#v-ring .r-val"); if (v) v.style.strokeDashoffset = v.dataset.off; }, 60));
    $("v-title").innerHTML = `<iconify-icon icon="${VERDICT_ICON[pt.recommendation] || "lucide:info"}" width="26" height="26"></iconify-icon>${T("pl." + pt.recommendation)}`;
    $("v-reason").textContent = pt.reason || "";
    $("v-window").innerHTML = `<iconify-icon icon="lucide:calendar" width="16" height="16"></iconify-icon>${T("rp.window")} : <b>${Terra.fmtWindow(pt.best_window)}</b>`;

    // Risque : jauge en demi-cercle
    $("k-risk").textContent = r.risk_score;
    $("k-risk-b").className = "badge " + rc; $("k-risk-b").textContent = T("risk." + rc);
    $("k-risk-d").textContent = T("risk." + rc + ".d");
    document.querySelectorAll(".rp-duo .semi-seg").forEach((p) => p.classList.toggle("is-on", p.classList.contains({ low: "low", moderate: "mod", high: "high" }[rc])));
    const ang = -90 + Math.max(0, Math.min(100, r.risk_score)) * 1.8;
    $("r-needle").style.transform = "rotate(-90deg)";
    requestAnimationFrame(() => setTimeout(() => { $("r-needle").style.transform = `rotate(${ang}deg)`; }, 120));

    // Signaux
    const items = ["rain", "soil", "ndvi", "solar", "temp"].map((k) => Object.assign({ k }, layerInsight(k)));
    if (wb.status !== "enough_water") items.push({ k: "water", lead: T("in.need_water"), lvl: wb.status === "risky" ? "warn" : "bad" });
    items.sort((a, b) => ({ bad: 0, warn: 1, ok: 2 }[a.lvl] - { bad: 0, warn: 1, ok: 2 }[b.lvl]));
    $("r-list").innerHTML = items.map((x) => `<li class="sig ${x.lvl}" ${LAYERS[x.k] ? `data-layer="${x.k}" tabindex="0" role="button"` : ""}>
      <iconify-icon icon="${LVL_ICON[x.lvl]}" width="22" height="22"></iconify-icon><span>${x.lead}</span>
      ${LAYERS[x.k] ? `<iconify-icon class="go" icon="lucide:map" width="18" height="18"></iconify-icon>` : ""}</li>`).join("");

    // Budget d'eau : disponible vs besoin
    const need = wb.crop_water_need_mm || 0, have = wb.available_water_mm || 0;
    const max = Math.max(need, have, 1);
    $("k-water").textContent = wb.coverage_pct;
    $("k-water-b").className = "badge " + Terra.wsClass(wb.status); $("k-water-b").textContent = T("ws." + wb.status);
    $("w-need").textContent = need + " mm";
    $("w-have").textContent = have + " mm";
    $("w-goal").style.left = (need / max) * 100 + "%";
    $("w-have-bar").className = "wbar-fill ok";
    $("w-have-bar").style.width = "0";
    requestAnimationFrame(() => setTimeout(() => { $("w-have-bar").style.width = (have / max) * 100 + "%"; }, 120));
    const gap = need - have;
    $("w-gap-txt").textContent = gap > 0 ? T("sc.missing", { n: gap }) : T("sc.surplus", { n: -gap });
    $("w-reco").textContent = T("wb.reco." + wb.status);

    // Saison
    const stages = (r.season && r.season.stages) || [];
    const dry = (r.season && r.season.dry_spells) || [];
    const days = (a, b) => Math.round((new Date(b) - new Date(a)) / 864e5) + 1;
    $("mini-tl").innerHTML = stages.map((s) => {
      const d = dry.find((x) => x.start <= s.end && x.end >= s.start);
      return `<div class="tl-item ${s.stage}">
        <span class="tl-dot"><iconify-icon icon="${STAGE_ICON[s.stage]}" width="16" height="16"></iconify-icon></span>
        <div class="tl-body"><b>${T("stage." + s.stage)}</b><span>${Terra.fmtDate(s.start)} – ${Terra.fmtDate(s.end)} · ${T("rp.days", { n: days(s.start, s.end) })}</span>
        ${d ? `<span class="tl-warn"><iconify-icon icon="lucide:triangle-alert" width="14" height="14"></iconify-icon>${T("stage.dry")} : ${Terra.fmtDate(d.start)} – ${Terra.fmtDate(d.end)}</span>` : ""}</div></div>`;
    }).join("");

    // Rotations (onglets)
    state.rot = 0;
    renderRotations();

    // Sources en direct + prévision de pluie
    renderLive(r);

    // Détails scientifiques (source réelle, ou « estimation » si la source n'a pas répondu)
    const n = r.nasa_indicators || {}, w = r.weather || {};
    const est = new Set(r.estimated || []);
    const live = !!r.live;
    const src = (key, name) => (!live || est.has(key) ? T("src.estimate") : name);
    const ds = {}; (r.data_sources || []).forEach((s) => { ds[s.name] = s.date; });
    const d = (name) => (ds[name] ? ` · ${Terra.fmtDate(String(ds[name]).slice(0, 10))}` : "");
    const rows = [
      ["adv.rain", src("rainfall_60d_mm", "NASA POWER" + d("NASA POWER")), `${n.rainfall_60d_mm} mm`],
      ["adv.normal", src("rainfall_normal_mm", T("adv.normal_src")), `${n.rainfall_normal_mm} mm`],
      ["adv.soil", src("soil_moisture", "Open-Meteo" + d("Open-Meteo")), `${n.soil_moisture} m³/m³`],
      ...(n.root_zone_wetness != null ? [["adv.root", "NASA POWER GWETROOT", `${Math.round(n.root_zone_wetness * 100)} %`]] : []),
      ["adv.ndvi", src("ndvi_trend", "NASA MODIS" + d("NASA MODIS (MOD13Q1)")), `${n.ndvi_trend > 0 ? "+" : ""}${n.ndvi_trend}${n.ndvi != null ? ` (${n.ndvi})` : ""}`],
      ["adv.solar", src("solar_mj_m2", "Open-Meteo"), `${n.solar_radiation} MJ/m²/j`],
      ["adv.et", src("et0_mm_day", "Open-Meteo ET₀ FAO-56"), `${n.evapotranspiration} mm/j`],
      ["adv.temp", src("temperature_7d_c", "Open-Meteo"), `${n.temperature_c} °C`],
      ["adv.wind", src("wind", "Open-Meteo"), `${w.wind_speed_kmh} km/h · ${w.wind_dir_deg}°`],
    ];
    $("adv").innerHTML = rows.map(([k, s, v]) => `<tr><td>${T(k)}<small>${s}</small></td><td>${v}</td></tr>`).join("");

    renderLayerButtons();
    renderInsight(state.layer);
  }

  function renderLive(r) {
    const bar = $("live-bar");
    const srcs = r.data_sources || [];
    if (r.live && srcs.length && !state.offline) {
      const chips = srcs.map((s) => {
        const dt = String(s.date || "");
        const when = dt.length > 10 ? `${Terra.fmtDate(dt.slice(0, 10))} ${dt.slice(11, 16)}` : Terra.fmtDate(dt);
        return `<span class="lv-src"><b>${s.name}</b>${when}</span>`;
      }).join("");
      bar.className = "live-bar is-live";
      bar.innerHTML = `<span class="lv-dot"></span><span class="lv-ttl">${T("src.live")}</span>${chips}`;
    } else {
      bar.className = "live-bar is-est";
      bar.innerHTML = `<iconify-icon icon="lucide:wifi-off" width="16" height="16"></iconify-icon><span class="lv-ttl">${T(state.offline ? "src.offline" : "src.est")}</span>`;
    }

    const fc = r.forecast || [];
    $("fc-card").classList.toggle("hidden", !fc.length);
    if (!fc.length) return;
    const total = Math.round(fc.reduce((a, x) => a + (x.rain_mm || 0), 0));
    const mx = Math.max(10, ...fc.map((x) => x.rain_mm || 0));
    $("fc-total").textContent = total + " mm";
    const w = r.weather || {};
    $("fc-sub").textContent = T("fc.sub", { t: w.temperature_c != null ? Math.round(w.temperature_c) : "—", h: w.humidity_pct != null ? w.humidity_pct : "—", v: w.wind_speed_kmh != null ? Math.round(w.wind_speed_kmh) : "—" });
    $("fc-bars").innerHTML = fc.map((x) => {
      const mm = x.rain_mm || 0;
      const dt = new Date(x.date + "T12:00:00");
      const day = dt.toLocaleDateString(FSI18N.locale, { weekday: "narrow" });
      const lvl = mm >= 10 ? "wet" : mm >= 1 ? "some" : "dry";
      return `<div class="fc-day ${lvl}" title="${Terra.fmtDate(x.date)} · ${mm} mm${x.tmax_c != null ? " · " + Math.round(x.tmax_c) + "°C" : ""}">
        <span class="fc-mm">${mm >= 1 ? Math.round(mm) : ""}</span>
        <span class="fc-col"><i style="height:${Math.max(3, (mm / mx) * 100)}%"></i></span>
        <span class="fc-d">${day}<small>${dt.getDate()}</small></span></div>`;
    }).join("");
  }

  function arc(p0, p1) {
    const cx = 110, cy = 112, r = 88;
    const pt = (p) => { const a = Math.PI * (1 - p / 100); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; };
    const [x0, y0] = pt(p0), [x1, y1] = pt(p1);
    return `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`;
  }
  $("r-seg-low").setAttribute("d", arc(1.5, 38.5));
  $("r-seg-mod").setAttribute("d", arc(41.5, 68.5));
  $("r-seg-high").setAttribute("d", arc(71.5, 98.5));

  function renderRotations() {
    const rots = state.reco.rotations || [];
    const LV = { high: "lvl.high", medium: "lvl.medium", low: "lvl.low" };
    $("rot-tabs").innerHTML = rots.map((ro, i) => `<button type="button" role="tab" data-i="${i}" aria-pressed="${i === state.rot}" aria-selected="${i === state.rot}">${T("rot." + ro.type)}</button>`).join("");
    const ro = rots[state.rot]; if (!ro) return;
    const rk = Terra.riskClass(ro.risk);
    const meter = (lvl) => `<span class="meter m-${lvl}"><i></i><i></i><i></i></span>`;
    $("rot-card").innerHTML = `
      <div class="rot fade-in ${state.rot === 0 ? "is-top" : ""}">
        <div class="kind"><span class="badge ${rk}">${T("rot.risk")} : ${T("risk." + rk)}</span>${state.rot === 0 ? `<span class="top-pill">${T("rot.best")}</span>` : ""}</div>
        <h3 class="rot-name">${ro.name.split("→").map((s) => `<span>${s.trim()}</span>`).join('<iconify-icon icon="lucide:arrow-right" width="16" height="16"></iconify-icon>')}</h3>
        <div class="rot-stats">
          <div><small>${T("rot.water")}</small><b>−${ro.water_saving_pct} %</b></div>
          <div><small>${T("rot.soil")}</small>${meter(ro.soil_benefit)}<b>${T(LV[ro.soil_benefit])}</b></div>
          <div><small>${T("rot.yield")}</small>${meter(ro.yield_potential)}<b>${T(LV[ro.yield_potential])}</b></div>
        </div>
        <p class="why">${ro.reason}</p>
        <div class="rot-steps"><span class="eyebrow">${T("rot.steps")}</span>
          <ol>${(ro.actions || []).map((a) => `<li>${a}</li>`).join("")}</ol>
        </div>
      </div>`;
  }

  /* =====================================================
     Démarrage
     ===================================================== */
  function togglePick(on) {
    state.picking = on;
    $("pick").classList.toggle("is-on", on);
    $("g-pick").classList.toggle("hidden", !on);
    if (spinner && on) spinner.pause();
    if (on && window.matchMedia("(max-width: 999px)").matches) window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function bind() {
    pickIn($("soil"), "soil");
    pickIn($("irr"), "irr");
    pickIn($("prio"), "prio");
    $("crop-suggest").addEventListener("click", (e) => {
      const b = e.target.closest(".sug"); if (!b) return;
      const cur = $("crop").value.trim();
      $("crop").value = cur && !cur.toLowerCase().includes(b.textContent.toLowerCase()) ? `${cur}, ${b.textContent}` : b.textContent;
    });
    $("form").addEventListener("submit", onSubmit);
    $("edit").addEventListener("click", () => { stopTour(); showView("form"); });
    $("ask-card").addEventListener("click", () => window.FSAssistant && FSAssistant.open());
    $("rot-tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-i]"); if (b) { state.rot = +b.dataset.i; renderRotations(); } });
    const toLayer = (e) => {
      const li = e.target.closest("li[data-layer]"); if (!li) return;
      if (e.type === "keydown" && e.key !== "Enter" && e.key !== " ") return;
      stopTour(); showLayer(li.dataset.layer);
      if (!window.matchMedia("(min-width: 1000px)").matches) document.querySelector(".an-globe").scrollIntoView({ behavior: "smooth" });
    };
    $("r-list").addEventListener("click", toLayer);
    $("r-list").addEventListener("keydown", toLayer);
    $("pick").addEventListener("click", () => togglePick(!state.picking));
    $("gps").addEventListener("click", () => {
      if (!navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition(async (p) => {
        const { latitude: lat, longitude: lng } = p.coords;
        setLocation(lat, lng, "");
        $("loc").value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        flyToField(lat, lng);
        const n = await reverse(lat, lng);
        if (n) { state.name = n; $("loc").value = n; $("g-name").textContent = n; }
      }, () => Terra.toast(T("an.not_found")), { enableHighAccuracy: true, timeout: 10000 });
    });
    $("layers").addEventListener("click", (e) => {
      const b = e.target.closest(".layer-btn"); if (!b || b.disabled) return;
      stopTour(); showLayer(b.dataset.layer);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    prefill();
    paintForm();
    bind();
    Terra.apply();
    initMap();
    renderLayerButtons();
    document.body.dataset.view = "form";
    if (state.lat != null) { $("g-name").textContent = state.name || T("home.your_field"); $("g-coords").textContent = Terra.fmtCoords(state.lat, state.lng); }
    else $("g-name").textContent = T("region");
  });

  document.addEventListener("fs:langchange", async () => {
    paintForm();
    renderLayerButtons();
    const tag = document.getElementById("pin-tag"); if (tag) tag.textContent = T("home.your_field");
    paintLegend(state.layer);
    if (!state.reco) return;
    try { const { data } = await FSApi.getRecommendation(FSStore.buildPayload()); state.reco = data; if (window.FSAssistant) FSAssistant.setContext(data); } catch (e) {}
    renderResults();
  });
})();
