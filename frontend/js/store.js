/* Field Shift — almacenamiento local del campo y del perfil del agricultor.
   Permite pasar datos entre páginas y funcionar sin conexión. */
(function () {
  const FIELD_KEY = "fs_field";     // { latitude, longitude }
  const PROFILE_KEY = "fs_profile"; // { crop, soil_type, irrigation, priority }
  const RECO_KEY = "fs_last_reco";  // última recomendación de la API

  function read(key) {
    try { return JSON.parse(localStorage.getItem(key) || "null"); }
    catch (e) { return null; }
  }
  function write(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
  }

  window.FSStore = {
    getField: () => read(FIELD_KEY),
    setField: (f) => write(FIELD_KEY, f),
    getProfile: () => read(PROFILE_KEY),
    setProfile: (p) => write(PROFILE_KEY, p),
    getLastReco: () => read(RECO_KEY),
    setLastReco: (r) => write(RECO_KEY, r),
    // Construye el payload del contrato 8.6 a partir de campo + perfil.
    buildPayload() {
      const f = read(FIELD_KEY) || { latitude: 14.8, longitude: -90.5 };
      const p = read(PROFILE_KEY) || {
        crop: "maize", soil_type: "sandy_loam", irrigation: false, irrigation_level: "none", priority: "save_water",
      };
      return {
        latitude: f.latitude, longitude: f.longitude,
        crop: p.crop, soil_type: p.soil_type,
        irrigation: !!p.irrigation, irrigation_level: p.irrigation_level || (p.irrigation ? "available" : "none"),
        priority: p.priority,
      };
    },
  };
})();
