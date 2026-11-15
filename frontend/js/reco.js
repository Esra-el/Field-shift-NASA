/* Field Shift — accès commun à la dernière analyse (pages Eau, Saison, Rotations…).
   1) on affiche tout de suite la dernière analyse gardée sur l'appareil ;
   2) on la rafraîchit avec l'API (données en direct) pour la parcelle enregistrée. */
(function () {
  let current = null;
  const subs = [];
  function emit() { subs.forEach((f) => { try { f(current); } catch (e) { console.error(e); } }); }

  async function refresh() {
    try {
      const { data } = await FSApi.getRecommendation(FSStore.buildPayload());
      current = data;
      emit();
      if (window.FSAssistant) FSAssistant.setContext(current);
    } catch (e) {
      if (!current) emit();
    }
    return current;
  }

  window.FSReco = {
    get: () => current,
    /* Appelle cb(reco) maintenant (cache) puis à chaque mise à jour. */
    on(cb) {
      subs.push(cb);
      if (current) cb(current);
    },
    refresh,
    start() {
      current = FSStore.getLastReco();
      if (current) { emit(); if (window.FSAssistant) FSAssistant.setContext(current); }
      refresh();
      document.addEventListener("fs:langchange", () => { emit(); refresh(); });
    },
  };
})();
