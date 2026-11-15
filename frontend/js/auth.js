/* Field Shift — session côté client.
   Jeton signé par le serveur (/api/auth/*), gardé dans localStorage « fs_token »,
   avec une copie du profil (« fs_user ») pour afficher le nom hors ligne. */
(function () {
  const TK = "fs_token", UK = "fs_user", GK = "fs_guest";
  const read = (k) => { try { return JSON.parse(localStorage.getItem(k) || "null"); } catch (e) { return null; } };
  const write = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };

  // Accès invité (jury, démo) : tout fonctionne sans compte, rien n'est enregistré côté
  // serveur. Activé par le bouton « Essayer sans compte » ou un lien ?demo=1.
  try { if (/[?&](demo|guest)=1\b/.test(location.search)) localStorage.setItem(GK, "1"); } catch (e) {}
  function guest() { try { return localStorage.getItem(GK) === "1" && !read(TK); } catch (e) { return false; } }
  function startGuest() { try { localStorage.setItem(GK, "1"); } catch (e) {} }

  function token() { return read(TK); }
  function user() { return read(UK) || (guest() ? { first_name: "Demo", last_name: "", region: "", guest: true } : null); }

  /* Le compte connaît l'adresse : la parcelle par défaut est placée là. */
  function applyUserPlace(u, force) {
    if (!u || u.latitude == null || u.longitude == null) return;
    const place = window.Terra && Terra.getPlace();
    if (force || !place) {
      const name = [u.region || u.address.split(",")[0], u.country].filter(Boolean).join(", ");
      if (window.Terra) Terra.setPlace({ name, lat: u.latitude, lng: u.longitude });
      if (window.FSStore) FSStore.setField({ latitude: u.latitude, longitude: u.longitude });
    }
  }

  function save(tok, u) {
    write(TK, tok); write(UK, u);
    applyUserPlace(u, false);
  }
  function clear() { write(TK, null); write(UK, null); try { localStorage.removeItem(GK); } catch (e) {} }

  async function api(path, opts) {
    const o = Object.assign({ method: "GET" }, opts || {});
    const headers = { "Content-Type": "application/json" };
    const t = token();
    if (t) headers.Authorization = "Bearer " + t;
    const res = await fetch("/api/auth" + path, { method: o.method, headers, body: o.body ? JSON.stringify(o.body) : undefined });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) { const err = new Error((data && data.detail) || "HTTP " + res.status); err.status = res.status; err.detail = data && data.detail; throw err; }
    return data;
  }

  function loginUrl() { return "/connexion.html?next=" + encodeURIComponent(location.pathname + location.hash); }

  /* Pages de l'application : sans session, direction la connexion. */
  function require() {
    if (!token() && guest()) return true;
    if (!token()) { location.replace(loginUrl()); return false; }
    // Vérification serveur en arrière-plan (jeton expiré ou compte supprimé -> reconnexion).
    api("/me").then((d) => { write(UK, d.user); applyUserPlace(d.user, false); document.dispatchEvent(new CustomEvent("fs:user", { detail: d.user })); })
      .catch((e) => { if (e.status === 401) { clear(); location.replace(loginUrl()); } });
    return true;
  }

  function logout() { clear(); location.href = "/"; }

  // Message d'erreur lisible pour les codes renvoyés par l'API.
  function errKey(e) {
    const d = e && e.detail;
    if (d === "phone_taken") return "au.err.taken";
    if (d === "bad_credentials") return "au.err.creds";
    if (d === "bad_current_password") return "au.err.current";
    if (d === "phone_invalid") return "au.err.phone";
    if (e && e.status === 422) return "au.err.form";
    return "au.err.net";
  }

  window.FSAuth = { token, user, save, clear, api, require, logout, applyUserPlace, errKey, guest, startGuest };
})();
