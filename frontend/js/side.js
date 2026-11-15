/* Field Shift — barre latérale commune à toutes les pages de l'application.
   Rendue dans <aside id="d-side">. La page courante vient de <body data-page>.
   Exige une session (FSAuth) : sinon, direction /connexion.html. */
(function () {
  const T = Terra.t;
  if (!window.FSAuth || !FSAuth.require()) return;

  FSI18N.extend({
    fr: { "d.logout": "Se déconnecter", "d.nav.dash": "Tableau de bord", "d.nav.fields": "Analyser", "d.nav.water": "Eau",
      "d.nav.climate": "Saison", "d.nav.rot": "Rotations", "d.nav.ai": "Assistant IA" },
    en: { "d.logout": "Sign out", "d.nav.dash": "Dashboard", "d.nav.fields": "Analyze", "d.nav.water": "Water",
      "d.nav.climate": "Season", "d.nav.rot": "Rotations", "d.nav.ai": "AI assistant" },
    it: { "d.logout": "Esci", "d.nav.dash": "Dashboard", "d.nav.fields": "Analizza", "d.nav.water": "Acqua",
      "d.nav.climate": "Stagione", "d.nav.rot": "Rotazioni", "d.nav.ai": "Assistente IA" },
  });

  const NAV = [
    { id: "home", href: "/inicio.html", icon: "lucide:layout-grid", key: "d.nav.dash" },
    { id: "analyse", href: "/globo.html", icon: "lucide:scan-search", key: "d.nav.fields" },
    { id: "water", href: "/eau.html", icon: "lucide:droplets", key: "d.nav.water" },
    { id: "season", href: "/saison.html", icon: "lucide:calendar-range", key: "d.nav.climate" },
    { id: "rotations", href: "/rotations.html", icon: "lucide:refresh-cw", key: "d.nav.rot" },
  ];

  function initials(u) { return ((u.first_name || " ")[0] + (u.last_name || " ")[0]).toUpperCase().trim() || "?"; }

  function render() {
    const el = document.getElementById("d-side");
    if (!el) return;
    const page = document.body.dataset.page;
    const u = FSAuth.user() || {};
    const ic = (i) => `<span class="d-ic"><iconify-icon icon="${i}" width="18" height="18"></iconify-icon></span>`;
    el.innerHTML = `
      <a class="d-logo" href="/inicio.html"><span class="d-logo-mark"><iconify-icon icon="lucide:sprout" width="22" height="22"></iconify-icon></span>Field Shift</a>
      <nav class="d-nav" aria-label="Menu">
        ${NAV.map((n) => `<a href="${n.href}" ${n.id === page ? 'aria-current="page"' : ""}>${ic(n.icon)}<span data-t="${n.key}"></span></a>`).join("")}
        <button type="button" id="d-nav-ai">${ic("lucide:sparkles")}<span data-t="d.nav.ai"></span></button>
      </nav>
      <div class="d-side-bottom">
        <div class="d-row d-lang" role="group" aria-label="Langue · Language · Lingua">${ic("lucide:languages")}
          <div class="lang-seg">${["fr", "en", "it"].map((l) => `<button type="button" data-l="${l}" aria-pressed="${l === FSI18N.lang}">${l.toUpperCase()}</button>`).join("")}</div>
        </div>
        <a class="d-row d-me" href="/compte.html" ${page === "account" ? 'aria-current="page"' : ""}><span class="d-avatar" id="d-initials">${initials(u)}</span><span class="d-me-txt"><b id="d-me-name">${[u.first_name, u.last_name].filter(Boolean).join(" ")}</b><small id="d-me-region">${u.region || ""}</small></span></a>
        <button type="button" class="d-row" id="d-logout">${ic("lucide:log-out")}<span data-t="d.logout"></span></button>
      </div>`;

    el.querySelector(".lang-seg").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-l]");
      if (b) FSI18N.setLang(b.dataset.l);
    });
    el.querySelector("#d-nav-ai").addEventListener("click", () => window.FSAssistant && FSAssistant.open());
    el.querySelector("#d-logout").addEventListener("click", () => FSAuth.logout());
    Terra.apply(el);
  }

  document.addEventListener("fs:user", (e) => {
    const u = e.detail || {};
    const n = document.getElementById("d-me-name"), r = document.getElementById("d-me-region"), i = document.getElementById("d-initials");
    if (n) n.textContent = [u.first_name, u.last_name].filter(Boolean).join(" ");
    if (r) r.textContent = u.region || "";
    if (i) i.textContent = initials(u);
  });

  window.FSSide = { setAlerts() {} };
  document.addEventListener("DOMContentLoaded", render);
})();
