/* Field Shift — carte coopérative (résumé imprimable + QR). */
(function () {
  const t = (k) => FSI18N.t(k);
  const RISK_COLOR = { low: "#2E7D32", moderate: "#D9731A", high: "#C0392B" };
  const ACT = { plant_now: "coop.act_plant", wait: "coop.act_wait", switch_crop: "coop.act_switch" };

  function render() {
    const reco = FSStore.getLastReco();
    const field = FSStore.getField();

    document.getElementById("c-coords").textContent =
      field ? `${field.latitude}, ${field.longitude}` : "—";

    if (!reco) {
      document.getElementById("c-water").textContent = t("coop.none");
      return;
    }

    const riskEl = document.getElementById("c-risk");
    riskEl.textContent = t("risk." + reco.risk_level) + " (" + reco.risk_score + ")";
    riskEl.style.background = RISK_COLOR[reco.risk_level];
    document.getElementById("c-risk-txt").textContent = t("risk." + reco.risk_level);

    const wb = reco.water_budget;
    document.getElementById("c-water").textContent =
      `${t("water." + wb.status)} · ${wb.available_water_mm}/${wb.crop_water_need_mm} mm`;

    // Rotation choisie par l'agriculteur (page Rotaciones), sinon la recommandée.
    let chosen = null;
    try { chosen = localStorage.getItem("fs_rotation"); } catch (e) {}
    const rot = reco.rotations.find((r) => r.type === chosen) || reco.rotations[0];
    document.getElementById("c-rotation").textContent = rot ? rot.name : "—";

    const pt = reco.planting_timeline;
    document.getElementById("c-planting").textContent =
      `${t("plant." + pt.recommendation)} · ${FSUI.fmtWindow(pt.best_window)}`;

    const acts = [t(ACT[pt.recommendation] || "coop.act_wait")].concat(rot && rot.actions ? rot.actions.slice(0, 2) : []);
    document.getElementById("c-actions").innerHTML = acts.map((x) => `<span style="display:block">• ${x}</span>`).join("");

    const qr = document.getElementById("qr");
    qr.innerHTML = "";
    if (window.QRCode) new QRCode(qr, { text: window.location.origin, width: 72, height: 72 });
  }

  document.addEventListener("fs:langchange", () => {
    document.getElementById("qr").innerHTML = "";
    render();
  });
  render();
})();
