/* Field Shift — page Eau : besoin vs disponible, d'où vient l'eau, pluie prévue, évaporation, pluie passée. */
(function () {
  const T = Terra.t;
  const $ = (id) => document.getElementById(id);
  FSI18N.extend({
    fr: {
      "w.cov": "du besoin en eau couvert", "w.need": "Besoin de la culture", "w.have": "Eau disponible", "w.gap": "Il manque {n} mm",
      "w.surplus": "{n} mm de marge", "w.parts": "D'où vient l'eau", "w.rain": "Pluie attendue sur le cycle", "w.soil": "Réserve du sol",
      "w.irr": "Irrigation", "w.parts_note": "Pluie : prévision 16 jours puis normale NASA. Réserve : humidité du sol actuelle.",
      "w.fc": "Pluie prévue · 16 jours", "w.fc_rainy": "{n} jours de pluie", "w.fc_dry": "Plus longue période sèche : {n} jours",
      "w.et": "Évaporation (ET₀)", "w.et_txt": "Chaque jour, le sol et les plantes perdent en moyenne {n} mm d'eau.", "w.et_hot": "Chaleur forte prévue : jusqu'à {t} °C.",
      "w.past": "Pluie des 8 dernières semaines", "w.past_vs": "{p} % de la normale", "w.normal": "Normale", "w.actual": "Tombée",
      "w.advice": "Notre conseil",
      "w.adv.enough_water": "L'eau suffit pour la saison. Gardez les résidus sur le sol pour garder l'humidité.",
      "w.adv.risky": "L'eau est juste : semez moins dense, paillez le sol, et préférez une culture qui demande moins d'eau.",
      "w.adv.not_enough_water": "Il manque beaucoup d'eau : attendez la pluie ou choisissez sorgho, mil ou haricot.",
    },
    en: {
      "w.cov": "of the water need covered", "w.need": "Crop need", "w.have": "Water available", "w.gap": "{n} mm missing",
      "w.surplus": "{n} mm to spare", "w.parts": "Where the water comes from", "w.rain": "Rain expected over the cycle", "w.soil": "Soil reserve",
      "w.irr": "Irrigation", "w.parts_note": "Rain: 16-day forecast then NASA normal. Reserve: current soil moisture.",
      "w.fc": "Rain forecast · 16 days", "w.fc_rainy": "{n} rainy days", "w.fc_dry": "Longest dry spell: {n} days",
      "w.et": "Evaporation (ET₀)", "w.et_txt": "Each day, soil and plants lose {n} mm of water on average.", "w.et_hot": "Strong heat expected: up to {t} °C.",
      "w.past": "Rain over the last 8 weeks", "w.past_vs": "{p}% of normal", "w.normal": "Normal", "w.actual": "Fallen",
      "w.advice": "Our advice",
      "w.adv.enough_water": "Water is enough for the season. Keep crop residue on the soil to hold moisture.",
      "w.adv.risky": "Water is tight: plant less densely, mulch the soil and prefer a crop that needs less water.",
      "w.adv.not_enough_water": "A lot of water is missing: wait for rain or choose sorghum, millet or beans.",
    },
    it: {
      "w.cov": "del fabbisogno d'acqua coperto", "w.need": "Fabbisogno della coltura", "w.have": "Acqua disponibile", "w.gap": "Mancano {n} mm",
      "w.surplus": "{n} mm di margine", "w.parts": "Da dove arriva l'acqua", "w.rain": "Pioggia attesa sul ciclo", "w.soil": "Riserva del suolo",
      "w.irr": "Irrigazione", "w.parts_note": "Pioggia: previsione a 16 giorni poi normale NASA. Riserva: umidità attuale del suolo.",
      "w.fc": "Pioggia prevista · 16 giorni", "w.fc_rainy": "{n} giorni di pioggia", "w.fc_dry": "Periodo secco più lungo: {n} giorni",
      "w.et": "Evaporazione (ET₀)", "w.et_txt": "Ogni giorno suolo e piante perdono in media {n} mm d'acqua.", "w.et_hot": "Caldo forte previsto: fino a {t} °C.",
      "w.past": "Pioggia delle ultime 8 settimane", "w.past_vs": "{p}% della normale", "w.normal": "Normale", "w.actual": "Caduta",
      "w.advice": "Il nostro consiglio",
      "w.adv.enough_water": "L'acqua basta per la stagione. Lascia i residui sul suolo per trattenere l'umidità.",
      "w.adv.risky": "L'acqua è al limite: semina meno fitto, pacciama il suolo e preferisci una coltura meno esigente.",
      "w.adv.not_enough_water": "Manca molta acqua: aspetta la pioggia o scegli sorgo, miglio o fagioli.",
    },
  });

  function render(r) {
    const wb = r.water_budget || {};
    const need = wb.crop_water_need_mm || 0, have = wb.available_water_mm || 0, max = Math.max(need, have, 1);
    const cls = Terra.wsClass(wb.status);
    const gap = need - have;

    $("w-hero").innerHTML = `
      <div class="pg-hero-top"><span class="d-pill ${cls === "ok" ? "" : cls}">${T("ws." + wb.status)}</span></div>
      <div class="pg-big"><b>${wb.coverage_pct ?? "—"}</b><em>%</em></div>
      <p class="pg-muted">${T("w.cov")}</p>
      <div class="pg-meter"><span class="fill ${cls}" style="width:${(have / max) * 100}%"></span><span class="goal" style="left:${(need / max) * 100}%"></span></div>
      <dl class="pg-kv"><div><dt>${T("w.have")}</dt><dd>${have} mm</dd></div><div><dt>${T("w.need")}</dt><dd>${need} mm</dd></div>
        <div><dt>&nbsp;</dt><dd class="${gap > 0 ? "neg" : "pos"}">${gap > 0 ? T("w.gap", { n: gap }) : T("w.surplus", { n: -gap })}</dd></div></dl>`;

    const parts = [["lucide:cloud-rain", "w.rain", wb.expected_rain_mm], ["lucide:layers", "w.soil", wb.soil_water_mm], ["lucide:droplet", "w.irr", wb.irrigation_mm]];
    const tot = parts.reduce((a, p) => a + (p[2] || 0), 0) || 1;
    $("w-parts").innerHTML = `<h2>${T("w.parts")}</h2>
      <div class="pg-stack">${parts.map((p, i) => `<span class="s${i}" style="width:${((p[2] || 0) / tot) * 100}%"></span>`).join("")}</div>
      <ul class="pg-list">${parts.map((p, i) => `<li><span class="dot s${i}"></span><iconify-icon icon="${p[0]}" width="18" height="18"></iconify-icon><span>${T(p[1])}</span><b>${p[2] != null ? p[2] + " mm" : "—"}</b></li>`).join("")}</ul>
      <p class="pg-note">${T("w.parts_note")}</p>`;

    const fc = r.forecast || [];
    if (fc.length) {
      const vals = fc.map((x) => x.rain_mm || 0);
      const labels = fc.map((x) => new Date(x.date + "T12:00:00").toLocaleDateString(FSI18N.locale, { weekday: "short", day: "numeric" }));
      let run = 0, best = 0; vals.forEach((v) => { run = v < 1 ? run + 1 : 0; best = Math.max(best, run); });
      $("w-forecast").innerHTML = `<header class="pg-ch"><h2>${T("w.fc")}</h2><b class="pg-total">${Math.round(vals.reduce((a, b) => a + b, 0))} mm</b></header>
        ${FSPage.bars(vals, labels, { unit: " mm", cls: (v) => (v >= 10 ? "wet" : v >= 1 ? "some" : "dry") })}
        <p class="pg-muted">${T("w.fc_rainy", { n: vals.filter((v) => v >= 1).length })} · ${T("w.fc_dry", { n: best })}</p>`;
      const et = fc.map((x) => x.et0_mm).filter((v) => v != null);
      const avg = et.length ? (et.reduce((a, b) => a + b, 0) / et.length).toFixed(1) : (r.nasa_indicators || {}).evapotranspiration;
      const tmax = Math.max(...fc.map((x) => x.tmax_c || 0));
      $("w-et").innerHTML = `<h2>${T("w.et")}</h2><div class="pg-big sm"><b>${avg}</b><em>mm/j</em></div>
        <p class="pg-muted">${T("w.et_txt", { n: avg })}</p>${tmax >= 34 ? `<p class="pg-warn"><iconify-icon icon="lucide:thermometer-sun" width="18" height="18"></iconify-icon>${T("w.et_hot", { t: Math.round(tmax) })}</p>` : ""}`;
    } else { FSPage.empty("w-forecast"); $("w-et").innerHTML = ""; }

    const s = r.series || {};
    const rain = s.rainfall_mm || [], norm = s.rainfall_normal_mm || [];
    const n = r.nasa_indicators || {};
    const pct = n.rainfall_normal_mm ? Math.round((n.rainfall_60d_mm / n.rainfall_normal_mm) * 100) : null;
    const mx = Math.max(1, ...rain, ...norm);
    $("w-past").innerHTML = `<header class="pg-ch"><h2>${T("w.past")}</h2>${pct != null ? `<b class="pg-total">${T("w.past_vs", { p: pct })}</b>` : ""}</header>
      <div class="pg-pairs">${rain.map((v, i) => `<div><span><i class="a" style="height:${(v / mx) * 100}%"></i><i class="b" style="height:${((norm[i] || 0) / mx) * 100}%"></i></span><small>${(s.labels || [])[i] || ""}</small></div>`).join("")}</div>
      <p class="pg-legend"><span><i class="a"></i>${T("w.actual")}</span><span><i class="b"></i>${T("w.normal")}</span></p>`;

    $("w-advice").innerHTML = `<span class="pg-kicker">${T("w.advice")}</span><p class="pg-adv">${T("w.adv." + wb.status)}</p>
      <a class="pg-link" href="/rotations.html">${T("d.nav.rot")} <iconify-icon icon="lucide:arrow-right" width="16" height="16"></iconify-icon></a>`;
  }

  FSPage.start(render);
})();
