/* Field Shift — profil de l'agriculteur. */
(function () {
  const state = { crop: "maize", irrigation: "none", priority: "save_water" };
  const saved = FSStore.getProfile();
  const soil = document.getElementById("soil");
  if (saved) {
    state.crop = saved.crop || "maize";
    state.irrigation = saved.irrigation_level || (saved.irrigation ? "available" : "none");
    state.priority = saved.priority || "save_water";
    if (state.crop === "cover_crop") state.crop = "maize";
    if (saved.soil_type && saved.soil_type !== "loam") soil.value = saved.soil_type;
  }

  const groups = [
    { sel: ".crop-btn", match: (b) => b.dataset.crop === state.crop, set: (b) => { state.crop = b.dataset.crop; } },
    { sel: ".irr-btn", match: (b) => b.dataset.irr === state.irrigation, set: (b) => { state.irrigation = b.dataset.irr; } },
    { sel: ".prio-btn", match: (b) => b.dataset.prio === state.priority, set: (b) => { state.priority = b.dataset.prio; } },
  ];
  const PRIO = { save_water: "profile.prio.water", balanced: "profile.prio.balanced", max_yield: "profile.prio.yield", protect_soil: "profile.prio.soil", food_security: "profile.prio.food" };
  function paint() {
    groups.forEach((g) => document.querySelectorAll(g.sel).forEach((b) => b.classList.toggle("is-active", g.match(b))));
    // Carte de synthèse (tuiles façon tableau de bord)
    const t = FSI18N.t;
    document.getElementById("s-crop").textContent = t("crop." + state.crop);
    document.getElementById("s-soil").textContent = t("soil." + soil.value);
    document.getElementById("s-irr").textContent = t("profile.irr." + state.irrigation);
    document.getElementById("s-prio").textContent = t(PRIO[state.priority]);
    const f = FSStore.getField();
    document.querySelector("#hero-parcel span").textContent = f
      ? `${t("dash.parcel")} · ${f.latitude}, ${f.longitude}${f.area_ha ? " · " + f.area_ha + " ha" : ""}`
      : t("field.none");
    FSUI.stepper(document.getElementById("steps"), 2);
  }
  soil.addEventListener("change", paint);
  document.addEventListener("fs:langchange", paint);
  groups.forEach((g) => document.querySelectorAll(g.sel).forEach((b) =>
    b.addEventListener("click", () => { g.set(b); paint(); })));
  paint();

  document.getElementById("submit-btn").addEventListener("click", () => {
    FSStore.setProfile({ crop: state.crop, soil_type: soil.value, irrigation: state.irrigation !== "none", irrigation_level: state.irrigation, priority: state.priority });
    window.location.href = FSStore.getField() ? "/panel.html" : "/campo.html";
  });
})();
