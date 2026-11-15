/* Field Shift — capa de acceso a la API.
   - Llama al backend FastAPI (/api/*).
   - Si no hay conexión, usa la última recomendación guardada (modo offline PWA).
   El formato de la respuesta sigue el contrato acordado (sección 8.6). */
(function () {
  const BASE = ""; // mismo origen: el backend sirve el front.

  function lang() { return window.FSI18N ? FSI18N.lang : "fr"; }

  async function getRecommendation(payload) {
    try {
      const res = await fetch(BASE + "/api/recommendation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({}, payload, { lang: lang() })),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      FSStore.setLastReco(data);
      return { data, offline: false };
    } catch (e) {
      const cached = FSStore.getLastReco();
      if (cached) return { data: cached, offline: true };
      throw e; // sin conexión y sin caché: la UI mostrará el error.
    }
  }

  async function askCopilot(question, context) {
    try {
      const res = await fetch(BASE + "/api/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, context, lang: lang() }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch (e) {
      return {
        answer: FSI18N.t("copilot.offline"),
        sources: [], limitations: "offline", _mock: true,
      };
    }
  }

  async function getBacktesting(payload) {
    try {
      const res = await fetch(BASE + "/api/backtesting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({}, payload, { lang: lang() })),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      try { localStorage.setItem("fs_last_bt", JSON.stringify(data)); } catch (e) {}
      return { data, offline: false };
    } catch (e) {
      try {
        const c = JSON.parse(localStorage.getItem("fs_last_bt") || "null");
        if (c) return { data: c, offline: true };
      } catch (_) {}
      throw e;
    }
  }

  window.FSApi = { getRecommendation, askCopilot, getBacktesting };
})();
