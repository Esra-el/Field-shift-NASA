/* Field Shift — connexion (démo).
   Il n'y a pas encore de comptes côté serveur : le nom est gardé sur cet appareil
   (localStorage « fs_user ») pour personnaliser l'application. Aucun mot de passe n'est demandé ni stocké. */
(function () {
  const $ = (id) => document.getElementById(id);
  FSI18N.extend({
    fr: {
      "lg.title": "Connexion", "lg.sub": "Accédez à votre tableau de bord et à l'analyse de votre parcelle.",
      "lg.name": "Votre nom", "lg.contact": "Téléphone ou e-mail (facultatif)", "lg.contact_ph": "ex. +504 9999 0000",
      "lg.submit": "Se connecter", "lg.err": "Indiquez votre nom pour continuer.",
      "lg.known": "Déjà connecté sur cet appareil", "lg.continue": "Continuer",
      "lg.note": "Version de démonstration : votre nom reste sur cet appareil, aucun mot de passe n'est demandé.",
      "lg.back": "Retour au site", "lg.v_title": "Votre parcelle vue du ciel", "lg.v_sub": "Données NASA en direct, conseils simples.",
    },
    en: {
      "lg.title": "Sign in", "lg.sub": "Open your dashboard and the analysis of your field.",
      "lg.name": "Your name", "lg.contact": "Phone or email (optional)", "lg.contact_ph": "e.g. +504 9999 0000",
      "lg.submit": "Sign in", "lg.err": "Enter your name to continue.",
      "lg.known": "Already signed in on this device", "lg.continue": "Continue",
      "lg.note": "Demo version: your name stays on this device, no password is asked.",
      "lg.back": "Back to site", "lg.v_title": "Your field seen from space", "lg.v_sub": "Live NASA data, simple advice.",
    },
    it: {
      "lg.title": "Accedi", "lg.sub": "Apri la tua dashboard e l'analisi del tuo campo.",
      "lg.name": "Il tuo nome", "lg.contact": "Telefono o e-mail (facoltativo)", "lg.contact_ph": "es. +504 9999 0000",
      "lg.submit": "Accedi", "lg.err": "Inserisci il tuo nome per continuare.",
      "lg.known": "Già connesso su questo dispositivo", "lg.continue": "Continua",
      "lg.note": "Versione dimostrativa: il tuo nome resta su questo dispositivo, nessuna password richiesta.",
      "lg.back": "Torna al sito", "lg.v_title": "Il tuo campo visto dallo spazio", "lg.v_sub": "Dati NASA in tempo reale, consigli semplici.",
    },
  });

  function getUser() { try { return JSON.parse(localStorage.getItem("fs_user") || "null"); } catch (e) { return null; } }
  const next = new URLSearchParams(location.search).get("next");
  const dest = next && next.startsWith("/") && !next.startsWith("//") ? next : "/inicio.html";

  const u = getUser();
  if (u && u.name) {
    $("lg-known").classList.remove("hidden");
    $("lg-known-name").textContent = u.name;
    $("lg-known").querySelector("a").href = dest;
  }

  $("lg-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("lg-name").value.trim();
    if (!name) { $("lg-err").classList.remove("hidden"); $("lg-name").focus(); return; }
    try { localStorage.setItem("fs_user", JSON.stringify({ name, contact: $("lg-contact").value.trim(), at: Date.now() })); } catch (err) {}
    location.href = dest;
  });

  document.querySelector(".lg-lang").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-l]");
    if (b) FSI18N.setLang(b.dataset.l);
  });
  const paintLang = () => document.querySelectorAll(".lg-lang button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.l === FSI18N.lang));
  document.addEventListener("fs:langchange", paintLang);
  document.addEventListener("DOMContentLoaded", paintLang);
})();
