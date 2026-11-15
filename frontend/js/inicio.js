/* Field Shift — Accueil : globe d'ambiance + 3 chiffres + calendrier + focus de la semaine. */
(function () {
  const T = Terra.t;
  let reco = null;

  /* ---------- Globe d'ambiance : vraie planète satellite qui tourne, puis se pose sur la parcelle ---------- */
  function heroGlobe(lat, lng) {
    const el = document.getElementById("hero-globe");
    if (!window.maplibregl || !Terra.hasWebGL()) return;
    const map = new maplibregl.Map({
      container: el, style: Terra.satStyle(false), center: [lng + 70, lat - 5], zoom: el.clientWidth < 500 ? 0.9 : 1.35,
      interactive: false, attributionControl: { compact: true }, renderWorldCopies: false,
    });
    map.on("load", () => {
      const d = document.createElement("div");
      d.className = "pin";
      d.innerHTML = `<span class="dot"><i></i></span>`;
      new maplibregl.Marker({ element: d }).setLngLat([lng, lat]).addTo(map);
      // Arrivée : la planète tourne jusqu'à la parcelle, puis continue doucement.
      map.easeTo({ center: [lng, lat], duration: 3600, easing: (t) => 1 - Math.pow(1 - t, 3) });
      map.once("moveend", () => Terra.spinGlobe(map, { speed: 2.5 }));
    });
    new ResizeObserver(() => map.resize()).observe(el);
  }

  /* ---------- 3 chiffres ---------- */
  FSI18N.extend({
    fr: { "home.photos": "Photos : Wikimedia Commons (domaine public, CC0, CC BY)", "sc.covered": "des besoins en eau couverts", "sc.have": "Disponible", "sc.need": "Besoin", "sc.missing": "Il manque {n} mm d'eau pour finir la saison.", "sc.surplus": "{n} mm de marge : l'eau suffit pour la saison.", "rp.window": "Fenêtre de semis" },
    en: { "home.photos": "Photos: Wikimedia Commons (public domain, CC0, CC BY)", "sc.covered": "of water needs covered", "sc.have": "Available", "sc.need": "Needed", "sc.missing": "{n} mm of water missing to finish the season.", "sc.surplus": "{n} mm to spare: water is enough for the season.", "rp.window": "Planting window" },
    it: { "home.photos": "Foto: Wikimedia Commons (pubblico dominio, CC0, CC BY)", "sc.covered": "del fabbisogno d'acqua coperto", "sc.have": "Disponibile", "sc.need": "Fabbisogno", "sc.missing": "Mancano {n} mm d'acqua per finire la stagione.", "sc.surplus": "{n} mm di margine: l'acqua basta per la stagione.", "rp.window": "Finestra di semina" },
  });

  /* Arc de cercle (jauge) : de a0 à a1 en « points » 0–100. */
  function arc(p0, p1) {
    const cx = 110, cy = 112, r = 88;
    const pt = (p) => { const a = Math.PI * (1 - p / 100); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; };
    const [x0, y0] = pt(p0), [x1, y1] = pt(p1);
    return `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`;
  }
  document.getElementById("seg-low").setAttribute("d", arc(1.5, 38.5));
  document.getElementById("seg-mod").setAttribute("d", arc(41.5, 68.5));
  document.getElementById("seg-high").setAttribute("d", arc(71.5, 98.5));

  function paintStats(r) {
    const rc = Terra.riskClass(r.risk_level);
    const rb = document.getElementById("s-risk-badge");
    rb.className = "badge " + rc; rb.textContent = T("risk." + rc);
    document.getElementById("s-risk").textContent = r.risk_score;
    const ang = -90 + Math.max(0, Math.min(100, r.risk_score)) * 1.8;
    requestAnimationFrame(() => setTimeout(() => { document.getElementById("needle").style.transform = `rotate(${ang}deg)`; }, 80));
    document.querySelectorAll(".semi-seg").forEach((p) => p.classList.toggle("is-on", p.classList.contains({ low: "low", moderate: "mod", high: "high" }[rc])));
    document.getElementById("s-risk-d").textContent = T("risk." + rc + ".d");

    const wb = r.water_budget || {};
    const need = wb.crop_water_need_mm || 0, have = wb.available_water_mm || 0;
    const max = Math.max(need, have, 1);
    const wcls = Terra.wsClass(wb.status);
    const wbB = document.getElementById("s-water-badge");
    wbB.className = "badge " + wcls; wbB.textContent = T("ws." + wb.status);
    document.getElementById("s-water").textContent = wb.coverage_pct;
    document.getElementById("s-have").textContent = have + " mm";
    document.getElementById("s-need").textContent = need + " mm";
    const bar = document.getElementById("s-water-bar");
    bar.className = "wbar-fill " + wcls;
    bar.style.width = "0";
    requestAnimationFrame(() => setTimeout(() => { bar.style.width = (have / max) * 100 + "%"; }, 80));
    document.getElementById("s-water-goal").style.left = (need / max) * 100 + "%";
    const gap = need - have;
    document.getElementById("s-water-d").textContent = gap > 0 ? T("sc.missing", { n: gap }) : T("sc.surplus", { n: -gap });

  }

  /* ---------- Calendrier ---------- */
  const STAGE_ICON = { planting: "lucide:sprout", growing: "lucide:leaf", flowering: "lucide:flower-2", harvest: "lucide:wheat" };
  function paintCalendar(r) {
    const cal = document.getElementById("cal");
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const months = 6;
    const end = new Date(now.getFullYear(), now.getMonth() + months, 1);
    const span = end - start;
    const pct = (iso) => Math.max(0, Math.min(100, ((new Date(iso + "T12:00:00") - start) / span) * 100));
    const loc = FSI18N.locale;

    let head = `<div class="cal-months" style="--cols:${months}"><span></span>`;
    for (let i = 0; i < months; i++) {
      const d = new Date(start.getFullYear(), start.getMonth() + i, 1);
      head += `<span class="${i === 0 ? "is-now" : ""}">${d.toLocaleDateString(loc, { month: "short" }).replace(".", "")}</span>`;
    }
    head += `</div>`;

    const stages = (r.season && r.season.stages) || [];
    const rows = stages.map((s) => {
      const l = pct(s.start), w = Math.max(1.5, pct(s.end) - l);
      return `<div class="cal-row"><span class="lab"><iconify-icon icon="${STAGE_ICON[s.stage]}" width="18" height="18"></iconify-icon>${T("stage." + s.stage)}</span>
        <div class="cal-track"><span class="cal-seg ${s.stage}" style="left:${l}%;width:${w}%" title="${Terra.fmtDate(s.start)} – ${Terra.fmtDate(s.end)}"></span></div></div>`;
    }).join("");
    const dry = (r.season && r.season.dry_spells) || [];
    const dryRow = dry.length ? `<div class="cal-row"><span class="lab"><iconify-icon icon="lucide:triangle-alert" width="18" height="18" style="color:var(--warn)"></iconify-icon>${T("stage.dry")}</span>
      <div class="cal-track">${dry.map((d) => { const l = pct(d.start); return `<span class="cal-seg dry ${d.level}" style="left:${l}%;width:${Math.max(1.5, pct(d.end) - l)}%"></span>`; }).join("")}</div></div>` : "";

    const today = pct(now.toISOString().slice(0, 10));
    cal.style.setProperty("--cols", months);
    cal.innerHTML = head + `<div style="position:relative">${rows}${dryRow}
      <div style="position:absolute;inset:0 0 0 var(--lab-w,110px);pointer-events:none" class="cal-today-wrap"><span class="cal-today" style="left:${today}%"><b>${T("today")}</b></span></div></div>`;
    const lab = window.matchMedia("(max-width:560px)").matches ? "74px" : "110px";
    cal.querySelector(".cal-today-wrap").style.setProperty("--lab-w", lab);

    document.getElementById("cal-legend").innerHTML = [
      ["planting", "var(--forest-600)"], ["growing", "var(--leaf-300)"], ["flowering", "#E9C46A"], ["harvest", "var(--soil-500)"],
    ].map(([k, c]) => `<span><i style="background:${c}"></i>${T("stage." + k)}</span>`).join("") +
      (dry.length ? `<span><i style="background:repeating-linear-gradient(135deg,var(--warn-bg) 0 3px,#F6D9B6 3px 6px);border:1px solid var(--warn)"></i>${T("stage.dry")}</span>` : "");
  }

  /* ---------- Focus ---------- */
  const FOCUS_IMG = { prepare_soil: "mulch.jpg", monitor_rain: "rain.jpg", consider_rotation: "cornfield.jpg", plant_now: "seedlings.jpg" };
  const FOCUS_ICON = { prepare_soil: "lucide:shovel", monitor_rain: "lucide:cloud-rain", consider_rotation: "lucide:refresh-cw", plant_now: "lucide:sprout" };
  function paintFocus(r) {
    let f = r.week_focus;
    if (!FOCUS_ICON[f]) f = r.planting_timeline && r.planting_timeline.recommendation === "plant_now" ? "plant_now" : "monitor_rain";
    document.getElementById("focus-text").textContent = T("focus." + f);
    document.getElementById("focus-why").textContent = T("focus.why." + f);
    document.getElementById("focus-icon").setAttribute("icon", FOCUS_ICON[f]);
    document.getElementById("focus-card").style.setProperty("--bg", `url('/img/photos/${FOCUS_IMG[f]}')`);
    const pt = r.planting_timeline || {};
    document.getElementById("focus-win").innerHTML = `<iconify-icon icon="lucide:calendar-days" width="16" height="16"></iconify-icon>${T("rp.window")} : <b>${Terra.fmtWindow(pt.best_window)}</b>`;
  }

  function paintField() {
    const place = Terra.getPlace();
    const p = FSStore.getProfile();
    document.getElementById("field-name").textContent = place && place.name ? place.name : T("home.example");
    document.getElementById("field-crop").textContent = Terra.cropLabel(p || {});
  }

  function paintAll() { paintField(); if (reco) { paintStats(reco); paintCalendar(reco); paintFocus(reco); } }

  async function load() {
    paintField();
    const payload = FSStore.buildPayload();
    heroGlobe(payload.latitude, payload.longitude);
    try {
      const { data } = await FSApi.getRecommendation(payload);
      reco = data;
    } catch (e) {
      reco = FSStore.getLastReco();
      if (!reco) { Terra.toast(T("an.error")); return; }
    }
    paintAll();
    if (window.FSAssistant && reco) FSAssistant.setContext(reco);
  }

  document.addEventListener("DOMContentLoaded", load);
  document.addEventListener("fs:langchange", async () => {
    paintAll();
    try { const { data } = await FSApi.getRecommendation(FSStore.buildPayload()); reco = data; paintAll(); } catch (e) {}
  });
})();
