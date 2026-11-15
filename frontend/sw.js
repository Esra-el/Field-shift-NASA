/* Field Shift — service worker.
   - App shell (pages, CSS, JS, images) : pré-cache, réseau d'abord + cache hors ligne.
   - Librairies CDN (Chart.js, Leaflet, Iconify, polices) : stale-while-revalidate,
     pour que l'appli reste utilisable hors-ligne.
   - API et tuiles de carte : réseau (l'appli garde sa dernière reco en localStorage). */
const CACHE = "field-shift-v27";
const RUNTIME = "field-shift-rt-v27";
const SHELL = [
  "/", "/site.html", "/inicio.html", "/globo.html", "/index.html", "/campo.html", "/perfil.html", "/panel.html", "/analyse.html", "/rotaciones.html",
  "/copiloto.html", "/cooperativa.html", "/backtesting.html",
  "/css/fieldshift.css", "/css/terra.css", "/css/site.css", "/css/dash.css",
  "/js/i18n.js", "/js/store.js", "/js/api.js", "/js/pwa.js", "/js/layout.js",
  "/js/campo.js", "/js/perfil.js", "/js/panel.js", "/js/analyse.js", "/js/rotaciones.js",
  "/js/copiloto.js", "/js/cooperativa.js", "/js/backtesting.js", "/js/landing.js", "/js/terra.js", "/js/inicio.js", "/js/globo.js", "/js/assistant.js", "/js/site.js", "/js/side.js", "/js/connexion.js", "/css/login.css", "/connexion.html", "/js/auth.js", "/js/i18n-auth.js", "/js/reco.js", "/js/pages.js", "/js/eau.js", "/js/saison.js", "/js/rotations-page.js", "/js/compte.js", "/eau.html", "/saison.html", "/rotations.html", "/compte.html",
  "/manifest.webmanifest",
  "/icons/icon.svg", "/icons/icon-192.png", "/icons/icon-512.png", "/icons/icon-maskable-512.png",
  "/img/fields.svg", "/img/assistant.svg", "/img/sky.jpg", "/img/photos/drought.jpg", "/img/photos/water.jpg", "/img/photos/rain.jpg", "/img/photos/seedlings.jpg", "/img/photos/mulch.jpg", "/img/photos/rows.jpg", "/img/photos/cornfield.jpg",
];
const LIB_HOSTS = [
  "cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com", "code.iconify.design",
  "api.iconify.design", "api.simplesvg.com", "api.unisvg.com",
  "fonts.googleapis.com", "fonts.gstatic.com",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== RUNTIME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  if (url.origin === self.location.origin) {
    if (url.pathname.startsWith("/api/")) {
      e.respondWith(fetch(req).catch(() => caches.match(req)));
      return;
    }
    // Réseau d'abord (toujours la dernière version en ligne), cache en secours hors ligne.
    e.respondWith(
      fetch(req).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
        return res;
      }).catch(() => caches.match(req, { ignoreSearch: true })
        .then((hit) => hit || (req.mode === "navigate" ? caches.match("/inicio.html") : undefined)))
    );
    return;
  }

  if (LIB_HOSTS.includes(url.hostname)) {
    e.respondWith(
      caches.open(RUNTIME).then((c) => c.match(req).then((hit) => {
        const net = fetch(req).then((res) => { c.put(req, res.clone()).catch(() => {}); return res; }).catch(() => hit);
        return hit || net;
      }))
    );
  }
  // Tout le reste (tuiles de carte…) : réseau normal, non mis en cache.
});
