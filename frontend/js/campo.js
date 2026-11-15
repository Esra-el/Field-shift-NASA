/* Field Shift — sélection de la parcelle : point OU polygone (+ surface). */
(function () {
  const t = (k) => FSI18N.t(k);
  const DEFAULT = { lat: 14.8, lon: -90.5 };
  const saved = FSStore.getField();
  const start = saved ? { lat: saved.latitude, lon: saved.longitude } : DEFAULT;

  // Textes des outils de dessin (Leaflet.draw) dans la langue courante.
  const DRAW_TXT = {
    fr: { polygon: "Dessiner la parcelle", marker: "Poser un point", start: "Clique pour commencer le contour.", cont: "Clique pour continuer le contour.", end: "Clique sur le premier point pour fermer.", point: "Clique sur la carte pour poser le point.", finish: "Terminer", cancel: "Annuler", undo: "Effacer le dernier point", remove: "Supprimer" },
    en: { polygon: "Draw the field", marker: "Drop a point", start: "Click to start drawing the boundary.", cont: "Click to continue the boundary.", end: "Click the first point to close.", point: "Click the map to drop the point.", finish: "Finish", cancel: "Cancel", undo: "Delete last point", remove: "Delete" },
    it: { polygon: "Disegna il campo", marker: "Posiziona un punto", start: "Clicca per iniziare il contorno.", cont: "Clicca per continuare il contorno.", end: "Clicca sul primo punto per chiudere.", point: "Clicca sulla mappa per posizionare il punto.", finish: "Fine", cancel: "Annulla", undo: "Elimina l'ultimo punto", remove: "Elimina" },
  };
  function localizeDraw() {
    const x = DRAW_TXT[FSI18N.lang] || DRAW_TXT.fr, d = L.drawLocal.draw;
    d.toolbar.buttons.polygon = x.polygon;
    d.toolbar.buttons.marker = x.marker;
    d.toolbar.actions.text = x.cancel; d.toolbar.actions.title = x.cancel;
    d.toolbar.finish.text = x.finish; d.toolbar.finish.title = x.finish;
    d.toolbar.undo.text = x.undo; d.toolbar.undo.title = x.undo;
    d.handlers.polygon.tooltip = { start: x.start, cont: x.cont, end: x.end };
    d.handlers.marker.tooltip.start = x.point;
    L.drawLocal.edit.toolbar.buttons.remove = x.remove;
  }
  localizeDraw();

  const map = L.map("map").setView([start.lat, start.lon], saved ? 15 : 7);
  const BASES = {
    plan: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }),
    sat: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Imagery © Esri" }),
  };
  let base = "sat";
  BASES.sat.addTo(map);
  document.querySelectorAll("#base-seg button").forEach((b) => b.addEventListener("click", () => {
    map.removeLayer(BASES[base]);
    base = b.dataset.base;
    BASES[base].addTo(map);
    document.querySelectorAll("#base-seg button").forEach((x) => x.classList.toggle("is-active", x === b));
  }));

  const drawn = new L.FeatureGroup().addTo(map);
  const coordsEl = document.getElementById("coords");
  const areaEl = document.getElementById("area");
  let pointMarker = null;

  // Le libellé « aucune parcelle » est traduit ; une fois une parcelle choisie,
  // on retire data-i18n pour que le changement de langue ne l'efface pas.
  function setCoords(text) { coordsEl.removeAttribute("data-i18n"); coordsEl.textContent = text; }
  function clearCoords() { coordsEl.setAttribute("data-i18n", "field.none"); coordsEl.textContent = t("field.none"); }
  function showArea(ha) {
    if (ha == null) { areaEl.classList.add("hidden"); return; }
    areaEl.textContent = `${t("field.area")} : ${Number(ha).toFixed(2)} ha`;
    areaEl.classList.remove("hidden");
  }

  // Tuiles de la carte latérale (lat / lon / surface / type) — style tableau de bord.
  function syncTiles() {
    const f = FSStore.getField();
    const set = (id, v) => { document.getElementById(id).textContent = v; };
    set("t-lat", f ? f.latitude.toFixed(4) : "—");
    set("t-lon", f ? f.longitude.toFixed(4) : "—");
    set("t-area", f && f.area_ha != null ? `${Number(f.area_ha).toFixed(2)} ha` : "—");
    const badge = document.getElementById("mode-badge");
    badge.textContent = !f ? "—" : t(f.polygon ? "field.mode_poly" : "field.mode_point");
    badge.className = "badge " + (f ? "badge-green" : "badge-gray");
    FSUI.stepper(document.getElementById("steps"), 1);
  }

  function savePoint(lat, lon) {
    const la = +lat.toFixed(4), lo = +lon.toFixed(4);
    drawn.clearLayers();
    if (!pointMarker) {
      pointMarker = L.marker([la, lo], { draggable: true }).addTo(map);
      pointMarker.on("dragend", (e) => { const p = e.target.getLatLng(); savePoint(p.lat, p.lng); });
    } else {
      pointMarker.setLatLng([la, lo]);
    }
    setCoords(`${la}, ${lo}`);
    showArea(null);
    FSStore.setField({ latitude: la, longitude: lo, area_ha: null, polygon: null });
    syncTiles();
  }

  function savePolygon(layer) {
    if (pointMarker) { map.removeLayer(pointMarker); pointMarker = null; }
    const latlngs = layer.getLatLngs()[0];
    const c = layer.getBounds().getCenter();
    const ha = L.GeometryUtil.geodesicArea(latlngs) / 10000;
    setCoords(`${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}`);
    showArea(ha);
    FSStore.setField({
      latitude: +c.lat.toFixed(4), longitude: +c.lng.toFixed(4), area_ha: +ha.toFixed(2),
      polygon: latlngs.map((p) => [+p.lat.toFixed(5), +p.lng.toFixed(5)]),
    });
    syncTiles();
  }

  map.addControl(new L.Control.Draw({
    position: "topleft",
    draw: { polygon: { shapeOptions: { color: "#CDE8F6", weight: 3 } }, marker: true,
      polyline: false, rectangle: false, circle: false, circlemarker: false },
    edit: { featureGroup: drawn, edit: false, remove: true },
  }));

  let drawing = false;
  map.on(L.Draw.Event.DRAWSTART, () => { drawing = true; });
  map.on(L.Draw.Event.DRAWSTOP, () => { setTimeout(() => { drawing = false; }, 50); });
  map.on(L.Draw.Event.CREATED, (e) => {
    if (e.layerType === "polygon") { drawn.clearLayers(); drawn.addLayer(e.layer); savePolygon(e.layer); }
    else { const p = e.layer.getLatLng(); savePoint(p.lat, p.lng); }
  });
  map.on(L.Draw.Event.DELETED, () => {
    if (pointMarker) { map.removeLayer(pointMarker); pointMarker = null; }
    FSStore.setField(null); clearCoords(); showArea(null); syncTiles();
  });

  // Clic simple (hors dessin) = poser/déplacer un point.
  map.on("click", (e) => { if (!drawing) savePoint(e.latlng.lat, e.latlng.lng); });

  // Restauration
  if (saved && saved.polygon && saved.polygon.length) {
    const poly = L.polygon(saved.polygon.map((p) => L.latLng(p[0], p[1])), { color: "#CDE8F6", weight: 3 });
    drawn.addLayer(poly);
    map.fitBounds(poly.getBounds(), { padding: [30, 30] });
    setCoords(`${saved.latitude}, ${saved.longitude}`);
    showArea(saved.area_ha);
  } else if (saved) {
    savePoint(saved.latitude, saved.longitude);
  }

  // Recherche d'un lieu (OpenStreetMap Nominatim) — seulement quand l'utilisateur clique sur « Buscar ».
  const results = document.getElementById("search-results");
  function goTo(lat, lon, zoom) { map.setView([lat, lon], zoom || 15); savePoint(lat, lon); results.classList.add("hidden"); }
  document.getElementById("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = document.getElementById("search-q").value.trim();
    if (!q) return;
    results.classList.remove("hidden");
    results.innerHTML = `<div class="sr-item muted">${t("common.loading")}</div>`;
    try {
      const url = "https://nominatim.openstreetmap.org/search?format=json&limit=5&q=" + encodeURIComponent(q) + "&accept-language=" + FSI18N.lang;
      const list = await (await fetch(url)).json();
      if (!list.length) { results.innerHTML = `<div class="sr-item muted">${t("field.search_none")}</div>`; return; }
      results.innerHTML = list.map((r, i) => `<button type="button" class="sr-item" data-i="${i}">${FSUI.icon("solar:map-point-bold", 18)}<span>${r.display_name}</span></button>`).join("");
      results.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
        const r = list[+b.dataset.i]; goTo(+r.lat, +r.lon, 15);
      }));
    } catch (err) {
      results.innerHTML = `<div class="sr-item muted">${t("field.search_none")}</div>`;
    }
  });
  document.getElementById("locate-btn").addEventListener("click", () => {
    if (!navigator.geolocation) { FSUI.toast(t("field.locate_fail")); return; }
    navigator.geolocation.getCurrentPosition((pos) => goTo(pos.coords.latitude, pos.coords.longitude, 16),
      () => FSUI.toast(t("field.locate_fail"), "solar:gps-bold"), { timeout: 10000 });
  });
  // « Analizar mi parcela » : directement au résultat si le profil est déjà rempli.
  if (FSStore.getProfile()) document.getElementById("use-btn").href = "/panel.html";

  document.addEventListener("fs:langchange", () => {
    localizeDraw();
    const f = FSStore.getField();
    showArea(f ? f.area_ha : null);
    syncTiles();
  });
  syncTiles();
})();
