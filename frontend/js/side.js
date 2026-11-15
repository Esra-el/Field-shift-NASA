/* Field Shift — barre latérale commune (tableau de bord, analyse).
   Rendue dans <aside id="d-side">. La page courante vient de <body data-page>. */
(function () {
  const T = Terra.t;
  // Espace connecté : sans connexion sur cet appareil, on passe d'abord par /connexion.html.
  function getUser() { try { return JSON.parse(localStorage.getItem("fs_user") || "null"); } catch (e) { return null; } }
  const user = getUser();
  if (!user || !user.name) {
    location.replace("/connexion.html?next=" + encodeURIComponent(location.pathname + location.hash));
    return;
  }
  FSI18N.extend({
    fr: { "d.logout": "Se déconnecter", "d.nav.dash": "Tableau de bord", "d.nav.fields": "Analyser", "d.nav.water": "Eau", "d.nav.climate": "Saison",
      "d.nav.rot": "Rotations", "d.nav.ai": "Assistant IA", "d.nav.about": "Le projet", "d.alerts": "Alertes" },
    en: { "d.logout": "Sign out", "d.nav.dash": "Dashboard", "d.nav.fields": "Analyze", "d.nav.water": "Water", "d.nav.climate": "Season",
      "d.nav.rot": "Rotations", "d.nav.ai": "AI assistant", "d.nav.about": "About", "d.alerts": "Alerts" },
    it: { "d.logout": "Esci", "d.nav.dash": "Dashboard", "d.nav.fields": "Analizza", "d.nav.water": "Acqua", "d.nav.climate": "Stagione",
      "d.nav.rot": "Rotazioni", "d.nav.ai": "Assistente IA", "d.nav.about": "Il progetto", "d.alerts": "Avvisi" },
  });

  const NAV = [
    { id: "home", href: "/inicio.html", icon: "lucide:layout-grid", key: "d.nav.dash" },
    { id: "analyse", href: "/globo.html", icon: "lucide:sprout", key: "d.nav.fields" },
  ];

  function render() {
    const el = document.getElementById("d-side");
    if (!el) return;
    const page = document.body.dataset.page;
    const ic = (i) => `<span class="d-ic"><iconify-icon icon="${i}" width="18" height="18"></iconify-icon></span>`;
    el.innerHTML = `
      <a class="d-logo" href="/"><span class="d-logo-mark"><iconify-icon icon="lucide:sprout" width="22" height="22"></iconify-icon></span>Field Shift</a>
      <nav class="d-nav" aria-label="Menu">
        ${NAV.map((n) => `<a href="${n.href}" data-sec="${n.id}" ${n.id === page ? 'aria-current="page"' : ""}>${ic(n.icon)}<span data-t="${n.key}"></span></a>`).join("")}
        <button type="button" id="d-nav-ai">${ic("lucide:sparkles")}<span data-t="d.nav.ai"></span></button>
      </nav>
      <div class="d-side-bottom">
        <div class="d-row d-lang" role="group" aria-label="Langue · Language · Lingua">${ic("lucide:languages")}
          <div class="lang-seg">${["fr", "en", "it"].map((l) => `<button type="button" data-l="${l}" aria-pressed="${l === FSI18N.lang}">${l.toUpperCase()}</button>`).join("")}</div>
        </div>
        <div class="d-row d-me"><span class="d-avatar"><iconify-icon icon="lucide:user" width="16" height="16"></iconify-icon></span><span id="d-me-name"></span></div>
        <button type="button" class="d-row" id="d-logout">${ic("lucide:log-out")}<span data-t="d.logout"></span></button>
      </div>`;

    el.querySelector(".lang-seg").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-l]");
      if (b) FSI18N.setLang(b.dataset.l);
    });
    el.querySelector("#d-nav-ai").addEventListener("click", () => window.FSAssistant && FSAssistant.open());
    el.querySelector("#d-logout").addEventListener("click", () => {
      try { localStorage.removeItem("fs_user"); } catch (e) {}
      location.href = "/";
    });
    // Sur la page d'analyse, les liens de section défilent jusqu'au bloc du rapport.
    if (page === "analyse") {
      el.querySelectorAll("a[data-sec]").forEach((a) => a.addEventListener("click", (e) => {
        const id = (a.getAttribute("href").split("#")[1]) || "";
        const t = id && document.getElementById(id);
        if (t && t.offsetParent) { e.preventDefault(); t.scrollIntoView({ behavior: "smooth", block: "start" }); }
      }));
    }
    el.querySelector("#d-me-name").textContent = user.name;
    Terra.apply(el);
  }

  window.FSSide = {
    setAlerts(n) { const b = document.getElementById("d-alert-n"); if (b) { b.textContent = n; b.classList.toggle("hidden", !n); } },
  };
  document.addEventListener("DOMContentLoaded", render);
})();
