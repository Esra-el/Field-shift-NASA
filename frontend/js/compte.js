/* Field Shift — page Mon compte : identité, adresse (re-géocodée), mot de passe, suppression. */
(function () {
  const T = Terra.t;
  const $ = (id) => document.getElementById(id);

  function u() { return FSAuth.user() || {}; }

  function paintId() {
    const x = u();
    const since = x.created_at ? new Date(x.created_at * 1000).toLocaleDateString(FSI18N.locale, { day: "numeric", month: "long", year: "numeric" }) : "";
    $("a-id").innerHTML = `<span class="pg-avatar">${((x.first_name || " ")[0] + (x.last_name || " ")[0]).toUpperCase()}</span>
      <div><h2>${[x.first_name, x.last_name].filter(Boolean).join(" ")}</h2><p class="pg-muted">${x.phone || ""}</p>${since ? `<small class="pg-muted">${T("ac.since", { d: since })}</small>` : ""}</div>
      <button type="button" class="pg-btn-ghost" id="a-logout"><iconify-icon icon="lucide:log-out" width="18" height="18"></iconify-icon>${T("ac.logout")}</button>`;
    $("a-logout").onclick = () => FSAuth.logout();
  }

  function paintInfo() {
    const x = u();
    $("a-info").innerHTML = `<h2>${T("ac.info")}</h2>
      <div class="pg-row"><label><span>${T("au.first")}</span><input id="i-first" value="${esc(x.first_name)}" autocomplete="given-name" /></label>
      <label><span>${T("au.last")}</span><input id="i-last" value="${esc(x.last_name)}" autocomplete="family-name" /></label></div>
      <label><span>${T("au.phone")}</span><input value="${esc(x.phone)}" disabled /></label>
      <label><span>${T("au.address")}</span><input id="i-addr" value="${esc(x.address)}" autocomplete="street-address" /></label>
      <p class="pg-msg" id="i-msg"></p>
      <button type="submit" class="d-btn-lime">${T("ac.save")}</button>`;
  }

  function paintPlace() {
    const x = u();
    $("a-place").innerHTML = `<h2>${T("ac.place")}</h2>
      <dl class="pg-kv col"><div><dt>${T("ac.region")}</dt><dd>${[x.region, x.country].filter(Boolean).join(", ") || "—"}</dd></div>
      <div><dt>${T("ac.coords")}</dt><dd>${x.latitude != null ? Terra.fmtCoords(x.latitude, x.longitude) : "—"}</dd></div></dl>
      <a class="pg-link" href="/globo.html">${T("d.nav.fields")} <iconify-icon icon="lucide:arrow-right" width="16" height="16"></iconify-icon></a>`;
  }

  function paintPw() {
    $("a-pw").innerHTML = `<h2>${T("ac.pw_title")}</h2>
      <label><span>${T("ac.pw_cur")}</span><input id="p-cur" type="password" autocomplete="current-password" /></label>
      <label><span>${T("ac.pw_new")}</span><input id="p-new" type="password" autocomplete="new-password" minlength="6" /></label>
      <p class="pg-msg" id="p-msg"></p>
      <button type="submit" class="pg-btn-ghost">${T("ac.pw_btn")}</button>`;
  }

  function paintDel() {
    $("a-del").innerHTML = `<h2>${T("ac.danger")}</h2><p class="pg-muted">${T("ac.danger_txt")}</p>
      <button type="button" class="pg-btn-danger" id="a-del-btn"><iconify-icon icon="lucide:trash-2" width="18" height="18"></iconify-icon>${T("ac.del_btn")}</button>`;
    $("a-del-btn").onclick = async () => {
      if (!confirm(T("ac.del_confirm"))) return;
      try { await FSAuth.api("/me", { method: "DELETE" }); } catch (e) {}
      ["fs_place", "fs_field", "fs_profile", "fs_last_reco"].forEach((k) => { try { localStorage.removeItem(k); } catch (e) {} });
      FSAuth.logout();
    };
  }

  function esc(s) { return String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]); }
  function msg(id, key, ok) { const e = $(id); e.textContent = key ? T(key) : ""; e.className = "pg-msg " + (ok ? "ok" : "bad"); }

  $("a-info").addEventListener("submit", async (e) => {
    e.preventDefault();
    const x = u();
    const body = { first_name: $("i-first").value.trim(), last_name: $("i-last").value.trim() };
    if (!body.first_name || !body.last_name) return msg("i-msg", "au.err.fill");
    const addr = $("i-addr").value.trim();
    if (addr && addr !== x.address) {
      body.address = addr;
      try {
        const g = await FSGeo.address(addr);
        if (g) Object.assign(body, { region: g.region || null, country: g.country || null, latitude: g.lat, longitude: g.lng });
      } catch (err) {}
    }
    try {
      const d = await FSAuth.api("/me", { method: "PUT", body });
      FSAuth.save(FSAuth.token(), d.user);
      if (body.latitude != null) FSAuth.applyUserPlace(d.user, true);
      paintAll(); msg("i-msg", "ac.saved", true);
      document.dispatchEvent(new CustomEvent("fs:user", { detail: d.user }));
    } catch (err) { msg("i-msg", FSAuth.errKey(err)); }
  });

  $("a-pw").addEventListener("submit", async (e) => {
    e.preventDefault();
    const cur = $("p-cur").value, nw = $("p-new").value;
    if (nw.length < 6) return msg("p-msg", "au.err.short");
    try {
      await FSAuth.api("/me", { method: "PUT", body: { password: nw, current_password: cur } });
      paintPw(); msg("p-msg", "ac.pw_ok", true);
    } catch (err) { msg("p-msg", FSAuth.errKey(err)); }
  });

  function paintAll() { paintId(); paintInfo(); paintPlace(); paintPw(); paintDel(); }
  document.addEventListener("fs:user", () => { paintId(); paintPlace(); });
  document.addEventListener("fs:langchange", paintAll);
  document.addEventListener("DOMContentLoaded", () => {
    paintAll();
    const p = document.getElementById("pg-place-name");
    if (p) p.textContent = [u().region, u().country].filter(Boolean).join(", ") || "—";
  });
})();
