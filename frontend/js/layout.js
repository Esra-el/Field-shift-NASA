/* Field Shift — mise en page de l'espace client + helpers partagés.
   Chaque page déclare <body data-page="..."> et <header id="topbar"></header>.
   Accessibilité (pensée pour les agriculteurs âgés) :
   - taille du texte réglable (Aa : normal / grand / très grand, mémorisée) ;
   - « Écouter » : lit à voix haute le résumé de la page (FSUI.setSpeech) ;
   - aide « ? » : tout élément [data-help="clé"] reçoit une bulle explicative ;
   - barre d'onglets en bas de l'écran sur téléphone (icône + mot). */
(function () {
  const NAV = [
    { id: "home", href: "/index.html", key: "nav.home", icon: "lucide:house" },
    { id: "analyse", href: "/analyse.html", key: "nav.analyse", icon: "lucide:earth" },
    { id: "assistant", href: "/analyse.html#asistente", key: "nav.assistant", icon: "lucide:message-circle" },
    { id: "history", href: "/backtesting.html", key: "nav.backtest", icon: "lucide:history" },
  ];

  /* ---------- Textes : outils d'accessibilité + bulles d'aide ---------- */
  FSI18N.extend({
    es: {
      "a11y.size": "Tamaño del texto", "a11y.size.m": "normal", "a11y.size.l": "grande", "a11y.size.xl": "muy grande",
      "a11y.listen": "Escuchar", "a11y.stop": "Detener", "a11y.help": "Ayuda",
      "a11y.help_on": "Toque un círculo « ? » para ver una explicación sencilla.",
      "a11y.help_off": "Ayuda oculta.", "a11y.no_voice": "La lectura en voz alta no está disponible en este aparato.",
      "a11y.tip": "Consejo: el botón « Aa » agranda el texto y « Escuchar » lee la página en voz alta.",
      "a11y.close": "Cerrar", "a11y.lang": "Idioma", "nav.home_public": "Sitio de Field Shift",
      "help.risk.t": "Riesgo de sequía", "help.risk.d": "Una nota de 0 a 100. Cuanto más alta, más amenaza la falta de agua a su cultivo. Menos de 40: bajo. De 40 a 70: moderado. Más de 70: alto.",
      "help.ndvi.t": "NDVI (vegetación)", "help.ndvi.d": "Medida satelital de qué tan verdes están las plantas, de 0 a 1. Cuanto más cerca de 1, más densa y sana está la vegetación.",
      "help.soil.t": "Humedad del suelo", "help.soil.d": "Cuánta agua hay en la tierra de arriba, medida por el satélite SMAP. Por debajo de 20 %, la tierra está muy seca para sembrar.",
      "help.rain.t": "Lluvia", "help.rain.d": "La lluvia de los últimos 60 días, comparada con un año normal en el mismo lugar.",
      "help.et.t": "Evapotranspiración (ETP)", "help.et.d": "El agua que se pierde cada día: se evapora del suelo y sale por las hojas. Cuanto más calor y sequedad, más alta es.",
      "help.water.t": "Agua para el cultivo", "help.water.d": "Comparamos el agua disponible (lluvia + reserva del suelo + riego) con el agua que su cultivo necesitará hasta la cosecha.",
      "help.window.t": "Ventana de siembra", "help.window.d": "El período de las próximas semanas en que sembrar tiene más probabilidades de éxito: suficiente humedad y lluvia prevista.",
      "help.rotation.t": "Rotación de cultivos", "help.rotation.d": "Cambiar de cultivo de una temporada a otra protege el suelo y el agua. Proponemos 3 planes, del más seguro al de mayor cosecha.",
      "help.health.t": "Salud de la parcela", "help.health.d": "Una nota de 0 a 100 que resume el estado de su parcela: 100 menos el riesgo de sequía.",
      "help.solar.t": "Radiación solar", "help.solar.d": "La energía del sol que llega cada día. Mucho sol y poca agua = la tierra se seca rápido.",
      "help.temp.t": "Temperatura", "help.temp.d": "La temperatura del aire según NASA POWER para su parcela.",
      "help.calendar.t": "Calendario", "help.calendar.d": "Las próximas 6 semanas. La zona marcada muestra el mejor momento para sembrar.",
      "help.backtest.t": "Historial", "help.backtest.d": "Probamos la herramienta con temporadas pasadas para ver si habría avisado antes de las sequías.",
      "help.scan.t": "Vista satelital", "help.scan.d": "Su parcela vista desde el cielo. « NDVI NASA » colorea la vegetación: verde oscuro = plantas fuertes, café = suelo desnudo o seco.",
    },
    fr: {
      "a11y.size": "Taille du texte", "a11y.size.m": "normale", "a11y.size.l": "grande", "a11y.size.xl": "très grande",
      "a11y.listen": "Écouter", "a11y.stop": "Arrêter", "a11y.help": "Aide",
      "a11y.help_on": "Touchez un rond « ? » pour avoir une explication simple.",
      "a11y.help_off": "Aide masquée.", "a11y.no_voice": "La lecture à voix haute n'est pas disponible sur cet appareil.",
      "a11y.tip": "Astuce : le bouton « Aa » agrandit le texte, « Écouter » lit la page à voix haute.",
      "a11y.close": "Fermer", "a11y.lang": "Langue", "nav.home_public": "Site Field Shift",
      "help.risk.t": "Risque de sécheresse", "help.risk.d": "Une note de 0 à 100. Plus elle est haute, plus le manque d'eau menace votre culture. Sous 40 : faible. De 40 à 70 : modéré. Au-dessus de 70 : élevé.",
      "help.ndvi.t": "NDVI (végétation)", "help.ndvi.d": "Mesure satellite de la verdure des plantes, de 0 à 1. Plus c'est proche de 1, plus la végétation est dense et en bonne santé.",
      "help.soil.t": "Humidité du sol", "help.soil.d": "La quantité d'eau dans la terre en surface, mesurée par le satellite SMAP. En dessous de 20 %, la terre est sèche pour semer.",
      "help.rain.t": "Pluie", "help.rain.d": "La pluie tombée ces 60 derniers jours, comparée à une année normale au même endroit.",
      "help.et.t": "Évapotranspiration (ETP)", "help.et.d": "L'eau qui s'en va chaque jour : elle s'évapore du sol et sort des feuilles. Plus il fait chaud et sec, plus elle est forte.",
      "help.water.t": "Budget d'eau", "help.water.d": "On compare l'eau disponible (pluie + réserve du sol) avec l'eau dont votre culture aura besoin jusqu'à la récolte.",
      "help.window.t": "Fenêtre de semis", "help.window.d": "La période des prochaines semaines où semer donne le plus de chances : assez d'eau dans le sol et de pluie annoncée.",
      "help.rotation.t": "Rotation des cultures", "help.rotation.d": "Alterner les cultures d'une saison à l'autre protège le sol et l'eau. Nous proposons 3 plans, du plus sûr au plus productif.",
      "help.health.t": "Santé du champ", "help.health.d": "Une note de 0 à 100 qui résume l'état de votre parcelle : 100 moins le risque de sécheresse.",
      "help.solar.t": "Rayonnement", "help.solar.d": "L'énergie du soleil reçue par jour. Beaucoup de soleil + peu d'eau = la terre sèche vite.",
      "help.temp.t": "Température", "help.temp.d": "La température de l'air relevée par NASA POWER pour votre parcelle.",
      "help.calendar.t": "Calendrier", "help.calendar.d": "Les 6 prochaines semaines. La zone jaune montre la meilleure période pour semer.",
      "help.backtest.t": "Historique", "help.backtest.d": "On rejoue l'outil sur les saisons passées pour vérifier s'il aurait prévenu avant les sécheresses.",
      "help.scan.t": "Vue satellite", "help.scan.d": "Votre parcelle vue du ciel. Le bouton « NDVI NASA » colore la végétation : vert foncé = plantes vigoureuses, brun = sol nu ou sec.",
    },
    en: {
      "a11y.size": "Text size", "a11y.size.m": "normal", "a11y.size.l": "large", "a11y.size.xl": "extra large",
      "a11y.listen": "Listen", "a11y.stop": "Stop", "a11y.help": "Help",
      "a11y.help_on": "Tap a “?” circle to get a simple explanation.",
      "a11y.help_off": "Help hidden.", "a11y.no_voice": "Read-aloud is not available on this device.",
      "a11y.tip": "Tip: the “Aa” button makes text bigger, “Listen” reads the page aloud.",
      "a11y.close": "Close", "a11y.lang": "Language", "nav.home_public": "Field Shift website",
      "help.risk.t": "Drought risk", "help.risk.d": "A score from 0 to 100. The higher it is, the more lack of water threatens your crop. Below 40: low. 40 to 70: moderate. Above 70: high.",
      "help.ndvi.t": "NDVI (vegetation)", "help.ndvi.d": "A satellite measure of how green plants are, from 0 to 1. Closer to 1 means dense, healthy vegetation.",
      "help.soil.t": "Soil moisture", "help.soil.d": "How much water is in the topsoil, measured by the SMAP satellite. Below 20%, the ground is too dry to sow.",
      "help.rain.t": "Rainfall", "help.rain.d": "Rain from the last 60 days, compared with a normal year at the same place.",
      "help.et.t": "Evapotranspiration (ET)", "help.et.d": "Water lost every day: it evaporates from the soil and leaves the plants. The hotter and drier, the higher it is.",
      "help.water.t": "Water budget", "help.water.d": "We compare available water (rain + soil reserve) with the water your crop will need until harvest.",
      "help.window.t": "Planting window", "help.window.d": "The period in the coming weeks when sowing has the best chance: enough water in the soil and rain expected.",
      "help.rotation.t": "Crop rotation", "help.rotation.d": "Changing crops from one season to the next protects soil and water. We suggest 3 plans, from safest to most productive.",
      "help.health.t": "Field health", "help.health.d": "A score from 0 to 100 summing up your plot: 100 minus the drought risk.",
      "help.solar.t": "Solar radiation", "help.solar.d": "Sun energy received per day. Lots of sun + little water = soil dries quickly.",
      "help.temp.t": "Temperature", "help.temp.d": "Air temperature from NASA POWER for your plot.",
      "help.calendar.t": "Calendar", "help.calendar.d": "The next 6 weeks. The yellow area shows the best time to sow.",
      "help.backtest.t": "History", "help.backtest.d": "We replay the tool on past seasons to check whether it would have warned before droughts.",
      "help.scan.t": "Satellite view", "help.scan.d": "Your field seen from the sky. “NASA NDVI” colours vegetation: dark green = vigorous plants, brown = bare or dry soil.",
    },
    it: {
      "a11y.size": "Dimensione testo", "a11y.size.m": "normale", "a11y.size.l": "grande", "a11y.size.xl": "molto grande",
      "a11y.listen": "Ascolta", "a11y.stop": "Ferma", "a11y.help": "Aiuto",
      "a11y.help_on": "Tocca un cerchio «?» per avere una spiegazione semplice.",
      "a11y.help_off": "Aiuto nascosto.", "a11y.no_voice": "La lettura ad alta voce non è disponibile su questo dispositivo.",
      "a11y.tip": "Consiglio: il pulsante «Aa» ingrandisce il testo, «Ascolta» legge la pagina ad alta voce.",
      "a11y.close": "Chiudi", "a11y.lang": "Lingua", "nav.home_public": "Sito Field Shift",
      "help.risk.t": "Rischio siccità", "help.risk.d": "Un punteggio da 0 a 100. Più è alto, più la mancanza d'acqua minaccia la coltura. Sotto 40: basso. Da 40 a 70: moderato. Sopra 70: alto.",
      "help.ndvi.t": "NDVI (vegetazione)", "help.ndvi.d": "Misura satellitare del verde delle piante, da 0 a 1. Più è vicino a 1, più la vegetazione è densa e sana.",
      "help.soil.t": "Umidità del suolo", "help.soil.d": "Quanta acqua c'è nella terra in superficie, misurata dal satellite SMAP. Sotto il 20% la terra è troppo secca per seminare.",
      "help.rain.t": "Pioggia", "help.rain.d": "La pioggia degli ultimi 60 giorni, confrontata con un anno normale nello stesso luogo.",
      "help.et.t": "Evapotraspirazione (ET)", "help.et.d": "L'acqua persa ogni giorno: evapora dal suolo ed esce dalle foglie. Più fa caldo e secco, più è alta.",
      "help.water.t": "Bilancio idrico", "help.water.d": "Confrontiamo l'acqua disponibile (pioggia + riserva del suolo) con l'acqua che servirà alla coltura fino al raccolto.",
      "help.window.t": "Finestra di semina", "help.window.d": "Il periodo delle prossime settimane in cui seminare dà più possibilità: abbastanza acqua nel suolo e pioggia prevista.",
      "help.rotation.t": "Rotazione colturale", "help.rotation.d": "Alternare le colture da una stagione all'altra protegge suolo e acqua. Proponiamo 3 piani, dal più sicuro al più produttivo.",
      "help.health.t": "Salute del campo", "help.health.d": "Un punteggio da 0 a 100 che riassume lo stato del campo: 100 meno il rischio siccità.",
      "help.solar.t": "Radiazione solare", "help.solar.d": "L'energia del sole ricevuta al giorno. Tanto sole + poca acqua = la terra si secca in fretta.",
      "help.temp.t": "Temperatura", "help.temp.d": "La temperatura dell'aria da NASA POWER per il tuo campo.",
      "help.calendar.t": "Calendario", "help.calendar.d": "Le prossime 6 settimane. La zona gialla mostra il periodo migliore per seminare.",
      "help.backtest.t": "Storico", "help.backtest.d": "Rigiochiamo lo strumento sulle stagioni passate per verificare se avrebbe avvisato prima delle siccità.",
      "help.scan.t": "Vista satellite", "help.scan.d": "Il tuo campo visto dal cielo. «NDVI NASA» colora la vegetazione: verde scuro = piante vigorose, marrone = suolo nudo o secco.",
    },
  });
  const t = (k) => FSI18N.t(k);

  // Logo : éventail de feuilles, sur pastille vert citron.
  const LOGO = `<iconify-icon icon="lucide:sprout" width="22" height="22" aria-hidden="true"></iconify-icon>`;

  function icon(name, size) {
    const s = size || 20;
    return `<iconify-icon icon="${name}" width="${s}" height="${s}" aria-hidden="true"></iconify-icon>`;
  }

  /* ---------- Taille du texte ---------- */
  const SIZES = ["m", "l", "xl"];
  function getSize() { try { return localStorage.getItem("fs_size") || "m"; } catch (e) { return "m"; } }
  function applySize(s) {
    if (s === "m") document.documentElement.removeAttribute("data-size");
    else document.documentElement.setAttribute("data-size", s);
  }
  function cycleSize() {
    const next = SIZES[(SIZES.indexOf(getSize()) + 1) % SIZES.length];
    try { localStorage.setItem("fs_size", next); } catch (e) {}
    applySize(next);
    toast(`${t("a11y.size")} : ${t("a11y.size." + next)}`, "lucide:type");
  }
  applySize(getSize());

  /* ---------- Toast ---------- */
  let toastTimer = null;
  function toast(msg, ico) {
    let el = document.getElementById("fs-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "fs-toast"; el.className = "toast"; el.setAttribute("role", "status"); el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.innerHTML = `${icon(ico || "lucide:info", 20)}<span>${msg}</span>`;
    requestAnimationFrame(() => el.classList.add("show"));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 3600);
  }

  /* ---------- Lecture à voix haute ---------- */
  let speechFn = null;
  function setSpeech(fn) { speechFn = fn; }
  function defaultSpeech() {
    const parts = [];
    document.querySelectorAll("[data-speak]").forEach((e) => { if (e.offsetParent !== null && e.innerText.trim()) parts.push(e.innerText.trim()); });
    if (!parts.length) {
      const h = document.querySelector("main h1, .page-hero h1, .page-head h1, h1");
      const sub = document.querySelector(".page-hero .hero-card p:not(.eyebrow), .page-head .sub");
      if (h) parts.push(h.innerText);
      if (sub) parts.push(sub.innerText);
    }
    return parts.join(". ");
  }
  function speaking() { return "speechSynthesis" in window && speechSynthesis.speaking; }
  function speak(text) {
    if (!("speechSynthesis" in window)) { toast(t("a11y.no_voice"), "lucide:volume-x"); return; }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(String(text || "").replace(/\s+/g, " "));
    u.lang = FSI18N.locale; u.rate = 0.9; // un peu plus lent : plus facile à suivre
    const v = speechSynthesis.getVoices().find((x) => x.lang && x.lang.slice(0, 2) === FSI18N.lang);
    if (v) u.voice = v;
    u.onend = u.onerror = () => paintListen(false);
    speechSynthesis.speak(u);
    paintListen(true);
  }
  function toggleListen() {
    if (speaking()) { speechSynthesis.cancel(); paintListen(false); return; }
    speak(speechFn ? speechFn() : defaultSpeech());
  }
  function paintListen(on) {
    const b = document.getElementById("fs-listen");
    if (!b) return;
    b.classList.toggle("is-on", on);
    b.innerHTML = `${icon(on ? "lucide:square" : "lucide:volume-2", 20)}<span class="lbl">${t(on ? "a11y.stop" : "a11y.listen")}</span>`;
    b.setAttribute("aria-label", t(on ? "a11y.stop" : "a11y.listen"));
  }

  /* ---------- Aide « ? » ---------- */
  let pop = null;
  function closeHelp() {
    if (pop) { pop.remove(); pop = null; }
    document.querySelectorAll('.help-btn[aria-expanded="true"]').forEach((b) => b.setAttribute("aria-expanded", "false"));
  }
  function openHelp(btn) {
    const key = btn.dataset.key;
    const was = btn.getAttribute("aria-expanded") === "true";
    closeHelp();
    if (was) return;
    pop = document.createElement("div");
    pop.className = "help-pop"; pop.setAttribute("role", "dialog");
    pop.innerHTML = `<button class="x" aria-label="${t("a11y.close")}">×</button><b>${t("help." + key + ".t")}</b>${t("help." + key + ".d")}
      <div style="margin-top:.6rem"><button class="badge badge-lime" data-say>${icon("lucide:volume-2", 14)} ${t("a11y.listen")}</button></div>`;
    document.body.appendChild(pop);
    const r = btn.getBoundingClientRect();
    const w = pop.offsetWidth;
    const left = Math.max(8, Math.min(window.scrollX + r.left - w / 2 + r.width / 2, window.scrollX + document.documentElement.clientWidth - w - 8));
    pop.style.left = left + "px";
    pop.style.top = window.scrollY + r.bottom + 8 + "px";
    btn.setAttribute("aria-expanded", "true");
    pop.querySelector(".x").addEventListener("click", closeHelp);
    pop.querySelector("[data-say]").addEventListener("click", () => speak(`${t("help." + key + ".t")}. ${t("help." + key + ".d")}`));
  }
  function helpify(root) {
    (root || document).querySelectorAll("[data-help]").forEach((el) => {
      if (el.querySelector(":scope > .help-btn")) return;
      const b = document.createElement("button");
      b.type = "button"; b.className = "help-btn"; b.dataset.key = el.dataset.help; b.textContent = "?";
      b.setAttribute("aria-label", `${t("a11y.help")} : ${t("help." + el.dataset.help + ".t")}`);
      b.setAttribute("aria-expanded", "false");
      b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); openHelp(b); });
      el.appendChild(b);
    });
  }
  function toggleHelpMode() {
    const on = document.body.classList.toggle("help-mode");
    document.getElementById("fs-help").classList.toggle("is-on", on);
    toast(t(on ? "a11y.help_on" : "a11y.help_off"), "lucide:circle-help");
    if (!on) closeHelp();
  }
  document.addEventListener("click", (e) => { if (pop && !pop.contains(e.target) && !e.target.classList.contains("help-btn")) closeHelp(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeHelp(); });
  window.addEventListener("resize", closeHelp);

  /* ---------- Barre du haut + barre d'onglets mobile ---------- */
  function renderTopbar() {
    const host = document.getElementById("topbar");
    if (!host) return;
    let page = document.body.dataset.page || "";
    if (page === "analyse" && location.hash === "#asistente") page = "assistant";
    const reco = FSStore.getLastReco();
    const alert = !!(reco && (reco.risk_components || []).some((c) => c.level === "bad"));
    host.className = "topbar";
    host.innerHTML = `
      <a class="brand" href="/index.html"><span class="brand-mark">${LOGO}</span><span><span data-i18n="app.name"></span><small>NASA · Space Apps</small></span></a>
      <nav class="tabs" aria-label="Navigation">${NAV.map((n) =>
        `<a class="tab${n.id === page ? " is-active" : ""}" href="${n.href}"${n.id === page ? ' aria-current="page"' : ""}>${icon(n.icon, 20)}<span class="tab-lbl" data-i18n="${n.key}"></span></a>`).join("")}</nav>
      <div class="top-right">
        <button class="icon-btn" id="fs-size" aria-label="${t("a11y.size")}" title="${t("a11y.size")}"><span style="font-family:var(--font-head);font-size:1.05rem">A<small style="font-size:.75em">a</small></span></button>
        <button class="icon-btn" id="fs-listen"></button>
        <button class="icon-btn${document.body.classList.contains("help-mode") ? " is-on" : ""}" id="fs-help" aria-label="${t("a11y.help")}" title="${t("a11y.help")}">${icon("lucide:circle-help", 20)}<span class="lbl">${t("a11y.help")}</span></button>
        ${FSI18N.langButton()}
        <a class="user-pill" href="/perfil.html" aria-label="${t("nav.profile")}">
          <span class="av">${icon("lucide:user-round", 18)}</span>
          <span class="who"><b data-i18n="user.name"></b><span data-i18n="user.role"></span></span>
        </a>
        ${alert ? `<a class="icon-btn" href="/analyse.html#alerts" aria-label="${t("alerts.title")}">${icon("lucide:bell-ring")}<span class="dot"></span></a>` : ""}
      </div>`;
    FSI18N.apply(host);
    host.querySelector("#fs-size").addEventListener("click", cycleSize);
    host.querySelector("#fs-listen").addEventListener("click", toggleListen);
    host.querySelector("#fs-help").addEventListener("click", toggleHelpMode);
    paintListen(speaking());

    let bn = document.getElementById("bottom-nav");
    if (!bn) { bn = document.createElement("nav"); bn.id = "bottom-nav"; bn.className = "bottom-nav"; bn.setAttribute("aria-label", "Navigation"); document.body.appendChild(bn); }
    bn.style.setProperty("--n", NAV.length);
    bn.innerHTML = NAV.map((n) => `<a class="${n.id === page ? "is-active" : ""}" href="${n.href}"${n.id === page ? ' aria-current="page"' : ""}>${icon(n.icon, 24)}<span>${t(n.key)}</span></a>`).join("");

    if (!document.getElementById("offline-banner")) {
      const b = document.createElement("div");
      b.id = "offline-banner";
      b.setAttribute("data-i18n", "common.offline");
      document.body.prepend(b);
      FSI18N.apply(b);
    }
  }

  /* ---------- Apparition douce des cartes ---------- */
  function reveal(root) {
    if (!("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }), { threshold: 0.08 });
    (root || document).querySelectorAll(".frame .card:not(.reveal), .frame .hero:not(.reveal), .frame .page-hero:not(.reveal)").forEach((el, i) => {
      if (el.closest(".sticky")) return;
      el.classList.add("reveal");
      el.style.transitionDelay = Math.min(i, 6) * 60 + "ms";
      io.observe(el);
    });
    // Filet de sécurité : jamais de contenu invisible (onglet en arrière-plan, vieux navigateur…).
    setTimeout(() => document.querySelectorAll(".frame .reveal:not(.in)").forEach((el) => el.classList.add("in")), 1200);
  }

  /* ---------- Helpers de données ---------- */
  const RISK_COLOR = { low: "#2F7A4D", moderate: "#E07B24", high: "#C9372C" };

  function ring(score, color, size, stroke) {
    const S = size || 150, W = stroke || 12, r = (S - W) / 2, c = 2 * Math.PI * r;
    const off = c * (1 - Math.max(0, Math.min(100, score)) / 100);
    return `<svg width="${S}" height="${S}" viewBox="0 0 ${S} ${S}" style="transform:rotate(-90deg)" aria-hidden="true">
      <circle cx="${S / 2}" cy="${S / 2}" r="${r}" fill="none" stroke="#EFE8DC" stroke-width="${W}"/>
      <circle class="ring-anim" style="--c:${c}" cx="${S / 2}" cy="${S / 2}" r="${r}" fill="none" stroke="${color}" stroke-width="${W}"
        stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${off}"/></svg>`;
  }

  function parseWindow(str) {
    const m = String(str || "").match(/(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})/);
    return m ? [new Date(m[1] + "T00:00:00"), new Date(m[2] + "T00:00:00")] : null;
  }
  const fmtDay = (d) => d.toLocaleDateString(FSI18N.locale, { weekday: "long", day: "numeric", month: "long" });
  const fmtShort = (d) => d.toLocaleDateString(FSI18N.locale, { day: "numeric", month: "short" });
  const fmtWindow = (str) => { const w = parseWindow(str); return w ? `${fmtShort(w[0])} → ${fmtShort(w[1])}` : (str || "—"); };

  function cropKey() { return (FSStore.getProfile() || {}).crop || "maize"; }
  function cropLabel() { return t("crop." + cropKey()); }

  function stamp(el, res, data) {
    if (!el) return;
    const time = new Date().toLocaleTimeString(FSI18N.locale, { hour: "2-digit", minute: "2-digit" });
    let html = `<span class="mock-chip">${icon("lucide:refresh-cw", 14)} ${t("panel.updated")} ${time}</span>`;
    if (res && res.offline) html += ` <span class="mock-chip">${icon("lucide:cloud-off", 14)} ${t("panel.offline")}</span>`;
    else if (data && data._mock) html += ` <span class="mock-chip">${icon("lucide:flask-conical", 14)} ${t("panel.mock")}</span>`;
    el.innerHTML = html;
  }

  /* Cycle de vie d'une page « données » : garde-fou, chargement, erreur,
     rechargement au changement de langue (les textes serveur sont localisés). */
  function dataPage(render, opts) {
    const o = opts || {};
    if (o.requireField !== false && !FSStore.getField()) { window.location.replace("/analyse.html"); return; }
    const loading = document.getElementById("loading");
    const content = document.getElementById("content");
    async function run() {
      try {
        const res = await FSApi.getRecommendation(FSStore.buildPayload());
        if (loading) loading.classList.add("hidden");
        if (content) content.classList.remove("hidden");
        render(res.data, res);
        renderTopbar();
        helpify();
        reveal();
      } catch (e) {
        if (loading) {
          loading.innerHTML = `<p class="c-red" style="margin-bottom:16px">${t("panel.error")}</p>
            <button class="btn btn-dark" onclick="location.reload()">${t("panel.retry")}</button>`;
        }
      }
    }
    document.addEventListener("fs:langchange", run);
    run();
  }

  /* Fil d'étapes Parcelle → Profil → Tableau de bord.
     current : 1, 2 ou 3 (0 = aucune étape en cours). */
  function stepper(el, current) {
    if (!el) return;
    const steps = [
      { href: "/analyse.html", key: "step.field", done: !!FSStore.getField() },
      { href: "/perfil.html", key: "step.profile", done: !!FSStore.getProfile() },
      { href: "/panel.html", key: "step.dash", done: false },
    ];
    const draw = () => {
      el.innerHTML = steps.map((s, i) => {
        const cls = i + 1 === current ? "is-now" : (s.done ? "is-done" : "");
        const n = s.done && i + 1 !== current ? icon("lucide:check", 12) : i + 1;
        return `<a class="${cls}" href="${s.href}"><span class="n">${n}</span>${t(s.key)}</a>`;
      }).join("");
    };
    draw();
    if (!el.dataset.bound) { el.dataset.bound = "1"; document.addEventListener("fs:langchange", draw); }
  }

  if (window.Chart) {
    Chart.defaults.font.family = '"Plus Jakarta Sans", system-ui, sans-serif';
    Chart.defaults.font.size = 13;
    Chart.defaults.color = "#4F5D53";
    Chart.defaults.plugins.legend.display = false;
    Chart.defaults.plugins.tooltip.backgroundColor = "#1D2B22";
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleFont = { size: 14, weight: "bold" };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 14 };
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
  }

  window.FSUI = { icon, ring, RISK_COLOR, parseWindow, fmtDay, fmtShort, fmtWindow, cropKey, cropLabel, stamp, dataPage,
    renderTopbar, stepper, toast, speak, setSpeech, helpify };

  renderTopbar();
  document.addEventListener("fs:langchange", () => {
    renderTopbar();
    document.querySelectorAll(".help-btn").forEach((b) => b.remove());
    helpify();
    closeHelp();
  });
  document.addEventListener("DOMContentLoaded", () => { helpify(); reveal(); });
  if (document.readyState !== "loading") { helpify(); reveal(); }

  // Astuce au premier passage dans l'espace client.
  try {
    if (!localStorage.getItem("fs_tip")) {
      localStorage.setItem("fs_tip", "1");
      setTimeout(() => toast(t("a11y.tip"), "lucide:lightbulb"), 1200);
    }
  } catch (e) {}
})();
