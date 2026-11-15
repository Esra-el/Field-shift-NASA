/* Field Shift — page Rotations : 3 plans de cultures, classés selon la priorité choisie. */
(function () {
  const T = Terra.t;
  const $ = (id) => document.getElementById(id);
  FSI18N.extend({
    fr: {
      "r.prio": "Ma priorité :", "r.p.save_water": "Économiser l'eau", "r.p.max_yield": "Récolter plus", "r.p.protect_soil": "Protéger le sol",
      "r.p.balanced": "Équilibre", "r.p.food_security": "Nourrir la famille",
      "r.best": "Conseillée pour vous", "r.water": "Eau économisée", "r.soil": "Santé du sol", "r.yield": "Rendement", "r.risk": "Risque",
      "r.steps": "Ce qu'il faut faire", "r.compare": "Comparer les plans et votre rotation actuelle", "r.plan": "Plan", "r.updating": "Mise à jour…",
    },
    en: {
      "r.prio": "My priority:", "r.p.save_water": "Save water", "r.p.max_yield": "Harvest more", "r.p.protect_soil": "Protect the soil",
      "r.p.balanced": "Balance", "r.p.food_security": "Feed the family",
      "r.best": "Recommended for you", "r.water": "Water saved", "r.soil": "Soil health", "r.yield": "Yield", "r.risk": "Risk",
      "r.steps": "What to do", "r.compare": "Compare the plans and your current rotation", "r.plan": "Plan", "r.updating": "Updating…",
    },
    it: {
      "r.prio": "La mia priorità:", "r.p.save_water": "Risparmiare acqua", "r.p.max_yield": "Raccogliere di più", "r.p.protect_soil": "Proteggere il suolo",
      "r.p.balanced": "Equilibrio", "r.p.food_security": "Nutrire la famiglia",
      "r.best": "Consigliato per te", "r.water": "Acqua risparmiata", "r.soil": "Salute del suolo", "r.yield": "Resa", "r.risk": "Rischio",
      "r.steps": "Cosa fare", "r.compare": "Confronta i piani e la tua rotazione attuale", "r.plan": "Piano", "r.updating": "Aggiornamento…",
    },
  });
  const PRIOS = ["save_water", "max_yield", "protect_soil", "balanced", "food_security"];
  const LV = { high: 3, medium: 2, low: 1, moderate: 2 };
  const IMG = (w) => {
    w = String(w).toLowerCase();
    if (/ma[iï]s|maize|corn/.test(w)) return "cornfield.jpg";
    if (/couvert|cover|copertura|jachère|fallow|maggese|mucuna|vesce|vetch|veccia/.test(w)) return "mulch.jpg";
    if (/haricot|bean|fagiol|légum|legum|legume|niébé|cowpea|arachide|groundnut|soja|soy|pois|chickpea|cece|fève|faba|fava|lentil/.test(w)) return "seedlings.jpg";
    if (/sorgh|sorgo|mil|miglio|millet|céréale|cereal|cereale|blé|wheat|frumento|orge|barley|orzo|tournesol|sunflower|girasole/.test(w)) return "rows.jpg";
    return "seedlings.jpg";
  };
  const dots = (lvl) => `<span class="pg-dots">${[1, 2, 3].map((i) => `<i class="${i <= (LV[lvl] || 0) ? "on" : ""}"></i>`).join("")}</span>`;

  function paintPrio() {
    const cur = (FSStore.getProfile() || {}).priority || "balanced";
    $("r-prio").innerHTML = `<span>${T("r.prio")}</span>` + PRIOS.map((p) => `<button type="button" data-p="${p}" aria-pressed="${p === cur}">${T("r.p." + p)}</button>`).join("");
  }
  $("r-prio").addEventListener("click", async (e) => {
    const b = e.target.closest("button[data-p]");
    if (!b || b.getAttribute("aria-pressed") === "true") return;
    const p = Object.assign({ crop: "maize", soil_type: "sandy_loam", irrigation: false, irrigation_level: "none" }, FSStore.getProfile() || {}, { priority: b.dataset.p });
    FSStore.setProfile(p);
    paintPrio();
    $("r-cards").classList.add("is-loading");
    await FSReco.refresh();
    $("r-cards").classList.remove("is-loading");
  });

  function render(r) {
    paintPrio();
    const rots = r.rotations || [];
    $("r-cards").innerHTML = rots.map((ro, i) => {
      const steps = String(ro.name).split(/→|->/).map((s) => s.replace(/\(.*\)/, "").trim()).filter(Boolean);
      const rk = Terra.riskClass(ro.risk);
      return `<article class="pg-card pg-rot ${i === 0 ? "best" : ""}">
        <header>${i === 0 ? `<span class="d-pill">${T("r.best")}</span>` : `<span class="pg-kicker">${T("r.plan")} ${i + 1}</span>`}<span class="badge ${rk}">${T("r.risk")} : ${T("risk." + rk)}</span></header>
        <h2>${T("rot." + ro.type)}</h2>
        <div class="pg-seq">${steps.map((s) => `<span><i style="background-image:url('/img/photos/${IMG(s)}')"></i>${s}</span>`).join('<iconify-icon icon="lucide:arrow-right" width="16" height="16"></iconify-icon>')}</div>
        <dl class="pg-metrics">
          <div><dt>${T("r.water")}</dt><dd><b>−${ro.water_saving_pct ?? { high: 35, medium: 20, low: 5 }[ro.water_saving]} %</b></dd></div>
          <div><dt>${T("r.soil")}</dt><dd>${dots(ro.soil_benefit)}</dd></div>
          <div><dt>${T("r.yield")}</dt><dd>${dots(ro.yield_potential)}</dd></div>
        </dl>
        <p class="pg-muted">${ro.reason || ""}</p>
        ${[["rot.evidence", ro.evidence], ["rot.gaps", ro.gaps], ["rot.review", ro.local_review]].filter(([, xs]) => xs && xs.length)
          .map(([k, xs]) => `<div class="pg-steps"><span class="pg-kicker">${T(k)}</span><ul>${xs.map((x) => `<li>${x}</li>`).join("")}</ul></div>`).join("")}
        ${(ro.actions || []).length ? `<div class="pg-steps"><span class="pg-kicker">${T("r.steps")}</span><ol>${ro.actions.map((a) => `<li>${a}</li>`).join("")}</ol></div>` : ""}
      </article>`;
    }).join("");

    $("r-compare").innerHTML = `<h2>${T("r.compare")}</h2>
      <div class="pg-table-wrap"><table class="pg-table"><thead><tr><th></th>${rots.map((ro) => `<th>${T("rot." + ro.type)}</th>`).join("")}</tr></thead>
      <tbody>
        <tr><th>${T("r.water")}</th>${rots.map((ro) => `<td>−${ro.water_saving_pct ?? "?"} %</td>`).join("")}</tr>
        <tr><th>${T("r.soil")}</th>${rots.map((ro) => `<td>${dots(ro.soil_benefit)}</td>`).join("")}</tr>
        <tr><th>${T("r.yield")}</th>${rots.map((ro) => `<td>${dots(ro.yield_potential)}</td>`).join("")}</tr>
        <tr><th>${T("r.risk")}</th>${rots.map((ro) => `<td><span class="badge ${Terra.riskClass(ro.risk)}">${T("risk." + Terra.riskClass(ro.risk))}</span></td>`).join("")}</tr>
      </tbody></table></div>
      <p class="pg-muted" style="margin-top:12px">${T("rot.disclaimer")}</p>`;
  }

  FSPage.start(render);
})();
