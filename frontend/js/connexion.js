/* Field Shift — connexion et inscription (comptes serveur /api/auth). */
(function () {
  const $ = (id) => document.getElementById(id);
  const T = Terra.t;
  const next = new URLSearchParams(location.search).get("next");
  const dest = next && next.startsWith("/") && !next.startsWith("//") ? next : "/inicio.html";

  // Déjà connecté : on entre directement.
  if (FSAuth.token()) { location.replace(dest); return; }

  /* ---------- Onglets ---------- */
  function show(tab) {
    $("f-in").classList.toggle("hidden", tab !== "in");
    $("f-up").classList.toggle("hidden", tab !== "up");
    $("tab-in").setAttribute("aria-selected", tab === "in");
    $("tab-up").setAttribute("aria-selected", tab === "up");
    history.replaceState(null, "", tab === "up" ? "#inscription" : location.pathname + location.search);
    (tab === "up" ? $("up-first") : $("in-phone")).focus({ preventScroll: true });
  }
  document.querySelectorAll("[data-tab],[data-goto]").forEach((b) => b.addEventListener("click", () => show(b.dataset.tab || b.dataset.goto)));
  if (location.hash === "#inscription") show("up");

  document.querySelectorAll(".lg-eye").forEach((b) => b.addEventListener("click", () => {
    const i = $(b.dataset.for);
    i.type = i.type === "password" ? "text" : "password";
    b.querySelector("iconify-icon").setAttribute("icon", i.type === "password" ? "lucide:eye" : "lucide:eye-off");
  }));

  function err(id, key) { const e = $(id); e.textContent = key ? T(key) : ""; e.classList.toggle("hidden", !key); }
  function busy(btn, on) {
    btn.disabled = on;
    const s = btn.querySelector("span");
    if (on) { s.dataset.prev = s.textContent; s.textContent = T("au.wait"); } else if (s.dataset.prev) s.textContent = s.dataset.prev;
  }

  /* ---------- Connexion ---------- */
  $("f-in").addEventListener("submit", async (e) => {
    e.preventDefault();
    const phone = $("in-phone").value.trim(), password = $("in-pw").value;
    if (!phone || !password) return err("in-err", "au.err.fill");
    err("in-err", null); busy($("in-go"), true);
    try {
      const d = await FSAuth.api("/login", { method: "POST", body: { phone, password } });
      FSAuth.save(d.token, d.user);
      FSAuth.applyUserPlace(d.user, true);
      location.href = dest;
    } catch (x) { err("in-err", FSAuth.errKey(x)); busy($("in-go"), false); }
  });

  /* ---------- Inscription : l'adresse donne la région et les coordonnées ---------- */
  let geo = null, geoFor = "";
  async function lookup() {
    const q = $("up-addr").value.trim();
    if (q.length < 3 || q === geoFor) return geo;
    geoFor = q; geo = null;
    const hint = $("up-region");
    hint.className = "lg-hint";
    hint.querySelector("span").textContent = T("au.addr_search");
    try { geo = await FSGeo.address(q); } catch (x) { geo = null; }
    hint.classList.toggle("ok", !!geo);
    hint.classList.toggle("warn", !geo);
    hint.querySelector("span").textContent = geo ? T("au.addr_found", { r: geo.label || geo.region }) : T("au.addr_none");
    return geo;
  }
  $("up-addr").addEventListener("blur", lookup);
  $("up-addr").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); lookup(); } });

  $("f-up").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      first_name: $("up-first").value.trim(), last_name: $("up-last").value.trim(),
      phone: $("up-phone").value.trim(), address: $("up-addr").value.trim(), password: $("up-pw").value,
    };
    if (Object.values(body).some((v) => !v)) return err("up-err", "au.err.fill");
    if (body.password.length < 6) return err("up-err", "au.err.short");
    if (body.password !== $("up-pw2").value) return err("up-err", "au.err.match");
    if (!$("up-ok").checked) return err("up-err", "au.err.consent");
    err("up-err", null); busy($("up-go"), true);
    const g = await lookup();
    if (g) Object.assign(body, { region: g.region || null, country: g.country || null, latitude: g.lat, longitude: g.lng });
    try {
      const d = await FSAuth.api("/register", { method: "POST", body });
      FSAuth.save(d.token, d.user);
      FSAuth.applyUserPlace(d.user, true);
      location.href = dest;
    } catch (x) { err("up-err", FSAuth.errKey(x)); busy($("up-go"), false); }
  });

  /* ---------- Langue ---------- */
  document.querySelector(".lg-lang").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-l]");
    if (b) FSI18N.setLang(b.dataset.l);
  });
  const paintLang = () => document.querySelectorAll(".lg-lang button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.l === FSI18N.lang));
  document.addEventListener("fs:langchange", paintLang);
  document.addEventListener("DOMContentLoaded", paintLang);
})();
