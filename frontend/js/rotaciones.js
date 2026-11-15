/* Field Shift — plans de rotation : 3 cartes comparables + actions à cocher + plan choisi. */
(function () {
  const t = (k) => FSI18N.t(k);
  const $ = (id) => document.getElementById(id);
  const LVL_BADGE = { low: "badge-green", moderate: "badge-amber", high: "badge-red" };
  const LVL_ICON = { low: "solar:check-circle-bold", moderate: "solar:danger-circle-bold", high: "solar:danger-triangle-bold" };
  const N = { low: 1, medium: 2, high: 3 };
  const TYPE_ICON = { safest: "solar:shield-check-bold", balanced: "solar:scale-bold", highest_yield: "mdi:corn" };
  const CROP_ICON = [["frijol|bean|haricot|fagiol|legum", "mdi:seed-outline"], ["sorg", "mdi:grass"], ["maíz|maize|maïs|mais", "mdi:corn"],
    ["cobertura|cover|couverture|copertura|descanso|fallow|jachère|maggese", "solar:leaf-bold"], ["cereal|céréale|cereale", "mdi:barley"]];

  function cropIcon(name) {
    const n = name.toLowerCase();
    const hit = CROP_ICON.find(([re]) => new RegExp(re).test(n));
    return hit ? hit[1] : "mdi:sprout";
  }
  function dots(level) {
    const n = N[level] || 1;
    return `<span class="dots" aria-label="${t("lvl3." + level)}">${[1, 2, 3].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</span>`;
  }
  function getChosen() { try { return localStorage.getItem("fs_rotation"); } catch (e) { return null; } }
  function getDone() { try { return JSON.parse(localStorage.getItem("fs_rot_done") || "{}"); } catch (e) { return {}; } }

  function render(d, res) {
    const field = FSStore.getField() || {};
    $("rot-field").innerHTML = `${FSUI.icon("mdi:sprout", 16)} ${FSI18N.f("dash.field_of", { crop: FSUI.cropLabel().toLowerCase() })} · ${t("risk." + d.risk_level)} ${d.risk_score}/100${field.area_ha ? " · " + field.area_ha + " ha" : ""}`;
    FSUI.stamp($("rot-stamp"), res, d);
    const chosen = getChosen() || (d.rotations[0] && d.rotations[0].type);
    const done = getDone();

    $("rot-list").innerHTML = d.rotations.map((r, i) => {
      const steps = r.name.split(/\s*→\s*/);
      const chain = steps.length > 1
        ? `<div class="chain">${steps.map((x) => `<span class="step">${FSUI.icon(cropIcon(x), 22)}<span>${x}</span></span>`).join(`<span class="to">${FSUI.icon("solar:arrow-right-linear", 18)}</span>`)}</div>`
        : `<div class="chain"><span class="step">${FSUI.icon(cropIcon(r.name), 22)}<span>${r.name}</span></span></div>`;
      const actions = (r.actions || []).map((a, j) => {
        const id = `${r.type}-${j}`;
        return `<label class="todo"><input type="checkbox" data-id="${id}"${done[id] ? " checked" : ""} /><span class="box">${FSUI.icon("solar:check-read-linear", 18)}</span><span>${a}</span></label>`;
      }).join("");
      const isChosen = r.type === chosen;
      return `<article class="card rot-card${i === 0 ? " is-reco" : ""}${isChosen ? " is-chosen" : ""}" data-type="${r.type}">
        <div class="card-head">
          <span class="badge ${i === 0 ? "badge-dark" : "badge-gray"}">${FSUI.icon(TYPE_ICON[r.type] || "mdi:sprout", 16)} ${t("rot." + r.type)}</span>
          <span class="badge ${LVL_BADGE[r.risk] || "badge-gray"}">${FSUI.icon(LVL_ICON[r.risk], 15)} ${t("rot.risk")} ${t("risk." + r.risk).toLowerCase()}</span>
        </div>
        ${i === 0 ? `<p class="reco-flag">${FSUI.icon("solar:star-bold", 16)} ${t("rot.recommended")}</p>` : ""}
        ${chain}
        <div class="rot-metrics">
          <div><span class="m-l">${FSUI.icon("solar:waterdrops-bold", 18)} ${t("rot.water_saving")}</span>
            <div class="m-bar"><div style="width:${Math.min(100, (r.water_saving_pct || 0) * 2.5)}%"></div></div><b>${r.water_saving_pct != null ? "−" + r.water_saving_pct + " %" : t("lvl3." + r.water_saving)}</b></div>
          <div><span class="m-l">${FSUI.icon("solar:leaf-bold", 18)} ${t("rot.soil")}</span>${dots(r.soil_benefit)}<b>${t("lvl3." + r.soil_benefit)}</b></div>
          <div><span class="m-l">${FSUI.icon("mdi:barley", 18)} ${t("rot.yield")}</span>${dots(r.yield_potential || "medium")}<b>${t("lvl3." + (r.yield_potential || "medium"))}</b></div>
        </div>
        <details class="why" ${i === 0 ? "open" : ""}><summary>${FSUI.icon("solar:info-circle-bold", 18)} ${t("rot.why")}</summary><p>${r.reason}</p></details>
        <p class="sci-h" style="margin:.9rem 0 .5rem;font-size:1rem">${t("rot.actions")}</p>
        <div class="todos">${actions}</div>
        <button class="btn ${isChosen ? "btn-dark" : "btn-light"} btn-block choose" data-type="${r.type}" style="margin-top:1rem">
          ${FSUI.icon(isChosen ? "solar:check-circle-bold" : "solar:hand-shake-linear", 20)} ${t(isChosen ? "rot.chosen" : "rot.choose")}</button>
      </article>`;
    }).join("");

    $("rot-list").querySelectorAll(".todo input").forEach((cb) => cb.addEventListener("change", () => {
      const all = getDone(); all[cb.dataset.id] = cb.checked;
      try { localStorage.setItem("fs_rot_done", JSON.stringify(all)); } catch (e) {}
    }));
    $("rot-list").querySelectorAll(".choose").forEach((b) => b.addEventListener("click", () => {
      try { localStorage.setItem("fs_rotation", b.dataset.type); } catch (e) {}
      const r = d.rotations.find((x) => x.type === b.dataset.type);
      FSUI.toast(`${t("rot.chosen")} : ${r ? r.name : ""}`, "solar:check-circle-bold");
      render(d, res);
    }));

    FSUI.setSpeech(() => [t("rot.title") + "."].concat(d.rotations.map((r) =>
      `${t("rot." + r.type)} : ${r.name}. ${t("rot.risk")} ${t("risk." + r.risk)}. ${r.reason}`)).join(" "));
  }

  FSUI.dataPage(render);
})();
