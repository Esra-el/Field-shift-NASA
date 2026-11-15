/* Field Shift — assistant (chat). Explique la recommandation déjà calculée. */
(function () {
  const t = (k) => FSI18N.t(k);
  const chat = document.getElementById("chat");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("q");

  // Crée une bulle ; renvoie l'élément texte (pour le mettre à jour ensuite).
  function bubble(text, who) {
    let textEl;
    if (who === "user") {
      textEl = document.createElement("div");
      textEl.className = "msg-user";
      textEl.textContent = text;
      chat.appendChild(textEl);
    } else {
      const wrap = document.createElement("div");
      wrap.className = "msg-bot";
      wrap.innerHTML = `<span class="bot-av">${FSUI.icon("solar:stars-bold", 20)}</span>`;
      textEl = document.createElement("div");
      textEl.className = "bub";
      textEl.textContent = text;
      wrap.appendChild(textEl);
      chat.appendChild(wrap);
    }
    chat.scrollTop = chat.scrollHeight;
    return textEl;
  }

  function sources(list) { // (conservé pour compatibilité)
    if (!list || !list.length) return;
    const el = document.createElement("p");
    el.className = "msg-src";
    el.textContent = t("copilot.sources") + " " + list.join(" · ");
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
  }

  function context() {
    const reco = FSStore.getLastReco();
    const chip = document.getElementById("ctx-chip");
    if (!reco) { chip.classList.add("hidden"); document.getElementById("ctx-card").classList.add("hidden"); return; }
    chip.innerHTML = `${FSUI.icon("solar:map-point-linear", 14)} ${FSUI.cropLabel()} · ${t("dash.risk")} ${t("risk." + reco.risk_level)}`;
    chip.classList.remove("hidden");
    // Carte latérale « Ton champ » (même vocabulaire que le tableau de bord)
    const BADGE = { low: "badge-green", moderate: "badge-amber", high: "badge-red" };
    const risk = document.getElementById("ctx-risk");
    risk.className = "badge " + (BADGE[reco.risk_level] || "badge-gray");
    risk.textContent = t("risk." + reco.risk_level);
    document.getElementById("ctx-ring").innerHTML = FSUI.ring(reco.risk_score, FSUI.RISK_COLOR[reco.risk_level], 130, 11);
    document.getElementById("ctx-score").textContent = reco.risk_score;
    const pt = reco.planting_timeline || {};
    document.getElementById("ctx-reco").textContent = pt.recommendation ? t("plant." + pt.recommendation) : "—";
    document.getElementById("ctx-crop").textContent = FSUI.cropLabel();
    const wb = reco.water_budget || {};
    document.getElementById("ctx-water").textContent = wb.status ? t("water." + wb.status) : "—";
    document.getElementById("ctx-window").textContent = FSUI.fmtWindow(pt.best_window);
  }

  function welcome() {
    const reco = FSStore.getLastReco();
    bubble(reco ? (reco.ai_explanation || "") : t("copilot.welcome_nofield"), "bot");
  }

  // Réponse structurée : recommandation · eau · alternatives · actions · sources · limites.
  const SEC_ICON = { reco: "solar:check-circle-bold", water: "solar:waterdrops-bold", alt: "mdi:sprout", actions: "solar:checklist-minimalistic-bold" };
  function structured(el, res) {
    const esc = (x) => String(x == null ? "" : x).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    if (!res.sections) { el.textContent = res.answer; return; }
    el.classList.add("bub-rich");
    el.innerHTML = res.sections.map((sec) => `<div class="sec sec-${sec.key}">
        <p class="sec-h">${FSUI.icon(SEC_ICON[sec.key] || "solar:info-circle-bold", 18)} ${esc(sec.title)}</p>
        ${sec.items ? `<ol>${sec.items.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>` : `<p>${esc(sec.text)}</p>`}
      </div>`).join("") + `
      <div class="sec-foot">
        <p class="sec-h">${FSUI.icon("solar:satellite-bold", 16)} ${esc(res.sources_title || t("copilot.sources"))}</p>
        <div class="src-chips">${(res.sources || []).map((x) => `<span>${esc(x)}</span>`).join("")}</div>
        <p class="xs muted" style="margin-top:.5rem"><b>${esc(res.limitations_title || t("copilot.limits"))} :</b> ${esc(res.limitations)}</p>
        <button type="button" class="badge badge-dark say">${FSUI.icon("solar:volume-loud-bold", 14)} ${t("a11y.listen")}</button>
      </div>`;
    el.querySelector(".say").addEventListener("click", () =>
      FSUI.speak(res.sections.map((x) => `${x.title}. ${x.text || (x.items || []).join(". ")}`).join(" ")));
  }

  async function ask(q) {
    bubble(q, "user");
    input.value = "";
    const thinking = bubble(t("common.loading"), "bot");
    thinking.classList.add("typing");
    const res = await FSApi.askCopilot(q, FSStore.getLastReco());
    thinking.classList.remove("typing");
    structured(thinking, res);
    chat.scrollTop = chat.scrollHeight;
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) ask(q);
  });

  function renderChips() {
    const box = document.getElementById("chips");
    box.innerHTML = "";
    const ICONS = ["solar:waterdrops-bold", "solar:calendar-bold", "mdi:sprout", "solar:shield-check-bold"];
    ["copilot.sugg1", "copilot.sugg2", "copilot.sugg3", "copilot.sugg4"].forEach((k, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.innerHTML = `${FSUI.icon(ICONS[i], 18)} <span>${t(k)}</span>`;
      b.addEventListener("click", () => ask(t(k)));
      box.appendChild(b);
    });
    const ex = document.getElementById("example-q");
    if (ex) { ex.querySelector("span").textContent = t("copilot.example"); ex.onclick = () => ask(t("copilot.example")); }
  }

  context();
  welcome();
  renderChips();
  document.addEventListener("fs:langchange", () => { renderChips(); context(); });
})();
