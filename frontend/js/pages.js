/* Field Shift — éléments communs aux pages Eau, Saison, Rotations et Mon compte. */
(function () {
  const T = Terra.t;
  FSI18N.extend({
    fr: {
      "pg.water.k": "Budget d'eau", "pg.water.h": "Eau", "pg.water.s": "Ce dont votre culture a besoin, et ce qu'elle va recevoir.",
      "pg.season.k": "Calendrier", "pg.season.h": "Saison", "pg.season.s": "Quand semer, comment la culture avance, et les mois à surveiller.",
      "pg.rot.k": "Plan de cultures", "pg.rot.h": "Rotations", "pg.rot.s": "Trois façons d'enchaîner vos cultures, classées selon votre priorité.",
      "ac.k": "Profil",
      "pg.src": "Données : NASA POWER, NASA MODIS, Open-Meteo · mises à jour {d}", "pg.src_old": "Dernière analyse enregistrée sur l'appareil",
      "pg.loading": "Chargement des données de votre parcelle…", "pg.none": "Pas encore d'analyse.", "pg.go": "Lancer une analyse",
      "pg.mm": "{n} mm", "pg.days": "{n} j",
    },
    en: {
      "pg.water.k": "Water budget", "pg.water.h": "Water", "pg.water.s": "What your crop needs, and what it is going to get.",
      "pg.season.k": "Calendar", "pg.season.h": "Season", "pg.season.s": "When to plant, how the crop progresses, and the months to watch.",
      "pg.rot.k": "Crop plan", "pg.rot.h": "Rotations", "pg.rot.s": "Three ways to sequence your crops, ranked by your priority.",
      "ac.k": "Profile",
      "pg.src": "Data: NASA POWER, NASA MODIS, Open-Meteo · updated {d}", "pg.src_old": "Last analysis saved on this device",
      "pg.loading": "Loading your field data…", "pg.none": "No analysis yet.", "pg.go": "Run an analysis",
      "pg.mm": "{n} mm", "pg.days": "{n} d",
    },
    it: {
      "pg.water.k": "Bilancio idrico", "pg.water.h": "Acqua", "pg.water.s": "Di cosa ha bisogno la tua coltura e cosa riceverà.",
      "pg.season.k": "Calendario", "pg.season.h": "Stagione", "pg.season.s": "Quando seminare, come avanza la coltura e i mesi da tenere d'occhio.",
      "pg.rot.k": "Piano colturale", "pg.rot.h": "Rotazioni", "pg.rot.s": "Tre modi di alternare le colture, ordinati secondo la tua priorità.",
      "ac.k": "Profilo",
      "pg.src": "Dati: NASA POWER, NASA MODIS, Open-Meteo · aggiornati {d}", "pg.src_old": "Ultima analisi salvata sul dispositivo",
      "pg.loading": "Caricamento dei dati del tuo campo…", "pg.none": "Nessuna analisi per ora.", "pg.go": "Avvia un'analisi",
      "pg.mm": "{n} mm", "pg.days": "{n} g",
    },
  });

  function paintPlace() {
    const el = document.getElementById("pg-place-name");
    if (!el) return;
    const p = Terra.getPlace(), u = FSAuth.user() || {};
    el.textContent = (p && p.name) || [u.region, u.country].filter(Boolean).join(", ") || T("home.example");
  }
  function paintSrc(r) {
    const el = document.getElementById("pg-src");
    if (!el || !r) return;
    el.textContent = r.live && r.fetched_at
      ? T("pg.src", { d: new Date(r.fetched_at).toLocaleString(FSI18N.locale, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) })
      : T("pg.src_old");
  }

  window.FSPage = {
    T,
    /* Graphique en barres SVG simple (valeurs, étiquettes, classe par barre). */
    bars(vals, labels, opts) {
      const o = Object.assign({ h: 150, unit: "", cls: () => "", hi: -1 }, opts || {});
      const n = vals.length, mx = Math.max(1, ...vals);
      const W = 100 / n;
      return `<div class="pg-bars" style="--n:${n};height:${o.h}px">${vals.map((v, i) => `
        <div class="pg-bar ${o.cls(v, i)} ${i === o.hi ? "hi" : ""}" title="${labels[i]} · ${Math.round(v)}${o.unit}">
          <em>${v >= 1 ? Math.round(v) : ""}</em><span><i style="height:${Math.max(2, (v / mx) * 100)}%"></i></span><small>${labels[i]}</small></div>`).join("")}</div>`;
    },
    empty(id) {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `<div class="pg-empty"><p>${T("pg.none")}</p><a class="d-btn-lime" href="/globo.html">${T("pg.go")}</a></div>`;
    },
    start(render) {
      paintPlace();
      FSReco.on((r) => { paintPlace(); if (r) { paintSrc(r); render(r); } });
      document.addEventListener("fs:user", paintPlace);
      FSReco.start();
    },
  };
})();
