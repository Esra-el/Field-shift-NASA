/* Field Shift — assistant IA flottant (bouton en bas à droite + panneau de discussion).
   Contexte : la dernière analyse (window.FSAssistant.setContext) ou celle gardée hors ligne. */
(function () {
  FSI18N.extend({
    fr: { "as.open": "Assistant", "as.close": "Fermer", "as.need": "Bonjour. Lancez d'abord l'analyse de votre parcelle : je pourrai ensuite vous répondre avec vos vraies données.", "as.cta": "Analyser ma parcelle", "as.new": "Nouveau" },
    en: { "as.open": "Assistant", "as.close": "Close", "as.need": "Hi. First run the analysis of your field: then I can answer with your real data.", "as.cta": "Analyze my field", "as.new": "New" },
    it: { "as.open": "Assistente", "as.close": "Chiudi", "as.need": "Ciao. Avvia prima l'analisi del tuo campo: poi potrò risponderti con i tuoi dati reali.", "as.cta": "Analizza il mio campo", "as.new": "Nuovo" },
  });
  const T = (k, v) => Terra.t(k, v);
  let ctx = null, open = false, greeted = false;
  let fab, panel, log, quick, form, input;

  function getContext() {
    const reco = ctx || FSStore.getLastReco();
    if (!reco) return null;
    const p = FSStore.getProfile() || {};
    return Object.assign({}, reco, { profile: { crop: Terra.cropLabel(p), resources: p.resources || "" } });
  }

  function build() {
    fab = document.createElement("button");
    fab.className = "fab"; fab.type = "button";
    fab.setAttribute("aria-haspopup", "dialog"); fab.setAttribute("aria-expanded", "false");
    fab.innerHTML = `<iconify-icon icon="lucide:sparkles" width="24" height="24"></iconify-icon><span class="fab-label" data-t="as.open"></span><i class="fab-dot hidden"></i>`;

    panel = document.createElement("section");
    panel.className = "chat-panel"; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-modal", "false"); panel.setAttribute("aria-labelledby", "as-title");
    panel.innerHTML = `
      <header class="cp-head">
        <span class="cp-avatar"><iconify-icon icon="lucide:sparkles" width="20" height="20"></iconify-icon></span>
        <div class="cp-titles"><h2 id="as-title" data-t="chat.title"></h2><p data-t="chat.sub"></p></div>
        <button type="button" class="cp-close" data-t-aria="as.close"><iconify-icon icon="lucide:x" width="22" height="22"></iconify-icon></button>
      </header>
      <div class="cp-log" aria-live="polite"></div>
      <div class="cp-foot">
        <div class="quick"></div>
        <form class="chat-form"><input class="input" autocomplete="off" /><button class="icon-btn is-on" type="submit" data-t-aria="chat.send"><iconify-icon icon="lucide:send" width="20" height="20"></iconify-icon></button></form>
      </div>`;
    document.body.append(panel, fab);
    log = panel.querySelector(".cp-log"); quick = panel.querySelector(".quick");
    form = panel.querySelector("form"); input = form.querySelector("input");

    fab.addEventListener("click", () => toggle(!open));
    panel.querySelector(".cp-close").addEventListener("click", () => toggle(false));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && open) toggle(false); });
    quick.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) ask(b.textContent); });
    form.addEventListener("submit", (e) => { e.preventDefault(); const q = input.value.trim(); if (q) { input.value = ""; ask(q); } });
    input.addEventListener("focus", syncKeyboard);
    input.addEventListener("blur", () => setTimeout(syncKeyboard, 50));
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", syncKeyboard);
      window.visualViewport.addEventListener("scroll", syncKeyboard);
    }
    paintStatic();
    Terra.apply(panel); Terra.apply(fab);
  }

  function paintStatic() {
    quick.innerHTML = ["chat.q1", "chat.q2", "chat.q3", "chat.q4"].map((k) => `<button type="button">${T(k)}</button>`).join("");
    input.placeholder = T("chat.ph");
  }

  function toEnd() {
    // Défiler après le reflow, sinon le dernier message apparaît à moitié coupé.
    requestAnimationFrame(() => { if (log) log.scrollTop = log.scrollHeight; });
  }

  function bubble(text, who) {
    const b = document.createElement("div");
    b.className = "bubble " + who;
    b.textContent = text;
    log.appendChild(b);
    toEnd();
    return b;
  }

  function greet() {
    if (greeted) return;
    greeted = true;
    if (getContext()) { bubble(T("chat.hello"), "ai"); return; }
    const b = bubble(T("as.need"), "ai");
    if (document.body.dataset.page !== "analyse") {
      const a = document.createElement("a"); a.href = "/globo.html"; a.className = "bubble-cta"; a.textContent = T("as.cta");
      b.appendChild(a);
    }
  }

  // Garde le champ de saisie et le dernier message au-dessus du clavier mobile :
  // le panneau est collé en bas (bottom:0) alors que le clavier recouvre le bas
  // de l'écran. On relève le panneau de la hauteur du clavier et on limite sa
  // hauteur à la zone réellement visible (visualViewport) — sinon le message
  // qu'on vient d'envoyer apparaît à moitié caché derrière le clavier.
  function syncKeyboard() {
    if (!panel) return;
    const vv = window.visualViewport;
    const narrow = window.matchMedia("(max-width: 640px)").matches;
    const sub = panel.querySelector(".cp-titles p");
    if (open && narrow && vv) {
      const kb = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
      // Clavier ouvert => la zone visible est courte. On fait remplir au panneau
      // toute la zone visible (au-dessus du clavier) et on replie l'en-tête + les
      // suggestions, sinon ils mangent presque toute la hauteur et le message
      // qu'on vient d'envoyer se retrouve coupé / poussé hors de vue.
      const compact = vv.height < 560;
      panel.style.bottom = kb + "px";
      if (compact) { panel.style.height = (vv.height - 8) + "px"; panel.style.maxHeight = "none"; }
      else { panel.style.height = ""; panel.style.maxHeight = (vv.height - 8) + "px"; }
      panel.classList.toggle("cp-compact", compact);
      if (quick) quick.style.display = compact ? "none" : "";
      if (sub) sub.style.display = compact ? "none" : "";
      toEnd();
    } else {
      panel.style.bottom = ""; panel.style.height = ""; panel.style.maxHeight = "";
      panel.classList.remove("cp-compact");
      if (quick) quick.style.display = "";
      if (sub) sub.style.display = "";
    }
  }

  function toggle(on) {
    open = on;
    panel.classList.toggle("is-open", on);
    fab.classList.toggle("is-open", on);
    fab.setAttribute("aria-expanded", on);
    fab.querySelector(".fab-dot").classList.add("hidden");
    document.body.classList.toggle("chat-open", on);
    syncKeyboard();
    if (on) { greet(); setTimeout(() => { input.focus({ preventScroll: true }); syncKeyboard(); }, 250); }
  }

  async function ask(q) {
    bubble(q, "me");
    const typing = bubble(T("chat.typing"), "ai typing");
    const res = await FSApi.askCopilot(q, getContext());
    typing.classList.remove("typing");
    typing.textContent = (res && res.answer) || T("copilot.offline");
    log.scrollTop = log.scrollHeight;
  }

  window.FSAssistant = {
    setContext(reco) {
      const first = !ctx;
      ctx = reco;
      if (fab && first && !open) fab.querySelector(".fab-dot").classList.remove("hidden");
      if (greeted && first) { log.innerHTML = ""; greeted = false; if (open) greet(); }
    },
    open: () => toggle(true),
    ask: (q) => { toggle(true); ask(q); },
  };

  document.addEventListener("DOMContentLoaded", build);
  document.addEventListener("fs:langchange", () => { if (panel) { paintStatic(); Terra.apply(panel); Terra.apply(fab); } });
})();
