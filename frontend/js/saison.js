/* Field Shift — page Saison : fenêtre de semis, calendrier de la culture, pluie normale par mois, épisodes secs. */
(function () {
  const T = Terra.t;
  const $ = (id) => document.getElementById(id);
  FSI18N.extend({
    fr: {
      "s.window": "Fenêtre de semis", "s.basis.now": "Le sol est déjà humide et de la pluie arrive.", "s.basis.forecast": "D'après la pluie prévue par Open-Meteo.",
      "s.basis.season": "D'après le retour des pluies dans la normale NASA.", "s.basis.default": "Estimation.",
      "s.in_days": "dans {n} jours", "s.today": "à partir d'aujourd'hui",
      "s.focus": "Priorité de la semaine", "s.cal": "Calendrier de la culture", "s.cal_sub": "{crop} · semis, croissance, floraison, récolte",
      "s.months": "Pluie normale par mois", "s.months_sub": "Moyenne NASA POWER 1981-2020 à votre parcelle. En vert : les mois de votre cycle.",
      "s.dry": "Périodes sèches à surveiller", "s.dry_none": "Aucune période sèche marquée pendant votre cycle.",
      "s.dry.forecast": "Prévue par la météo", "s.dry.normal": "Mois sec habituel", "s.today_mark": "Aujourd'hui",
    },
    en: {
      "s.window": "Planting window", "s.basis.now": "The soil is already moist and rain is coming.", "s.basis.forecast": "Based on Open-Meteo's rain forecast.",
      "s.basis.season": "Based on the return of rains in the NASA normal.", "s.basis.default": "Estimate.",
      "s.in_days": "in {n} days", "s.today": "from today",
      "s.focus": "Priority of the week", "s.cal": "Crop calendar", "s.cal_sub": "{crop} · planting, growth, flowering, harvest",
      "s.months": "Normal rain per month", "s.months_sub": "NASA POWER 1981-2020 average at your field. In green: the months of your cycle.",
      "s.dry": "Dry periods to watch", "s.dry_none": "No marked dry period during your cycle.",
      "s.dry.forecast": "Forecast by the weather", "s.dry.normal": "Usual dry month", "s.today_mark": "Today",
    },
    it: {
      "s.window": "Finestra di semina", "s.basis.now": "Il suolo è già umido e arriva la pioggia.", "s.basis.forecast": "In base alla pioggia prevista da Open-Meteo.",
      "s.basis.season": "In base al ritorno delle piogge nella normale NASA.", "s.basis.default": "Stima.",
      "s.in_days": "tra {n} giorni", "s.today": "da oggi",
      "s.focus": "Priorità della settimana", "s.cal": "Calendario della coltura", "s.cal_sub": "{crop} · semina, crescita, fioritura, raccolto",
      "s.months": "Pioggia normale per mese", "s.months_sub": "Media NASA POWER 1981-2020 sul tuo campo. In verde: i mesi del tuo ciclo.",
      "s.dry": "Periodi secchi da tenere d'occhio", "s.dry_none": "Nessun periodo secco marcato durante il ciclo.",
      "s.dry.forecast": "Previsto dal meteo", "s.dry.normal": "Mese secco abituale", "s.today_mark": "Oggi",
    },
  });
  const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  const STAGE_ICON = { planting: "lucide:sprout", growing: "lucide:leaf", flowering: "lucide:flower-2", harvest: "lucide:wheat" };
  const FOCUS_ICON = { prepare_soil: "lucide:shovel", soil_cover: "lucide:shovel", monitor_rain: "lucide:cloud-rain", consider_rotation: "lucide:refresh-cw", resilient_rotation: "lucide:refresh-cw", plant_now: "lucide:sprout", prepare_planting: "lucide:sprout" };
  const FOCUS_KEY = { soil_cover: "prepare_soil", resilient_rotation: "consider_rotation", prepare_planting: "plant_now" };
  const day = (iso) => new Date(iso + "T12:00:00");

  function render(r) {
    const pt = r.planting_timeline || {};
    const [a, b] = String(pt.best_window || "").split("→").map((s) => s.trim());
    const inDays = a ? Math.round((day(a) - new Date()) / 864e5) : null;
    $("s-window").innerHTML = `<span class="pg-kicker light">${T("s.window")}</span>
      <h2 class="pg-window">${Terra.fmtWindow(pt.best_window)}</h2>
      <p class="pg-when">${inDays != null && inDays > 0 ? T("s.in_days", { n: inDays }) : T("s.today")}</p>
      <span class="d-pill ${Terra.plClass(pt.recommendation) === "ok" ? "" : Terra.plClass(pt.recommendation)}">${T("pl." + pt.recommendation)}</span>
      <p class="pg-reason">${pt.reason || ""}</p>
      <small class="pg-basis">${T("s.basis." + (pt.basis || "default"))}</small>`;

    let f = FOCUS_KEY[r.week_focus] || r.week_focus;
    if (!T("focus." + f) || T("focus." + f) === "focus." + f) f = "monitor_rain";
    $("s-focus").innerHTML = `<span class="pg-kicker">${T("s.focus")}</span>
      <div class="pg-focus"><span class="pg-ic"><iconify-icon icon="${FOCUS_ICON[r.week_focus] || "lucide:cloud-rain"}" width="22" height="22"></iconify-icon></span>
      <div><b>${T("focus." + f)}</b><p class="pg-muted">${T("focus.why." + f)}</p></div></div>`;

    // Calendrier : du mois courant jusqu'après la récolte
    const stages = (r.season && r.season.stages) || [];
    const dry = (r.season && r.season.dry_spells) || [];
    const now = new Date();
    const lastEnd = stages.length ? day(stages[stages.length - 1].end) : new Date(now.getFullYear(), now.getMonth() + 6, 1);
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    const months = Math.min(14, Math.max(6, (lastEnd.getFullYear() - start.getFullYear()) * 12 + lastEnd.getMonth() - start.getMonth() + 1));
    const end = new Date(start.getFullYear(), start.getMonth() + months, 1);
    const pct = (d) => Math.max(0, Math.min(100, ((d - start) / (end - start)) * 100));
    const crop = Terra.cropLabel(FSStore.getProfile() || {});
    const head = Array.from({ length: months }, (_, i) => new Date(start.getFullYear(), start.getMonth() + i, 1)
      .toLocaleDateString(FSI18N.locale, { month: "short" }).replace(".", ""));
    $("s-cal").innerHTML = `<header class="pg-ch"><div><h2>${T("s.cal")}</h2><p class="pg-muted">${T("s.cal_sub", { crop })}</p></div></header>
      <div class="pg-cal" style="--m:${months}">
        <div class="pg-cal-head"><span></span>${head.map((m) => `<span>${m}</span>`).join("")}</div>
        ${stages.map((s) => { const l = pct(day(s.start)), w = Math.max(1.5, pct(day(s.end)) - l); return `
          <div class="pg-cal-row"><span class="lab"><iconify-icon icon="${STAGE_ICON[s.stage]}" width="18" height="18"></iconify-icon>${T("stage." + s.stage)}</span>
          <div class="trk"><span class="seg ${s.stage}" style="left:${l}%;width:${w}%" title="${Terra.fmtDate(s.start)} – ${Terra.fmtDate(s.end)}"></span></div></div>`; }).join("")}
        ${dry.length ? `<div class="pg-cal-row"><span class="lab"><iconify-icon icon="lucide:sun" width="18" height="18"></iconify-icon>${T("stage.dry")}</span>
          <div class="trk">${dry.map((d) => { const l = pct(day(d.start)); return `<span class="seg dry ${d.level}" style="left:${l}%;width:${Math.max(1.5, pct(day(d.end)) - l)}%"></span>`; }).join("")}</div></div>` : ""}
        <div class="pg-cal-today" style="left:calc(var(--lab) + (100% - var(--lab)) * ${pct(now) / 100})"><b>${T("s.today_mark")}</b></div>
      </div>`;

    // Pluie normale par mois (12 mois, en commençant par le mois courant)
    const rn = r.rain_normal_monthly;
    if (rn) {
      const cycle = new Set();
      stages.forEach((s) => { for (let d = day(s.start); d <= day(s.end); d.setDate(d.getDate() + 10)) cycle.add(d.getMonth()); });
      const idx = Array.from({ length: 12 }, (_, i) => (now.getMonth() + i) % 12);
      const vals = idx.map((m) => rn[MONTHS[m]] || 0);
      const labels = idx.map((m) => new Date(2026, m, 1).toLocaleDateString(FSI18N.locale, { month: "short" }).replace(".", ""));
      $("s-months").innerHTML = `<h2>${T("s.months")}</h2><p class="pg-muted">${T("s.months_sub")}</p>
        ${FSPage.bars(vals, labels, { unit: " mm", h: 170, hi: 0, cls: (v, i) => (cycle.has(idx[i]) ? "cyc" : "off") })}`;
    } else { $("s-months").innerHTML = `<h2>${T("s.months")}</h2><p class="pg-muted">${T("pg.none")}</p>`; }

    $("s-dry").innerHTML = `<h2>${T("s.dry")}</h2>${dry.length ? `<ul class="pg-list pg-dry">${dry.map((d) => `
      <li><span class="pg-lvl ${d.level}"></span><div><b>${Terra.fmtDate(d.start)} – ${Terra.fmtDate(d.end)}</b><small>${T("s.dry." + (d.source || "forecast"))} · ${T("risk." + Terra.riskClass(d.level))}</small></div></li>`).join("")}</ul>`
      : `<p class="pg-muted">${T("s.dry_none")}</p>`}`;
  }

  FSPage.start(render);
})();
