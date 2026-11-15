/* Field Shift — « Terra » : textes FR / EN / IT, barre de navigation, globe satellite partagé.
   Expose window.FSI18N (compatible avec api.js) et window.Terra. */
(function () {
  const DICT = {
    fr: {
      "nav.home": "Accueil", "nav.analyse": "Analyser", "nav.site": "Le projet",
      "tagline": "Décidez quoi semer avant l'arrivée de la sécheresse.",
      "home.hello": "Bonjour, bienvenue sur Field Shift.",
      "home.lead": "Les données des satellites de la NASA transformées en réponses simples pour votre parcelle.",
      "cta.analyse": "Analyser ma parcelle",
      "home.example": "Parcelle d'exemple", "home.your_field": "Votre parcelle",
      "stat.risk": "Risque de sécheresse", "stat.water": "Eau pour la culture", "stat.next": "Prochaine étape",
      "home.calendar": "Calendrier de la saison", "home.calendar_sub": "Quand semer et comment votre culture va pousser",
      "home.focus": "Priorité de la semaine", "home.sources": "Données :",
      "stage.planting": "Semis", "stage.growing": "Croissance", "stage.flowering": "Floraison", "stage.harvest": "Récolte",
      "stage.dry": "Période sèche", "today": "Aujourd'hui",
      "risk.low": "Faible", "risk.moderate": "Modéré", "risk.high": "Élevé",
      "risk.low.d": "Les conditions d'eau sont bonnes pour votre culture.",
      "risk.moderate.d": "Il y a des signes de manque d'eau. Mieux vaut être prudent.",
      "risk.high.d": "L'eau manque beaucoup. Semer maintenant est risqué.",
      "ws.enough_water": "Assez d'eau", "ws.risky": "Eau juste", "ws.not_enough_water": "Pas assez d'eau",
      "ws.d": "Couvre {cov} % de ce dont la culture a besoin.",
      "pl.plant_now": "Semer maintenant", "pl.wait": "Attendre", "pl.switch_crop": "Changer de culture",
      "focus.prepare_soil": "Préparez une couverture du sol avant de semer.",
      "focus.monitor_rain": "Surveillez la pluie pendant les 7 prochains jours.",
      "focus.consider_rotation": "Envisagez une rotation de cultures résistante à la sécheresse.",
      "focus.plant_now": "C'est le bon moment : semez dans la fenêtre conseillée.",
      "focus.why.prepare_soil": "Un sol couvert perd moins d'eau quand il fait chaud.",
      "focus.why.monitor_rain": "S'il tombe plus de 20 mm cette semaine, la fenêtre de semis s'ouvre.",
      "focus.why.consider_rotation": "Une culture qui demande moins d'eau réduit votre risque cette saison.",
      "focus.why.plant_now": "L'humidité du sol et la pluie prévue sont favorables.",
      "focus.cta": "Voir l'analyse complète",

      "an.title": "Analysez votre parcelle",
      "an.sub": "Quatre questions. Ensuite, le satellite vous montre votre terrain.",
      "f.location": "Où est votre parcelle ?", "f.location_ph": "Village, ville ou coordonnées",
      "f.gps": "Utiliser ma position", "f.pick": "Choisir sur le globe", "f.pick_msg": "Touchez votre terrain sur le globe",
      "f.crop": "Culture", "f.soil": "Type de sol", "f.irrigation": "Accès à l'irrigation", "f.priority": "Votre priorité",
      "crop.maize": "Maïs", "crop.beans": "Haricot", "crop.sorghum": "Sorgho", "crop.millet": "Millet", "crop.other": "Autre",
      "soil.sandy": "Sableux", "soil.sandy_loam": "Limon sableux", "soil.clay_loam": "Limon argileux", "soil.clay": "Argileux",
      "irr.none": "Aucun", "irr.limited": "Limité", "irr.available": "Disponible",
      "prio.save_water": "Économiser l'eau", "prio.protect_soil": "Protéger le sol", "prio.max_yield": "Meilleure récolte", "prio.food_security": "Sécurité alimentaire",
      "an.analysing": "Analyse en cours…", "an.not_found": "Lieu introuvable. Essayez un autre nom ou des coordonnées.",
      "an.offline": "Hors ligne : voici la dernière analyse enregistrée.",
      "an.error": "L'analyse a échoué. Vérifiez votre connexion et réessayez.",
      "an.ready": "Terminé. Touchez les couches du globe pour voir chaque donnée.",
      "an.idle": "Satellite prêt", "an.live": "Images satellite réelles",
      "q.risk": "À quel point est-ce sec ?", "q.water": "Ai-je assez d'eau pour ma culture ?", "q.when": "Quand dois-je semer ?",
      "q.rot": "Quelle rotation me convient ?", "q.rot_sub": "Trois plans, du plus sûr au plus productif.",
      "wb.need": "Ce dont la culture a besoin", "wb.have": "L'eau que vous aurez",
      "wb.reco.enough_water": "Vous pouvez semer sereinement. Gardez le sol couvert.",
      "wb.reco.risky": "Semez moins dense ou choisissez une culture qui demande moins d'eau.",
      "wb.reco.not_enough_water": "L'eau ne suffit pas : attendez la pluie ou passez à une culture plus résistante.",
      "rot.safest": "Plan le plus sûr", "rot.balanced": "Plan équilibré", "rot.highest_yield": "Meilleure récolte",
      "rot.risk": "Risque", "rot.water": "Eau économisée", "rot.soil": "Santé du sol", "rot.yield": "Récolte",
      "lvl.high": "Élevée", "lvl.medium": "Moyenne", "lvl.low": "Faible", "rot.best": "Pour vous",
      "adv.title": "Détails scientifiques (NASA)",
      "adv.rain": "Pluie sur 60 jours", "adv.normal": "Normale", "adv.normal_src": "NASA POWER · 1981-2020", "adv.soil": "Humidité du sol", "adv.ndvi": "Tendance NDVI",
      "adv.solar": "Rayonnement solaire", "adv.et": "Évapotranspiration", "adv.temp": "Température", "adv.wind": "Vent",
      "chat.title": "Demandez à l'assistant", "chat.sub": "Il répond avec les données de votre parcelle.",
      "chat.ph": "Écrivez votre question…", "chat.send": "Envoyer",
      "chat.hello": "Bonjour. Je peux vous expliquer l'analyse de votre parcelle. Que voulez-vous savoir ?",
      "chat.q1": "Ai-je assez d'eau ?", "chat.q2": "Quand dois-je semer ?", "chat.q3": "Quelle culture choisir à la place ?", "chat.q4": "Comment protéger mon sol ?",
      "chat.example": "Je n'ai pas d'irrigation et je veux semer du maïs la semaine prochaine. Que faire ?",
      "chat.typing": "En train d'écrire…", "copilot.offline": "Hors ligne. Réessayez quand vous aurez internet.",

      "layer.sat": "Satellite", "layer.rain": "Précipitations", "layer.wind": "Vent", "layer.temp": "Température", "layer.solar": "Rayonnement solaire", "layer.soil": "Humidité du sol", "layer.ndvi": "Végétation",
      "lg.rain": ["Faible", "Forte pluie"], "lg.wind": ["Calme", "Fort"], "lg.temp": ["Frais", "Chaud"], "lg.solar": ["Faible", "Intense"], "lg.soil": ["Sec", "Humide"], "lg.ndvi": ["Stressée", "Saine"],
      "lg.sat": "Image satellite du terrain",
      "lg.date": "Image du {d}", "lg.month": "Moyenne de {d}",
      "in.sat": "Voici votre terrain vu du ciel.",
      "in.sat.more": "Zoomez avec deux doigts pour voir vos champs. Les couches en bas montrent les données NASA autour de chez vous.",
      "in.rain.below": "Les pluies des 60 derniers jours sont en dessous de la normale.",
      "in.rain.ok": "Les pluies des 60 derniers jours sont proches de la normale.",
      "in.rain.more": "Il est tombé {a} mm de pluie. La normale dans votre zone est de {b} mm.",
      "in.wind": "Le vent souffle à {s} km/h depuis le {d}.",
      "in.wind.more": "Un vent fort sèche plus vite la terre et les feuilles.",
      "in.wind.calm": "C'est un vent doux : il sèche peu le sol.",
      "in.temp.hot": "Il fait chaud dans votre zone ({t} °C). Risque de stress pour les plantes.",
      "in.temp.ok": "La température est normale pour la saison ({t} °C).",
      "in.temp.more": "Quand il fait très chaud, la culture demande plus d'eau chaque jour.",
      "in.solar.high": "Il y a beaucoup de soleil dans votre zone.",
      "in.solar.ok": "L'ensoleillement est modéré.",
      "in.solar.more": "Plus de soleil, c'est une terre qui sèche plus vite. Votre sol perd environ {et} mm d'eau par jour.",
      "in.soil.low": "L'humidité du sol est basse dans votre zone.",
      "in.soil.ok": "Le sol est bien humide.",
      "in.soil.more": "Le satellite mesure {p} % d'eau dans la terre en surface. En dessous de 20 %, il est difficile de semer.",
      "in.ndvi.stress": "La végétation montre des signes de stress modéré.",
      "in.ndvi.ok": "La végétation de votre zone est en bonne santé.",
      "in.ndvi.more": "Les plantes sont moins vertes qu'il y a deux mois.",
      "in.ndvi.more_ok": "Les plantes restent vertes depuis deux mois.",
      "in.need_water": "Votre culture pourrait avoir besoin de plus d'eau que disponible.",
      "in.wait": "Nous conseillons d'attendre avant de semer ou d'envisager une rotation plus résistante.",
      "in.plant": "Les conditions permettent de semer dans la fenêtre conseillée.",
      "dir": ["nord", "nord-est", "est", "sud-est", "sud", "sud-ouest", "ouest", "nord-ouest"],
      "no3d": "Le globe 3D n'est pas disponible sur cet appareil.",
      "region": "Amérique centrale",
    },
    en: {
      "nav.home": "Home", "nav.analyse": "Analyze", "nav.site": "About",
      "tagline": "Decide what to plant before a drought hits.",
      "home.hello": "Hello, welcome to Field Shift.",
      "home.lead": "NASA satellite data turned into simple answers for your field.",
      "cta.analyse": "Analyze my field",
      "home.example": "Example field", "home.your_field": "Your field",
      "stat.risk": "Drought risk", "stat.water": "Water for your crop", "stat.next": "Next step",
      "home.calendar": "Season calendar", "home.calendar_sub": "When to plant and how your crop will grow",
      "home.focus": "This week's focus", "home.sources": "Data:",
      "stage.planting": "Planting", "stage.growing": "Growing", "stage.flowering": "Flowering", "stage.harvest": "Harvest",
      "stage.dry": "Dry spell", "today": "Today",
      "risk.low": "Low", "risk.moderate": "Moderate", "risk.high": "High",
      "risk.low.d": "Water conditions are good for your crop.",
      "risk.moderate.d": "There are signs of water shortage. Be careful.",
      "risk.high.d": "Water is very short. Planting now is risky.",
      "ws.enough_water": "Enough water", "ws.risky": "Risky", "ws.not_enough_water": "Not enough water",
      "ws.d": "Covers {cov}% of what the crop needs.",
      "pl.plant_now": "Plant now", "pl.wait": "Wait", "pl.switch_crop": "Switch crop",
      "focus.prepare_soil": "Prepare soil cover before planting.",
      "focus.monitor_rain": "Monitor rainfall during the next 7 days.",
      "focus.consider_rotation": "Consider a drought-resilient crop rotation.",
      "focus.plant_now": "Good timing: plant within the recommended window.",
      "focus.why.prepare_soil": "Covered soil loses less water in hot weather.",
      "focus.why.monitor_rain": "If more than 20 mm falls this week, the planting window opens.",
      "focus.why.consider_rotation": "A crop that needs less water lowers your risk this season.",
      "focus.why.plant_now": "Soil moisture and forecast rain are favourable.",
      "focus.cta": "See the full analysis",

      "an.title": "Analyze your field", "an.sub": "Four questions. Then the satellite shows you your land.",
      "f.location": "Where is your field?", "f.location_ph": "Village, city or coordinates",
      "f.gps": "Use my location", "f.pick": "Pick on the globe", "f.pick_msg": "Tap your land on the globe",
      "f.crop": "Crop", "f.soil": "Soil type", "f.irrigation": "Irrigation access", "f.priority": "Your priority",
      "crop.maize": "Maize", "crop.beans": "Beans", "crop.sorghum": "Sorghum", "crop.millet": "Millet", "crop.other": "Other",
      "soil.sandy": "Sandy", "soil.sandy_loam": "Sandy loam", "soil.clay_loam": "Clay loam", "soil.clay": "Clay",
      "irr.none": "None", "irr.limited": "Limited", "irr.available": "Available",
      "prio.save_water": "Save water", "prio.protect_soil": "Protect soil", "prio.max_yield": "Maximize yield", "prio.food_security": "Food security",
      "an.analysing": "Analyzing…", "an.not_found": "We couldn't find that place. Try another name or coordinates.",
      "an.offline": "Offline: showing your last saved analysis.",
      "an.error": "Analysis failed. Check your connection and try again.",
      "an.ready": "Done. Tap the globe layers to see each data set.",
      "an.idle": "Satellite ready", "an.live": "Real satellite imagery",
      "q.risk": "How dry is it?", "q.water": "Do I have enough water for my crop?", "q.when": "When should I plant?",
      "q.rot": "Which rotation suits me?", "q.rot_sub": "Three plans, from safest to highest yield.",
      "wb.need": "What the crop needs", "wb.have": "Water you will have",
      "wb.reco.enough_water": "You can plant with confidence. Keep the soil covered.",
      "wb.reco.risky": "Plant less densely or choose a crop that needs less water.",
      "wb.reco.not_enough_water": "Not enough water: wait for rain or switch to a hardier crop.",
      "rot.safest": "Safest plan", "rot.balanced": "Balanced plan", "rot.highest_yield": "Highest yield",
      "rot.risk": "Risk", "rot.water": "Water saving", "rot.soil": "Soil health", "rot.yield": "Yield",
      "lvl.high": "High", "lvl.medium": "Medium", "lvl.low": "Low", "rot.best": "For you",
      "adv.title": "Scientific details (NASA)",
      "adv.rain": "Rain, 60 days", "adv.normal": "Normal", "adv.normal_src": "NASA POWER · 1981-2020", "adv.soil": "Soil moisture", "adv.ndvi": "NDVI trend",
      "adv.solar": "Solar radiation", "adv.et": "Evapotranspiration", "adv.temp": "Temperature", "adv.wind": "Wind",
      "chat.title": "Ask the assistant", "chat.sub": "Answers using your field's data.",
      "chat.ph": "Type your question…", "chat.send": "Send",
      "chat.hello": "Hi. I can explain your field's analysis. What would you like to know?",
      "chat.q1": "Do I have enough water?", "chat.q2": "When should I plant?", "chat.q3": "Which crop can I switch to?", "chat.q4": "How do I protect my soil?",
      "chat.example": "I have no irrigation and want to plant maize next week. What should I do?",
      "chat.typing": "Typing…", "copilot.offline": "Offline. Try again when you have internet.",

      "layer.sat": "Satellite", "layer.rain": "Rainfall", "layer.wind": "Wind", "layer.temp": "Temperature", "layer.solar": "Solar radiation", "layer.soil": "Soil moisture", "layer.ndvi": "Vegetation",
      "lg.rain": ["Light", "Heavy rain"], "lg.wind": ["Calm", "Strong"], "lg.temp": ["Cool", "Hot"], "lg.solar": ["Low", "Intense"], "lg.soil": ["Dry", "Moist"], "lg.ndvi": ["Stressed", "Healthy"],
      "lg.sat": "Satellite image of the land",
      "lg.date": "Image from {d}", "lg.month": "Average for {d}",
      "in.sat": "This is your land seen from the sky.",
      "in.sat.more": "Pinch to zoom in on your fields. The layers below show NASA data around you.",
      "in.rain.below": "Rainfall over the last 60 days is below normal.",
      "in.rain.ok": "Rainfall over the last 60 days is close to normal.",
      "in.rain.more": "{a} mm of rain fell. Normal for your area is {b} mm.",
      "in.wind": "Wind blows at {s} km/h from the {d}.",
      "in.wind.more": "Strong wind dries soil and leaves faster.",
      "in.wind.calm": "It's a gentle wind: it doesn't dry the soil much.",
      "in.temp.hot": "It is hot in your area ({t} °C). Risk of heat stress for plants.",
      "in.temp.ok": "Temperature is normal for the season ({t} °C).",
      "in.temp.more": "In hot weather, the crop needs more water every day.",
      "in.solar.high": "There is a lot of sun in your area.", "in.solar.ok": "Sunshine is moderate.",
      "in.solar.more": "More sun means the soil dries faster. Your soil loses about {et} mm of water per day.",
      "in.soil.low": "Soil moisture is low in your area.", "in.soil.ok": "The soil has good moisture.",
      "in.soil.more": "The satellite measures {p}% water in the topsoil. Below 20% planting is hard.",
      "in.ndvi.stress": "Vegetation shows signs of moderate stress.", "in.ndvi.ok": "Vegetation in your area is healthy.",
      "in.ndvi.more": "Plants are less green than two months ago.", "in.ndvi.more_ok": "Plants have stayed green over two months.",
      "in.need_water": "Your crop may need more water than is available.",
      "in.wait": "We recommend waiting before planting or considering a more resilient rotation.",
      "in.plant": "Conditions allow planting within the recommended window.",
      "dir": ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"],
      "no3d": "The 3D globe is not available on this device.",
      "region": "Central America",
    },
    it: {
      "nav.home": "Home", "nav.analyse": "Analizza", "nav.site": "Il progetto",
      "tagline": "Decidi cosa seminare prima che arrivi la siccità.",
      "home.hello": "Ciao, benvenuto su Field Shift.",
      "home.lead": "I dati dei satelliti NASA trasformati in risposte semplici per il tuo campo.",
      "cta.analyse": "Analizza il mio campo",
      "home.example": "Campo di esempio", "home.your_field": "Il tuo campo",
      "stat.risk": "Rischio siccità", "stat.water": "Acqua per la coltura", "stat.next": "Prossimo passo",
      "home.calendar": "Calendario della stagione", "home.calendar_sub": "Quando seminare e come crescerà la tua coltura",
      "home.focus": "Priorità della settimana", "home.sources": "Dati:",
      "stage.planting": "Semina", "stage.growing": "Crescita", "stage.flowering": "Fioritura", "stage.harvest": "Raccolto",
      "stage.dry": "Periodo secco", "today": "Oggi",
      "risk.low": "Basso", "risk.moderate": "Moderato", "risk.high": "Alto",
      "risk.low.d": "Le condizioni d'acqua sono buone per la tua coltura.",
      "risk.moderate.d": "Ci sono segnali di mancanza d'acqua. Meglio essere prudenti.",
      "risk.high.d": "Manca molta acqua. Seminare ora è rischioso.",
      "ws.enough_water": "Acqua sufficiente", "ws.risky": "Acqua al limite", "ws.not_enough_water": "Acqua insufficiente",
      "ws.d": "Copre il {cov}% di ciò che serve alla coltura.",
      "pl.plant_now": "Semina ora", "pl.wait": "Aspetta", "pl.switch_crop": "Cambia coltura",
      "focus.prepare_soil": "Prepara una copertura del suolo prima di seminare.",
      "focus.monitor_rain": "Controlla la pioggia nei prossimi 7 giorni.",
      "focus.consider_rotation": "Valuta una rotazione colturale resistente alla siccità.",
      "focus.plant_now": "È il momento giusto: semina nella finestra consigliata.",
      "focus.why.prepare_soil": "Un suolo coperto perde meno acqua quando fa caldo.",
      "focus.why.monitor_rain": "Se cadono più di 20 mm questa settimana, la finestra di semina si apre.",
      "focus.why.consider_rotation": "Una coltura che chiede meno acqua riduce il tuo rischio in questa stagione.",
      "focus.why.plant_now": "L'umidità del suolo e la pioggia prevista sono favorevoli.",
      "focus.cta": "Vedi l'analisi completa",

      "an.title": "Analizza il tuo campo", "an.sub": "Quattro domande. Poi il satellite ti mostra il tuo terreno.",
      "f.location": "Dov'è il tuo campo?", "f.location_ph": "Villaggio, città o coordinate",
      "f.gps": "Usa la mia posizione", "f.pick": "Scegli sul globo", "f.pick_msg": "Tocca il tuo terreno sul globo",
      "f.crop": "Coltura", "f.soil": "Tipo di suolo", "f.irrigation": "Accesso all'irrigazione", "f.priority": "La tua priorità",
      "crop.maize": "Mais", "crop.beans": "Fagioli", "crop.sorghum": "Sorgo", "crop.millet": "Miglio", "crop.other": "Altro",
      "soil.sandy": "Sabbioso", "soil.sandy_loam": "Franco sabbioso", "soil.clay_loam": "Franco argilloso", "soil.clay": "Argilloso",
      "irr.none": "Nessuna", "irr.limited": "Limitata", "irr.available": "Disponibile",
      "prio.save_water": "Risparmiare acqua", "prio.protect_soil": "Proteggere il suolo", "prio.max_yield": "Raccolto migliore", "prio.food_security": "Sicurezza alimentare",
      "an.analysing": "Analisi in corso…", "an.not_found": "Luogo non trovato. Prova un altro nome o le coordinate.",
      "an.offline": "Offline: ecco l'ultima analisi salvata.",
      "an.error": "Analisi non riuscita. Controlla la connessione e riprova.",
      "an.ready": "Fatto. Tocca i livelli del globo per vedere ogni dato.",
      "an.idle": "Satellite pronto", "an.live": "Immagini satellitari reali",
      "q.risk": "Quanto è secco?", "q.water": "Ho abbastanza acqua per la mia coltura?", "q.when": "Quando devo seminare?",
      "q.rot": "Quale rotazione fa per me?", "q.rot_sub": "Tre piani, dal più sicuro al più produttivo.",
      "wb.need": "Ciò che serve alla coltura", "wb.have": "L'acqua che avrai",
      "wb.reco.enough_water": "Puoi seminare tranquillo. Tieni il suolo coperto.",
      "wb.reco.risky": "Semina meno fitto o scegli una coltura che chiede meno acqua.",
      "wb.reco.not_enough_water": "L'acqua non basta: aspetta la pioggia o passa a una coltura più resistente.",
      "rot.safest": "Piano più sicuro", "rot.balanced": "Piano equilibrato", "rot.highest_yield": "Raccolto migliore",
      "rot.risk": "Rischio", "rot.water": "Acqua risparmiata", "rot.soil": "Salute del suolo", "rot.yield": "Raccolto",
      "lvl.high": "Alta", "lvl.medium": "Media", "lvl.low": "Bassa", "rot.best": "Per te",
      "adv.title": "Dettagli scientifici (NASA)",
      "adv.rain": "Pioggia 60 giorni", "adv.normal": "Normale", "adv.normal_src": "NASA POWER · 1981-2020", "adv.soil": "Umidità del suolo", "adv.ndvi": "Tendenza NDVI",
      "adv.solar": "Radiazione solare", "adv.et": "Evapotraspirazione", "adv.temp": "Temperatura", "adv.wind": "Vento",
      "chat.title": "Chiedi all'assistente", "chat.sub": "Risponde con i dati del tuo campo.",
      "chat.ph": "Scrivi la tua domanda…", "chat.send": "Invia",
      "chat.hello": "Ciao. Posso spiegarti l'analisi del tuo campo. Cosa vuoi sapere?",
      "chat.q1": "Ho abbastanza acqua?", "chat.q2": "Quando devo seminare?", "chat.q3": "Che coltura posso scegliere?", "chat.q4": "Come proteggo il mio suolo?",
      "chat.example": "Non ho irrigazione e voglio seminare mais la prossima settimana. Cosa devo fare?",
      "chat.typing": "Sta scrivendo…", "copilot.offline": "Offline. Riprova quando hai internet.",

      "layer.sat": "Satellite", "layer.rain": "Precipitazioni", "layer.wind": "Vento", "layer.temp": "Temperatura", "layer.solar": "Radiazione solare", "layer.soil": "Umidità del suolo", "layer.ndvi": "Vegetazione",
      "lg.rain": ["Debole", "Pioggia forte"], "lg.wind": ["Calmo", "Forte"], "lg.temp": ["Fresco", "Caldo"], "lg.solar": ["Bassa", "Intensa"], "lg.soil": ["Secco", "Umido"], "lg.ndvi": ["Stressata", "Sana"],
      "lg.sat": "Immagine satellitare del terreno",
      "lg.date": "Immagine del {d}", "lg.month": "Media di {d}",
      "in.sat": "Ecco il tuo terreno visto dal cielo.",
      "in.sat.more": "Allarga con due dita per vedere i tuoi campi. I livelli in basso mostrano i dati NASA intorno a te.",
      "in.rain.below": "Le piogge degli ultimi 60 giorni sono sotto la norma.",
      "in.rain.ok": "Le piogge degli ultimi 60 giorni sono vicine alla norma.",
      "in.rain.more": "Sono caduti {a} mm di pioggia. La norma nella tua zona è {b} mm.",
      "in.wind": "Il vento soffia a {s} km/h da {d}.",
      "in.wind.more": "Un vento forte secca più in fretta terra e foglie.",
      "in.wind.calm": "È un vento leggero: secca poco il suolo.",
      "in.temp.hot": "Fa caldo nella tua zona ({t} °C). Rischio di stress per le piante.",
      "in.temp.ok": "La temperatura è normale per la stagione ({t} °C).",
      "in.temp.more": "Con molto caldo, la coltura chiede più acqua ogni giorno.",
      "in.solar.high": "C'è molto sole nella tua zona.", "in.solar.ok": "Il sole è moderato.",
      "in.solar.more": "Più sole significa terra che si secca più in fretta. Il tuo suolo perde circa {et} mm d'acqua al giorno.",
      "in.soil.low": "L'umidità del suolo è bassa nella tua zona.", "in.soil.ok": "Il suolo è ben umido.",
      "in.soil.more": "Il satellite misura il {p}% d'acqua nella terra in superficie. Sotto il 20% è difficile seminare.",
      "in.ndvi.stress": "La vegetazione mostra segni di stress moderato.", "in.ndvi.ok": "La vegetazione della tua zona è sana.",
      "in.ndvi.more": "Le piante sono meno verdi di due mesi fa.", "in.ndvi.more_ok": "Le piante restano verdi da due mesi.",
      "in.need_water": "La tua coltura potrebbe aver bisogno di più acqua di quella disponibile.",
      "in.wait": "Ti consigliamo di aspettare prima di seminare o di valutare una rotazione più resistente.",
      "in.plant": "Le condizioni permettono di seminare nella finestra consigliata.",
      "dir": ["nord", "nord-est", "est", "sud-est", "sud", "sud-ovest", "ovest", "nord-ovest"],
      "no3d": "Il globo 3D non è disponibile su questo dispositivo.",
      "region": "America centrale",
    },
  };
  const LANGS = ["fr", "en", "it"];
  const LOCALE = { fr: "fr-FR", en: "en-US", it: "it-IT" };

  let lang = "fr";
  try { lang = localStorage.getItem("fs_lang") || "fr"; } catch (e) {}
  if (!DICT[lang]) lang = "fr";

  function t(key, vars) {
    let s = DICT[lang][key];
    if (s === undefined) s = DICT.fr[key];
    if (s === undefined) return key;
    if (vars && typeof s === "string") s = s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] !== undefined ? vars[k] : ""));
    return s;
  }
  function apply(root) {
    (root || document).querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
    (root || document).querySelectorAll("[data-t-ph]").forEach((el) => { el.placeholder = t(el.dataset.tPh); });
    (root || document).querySelectorAll("[data-t-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.tAria)); el.title = t(el.dataset.tAria); });
    document.querySelectorAll(".lang-seg button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.l === lang));
    document.documentElement.lang = lang;
  }
  function setLang(l) {
    lang = DICT[l] ? l : "fr";
    try { localStorage.setItem("fs_lang", lang); } catch (e) {}
    apply();
    document.dispatchEvent(new CustomEvent("fs:langchange", { detail: { lang } }));
  }
  function extend(more) { Object.keys(more).forEach((l) => { if (DICT[l]) Object.assign(DICT[l], more[l]); }); }
  window.FSI18N = { get lang() { return lang; }, get locale() { return LOCALE[lang]; }, t, apply, setLang, extend };

  /* ---------- Navigation : même menu pilule que le site public ---------- */
  const NAV = [
    { href: "/inicio.html", key: "nav.home", id: "home" },
    { href: "/globo.html", key: "nav.analyse", id: "analyse" },
    { href: "/", key: "nav.site", id: "site" },
  ];
  function renderNav() {
    const el = document.getElementById("nav");
    if (!el) return;
    const page = document.body.dataset.page;
    el.className = "nav";
    el.innerHTML = `
      <a class="brand" href="/inicio.html"><span class="brand-mark"><iconify-icon icon="lucide:sprout" width="18" height="18"></iconify-icon></span><span class="brand-name">Field Shift</span></a>
      <nav class="nav-links" id="nav-links" aria-label="Menu">
        ${NAV.map((n) => `<a href="${n.href}" ${n.id === page ? 'aria-current="page"' : ""}><span data-t="${n.key}"></span></a>`).join("")}
      </nav>
      <div class="nav-right">
        <div class="lang-seg" role="group" aria-label="Langue · Language · Lingua">
          ${LANGS.map((l) => `<button type="button" data-l="${l}" aria-pressed="${l === lang}">${l.toUpperCase()}</button>`).join("")}
        </div>
        ${page === "analyse" ? "" : `<a class="nav-cta" href="/globo.html"><span data-t="cta.analyse"></span><iconify-icon icon="lucide:arrow-right" width="16" height="16"></iconify-icon></a>`}
        <button type="button" class="nav-burger" aria-label="Menu" aria-expanded="false"><iconify-icon icon="lucide:menu" width="22" height="22"></iconify-icon></button>
      </div>`;
    el.querySelector(".lang-seg").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-l]");
      if (b && b.dataset.l !== lang) setLang(b.dataset.l);
    });
    const burger = el.querySelector(".nav-burger"), links = el.querySelector(".nav-links");
    burger.addEventListener("click", () => {
      const open = links.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", open);
    });
  }

  /* ---------- Fond animé : vue satellite réelle qui dérive (comme le site public) ---------- */
  function driftBg(el, opts) {
    if (!el || !window.maplibregl || !hasWebGL()) return null;
    const o = Object.assign({ center: [-87.255, 13.215], zoom: 14.2, pitch: 38, bearing: -20,
      path: [[-87.255, 13.215], [-87.215, 13.235], [-87.19, 13.205], [-87.235, 13.19]], ms: 26000 }, opts || {});
    const style = satStyle(false);
    style.projection = { type: "mercator" };
    delete style.sky;
    const map = new maplibregl.Map({ container: el, style, center: o.center, zoom: o.zoom, pitch: o.pitch, bearing: o.bearing,
      interactive: false, attributionControl: false, fadeDuration: 0 });
    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      let i = 0;
      const go = () => { i = (i + 1) % o.path.length; map.easeTo({ center: o.path[i], duration: o.ms, easing: (t) => t, bearing: map.getBearing() + 4 }); };
      map.on("moveend", go);
      map.once("load", go);
    }
    return map;
  }

  /* ---------- Helpers ---------- */
  function fmtDate(iso, opts) {
    const d = new Date(iso.length === 10 ? iso + "T12:00:00" : iso);
    return d.toLocaleDateString(LOCALE[lang], opts || { day: "numeric", month: "short" });
  }
  function fmtWindow(str) {
    const parts = String(str || "").split("→").map((s) => s.trim());
    if (parts.length !== 2) return str || "—";
    return `${fmtDate(parts[0])} – ${fmtDate(parts[1])}`;
  }
  function riskClass(level) { return level === "low" ? "low" : level === "high" ? "high" : "moderate"; }
  function wsClass(s) { return s === "enough_water" ? "ok" : s === "risky" ? "warn" : "bad"; }
  function plClass(s) { return s === "plant_now" ? "ok" : s === "wait" ? "warn" : "bad"; }
  let toastTimer;
  function toast(msg) {
    let el = document.getElementById("toast");
    if (!el) { el = document.createElement("div"); el.id = "toast"; el.className = "toast"; el.setAttribute("role", "status"); document.body.appendChild(el); }
    el.textContent = msg; el.classList.remove("hidden");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.add("hidden"), 3800);
  }
  function getPlace() { try { return JSON.parse(localStorage.getItem("fs_place") || "null"); } catch (e) { return null; } }
  function setPlace(p) { try { localStorage.setItem("fs_place", JSON.stringify(p)); } catch (e) {} }
  function fmtCoords(lat, lng) {
    const ns = lat >= 0 ? "N" : "S", ew = lng >= 0 ? "E" : (lang === "en" ? "W" : "O");
    return `${Math.abs(lat).toFixed(4)}° ${ns} · ${Math.abs(lng).toFixed(4)}° ${ew}`;
  }
  function hasWebGL() {
    try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); }
    catch (e) { return false; }
  }

  /* =====================================================
     Globe satellite (MapLibre GL, projection « globe »)
     - Fond : imagerie satellite réelle (Esri World Imagery) jusqu'au niveau du champ.
     - Couches NASA GIBS (vraies données) ajoutées par la page d'analyse.
     ===================================================== */
  const ESRI_SAT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
  const ESRI_LABELS = "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}";

  function satStyle(withLabels) {
    const style = {
      version: 8,
      projection: { type: "globe" },
      sky: {
        "sky-color": "rgba(6,16,26,0)", "horizon-color": "#7FB8E6", "fog-color": "rgba(6,16,26,0)",
        "sky-horizon-blend": 0.6, "horizon-fog-blend": 0.9, "fog-ground-blend": 0.95,
        "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 0.9, 8, 0],
      },
      sources: {
        sat: { type: "raster", tiles: [ESRI_SAT], tileSize: 256, maxzoom: 19, attribution: "Imagery © Esri, Maxar, Earthstar Geographics · NASA GIBS" },
      },
      layers: [
        { id: "space", type: "background", paint: { "background-color": "#0A1622" } },
        { id: "sat", type: "raster", source: "sat", paint: { "raster-fade-duration": 250 } },
      ],
    };
    if (withLabels) {
      style.sources.labels = { type: "raster", tiles: [ESRI_LABELS], tileSize: 256, maxzoom: 19 };
      style.layers.push({ id: "labels", type: "raster", source: "labels", paint: { "raster-opacity": 0.85 } });
    }
    return style;
  }

  /* Rotation lente du globe tant que personne ne le touche (style « observatoire »). */
  function spinGlobe(map, opts) {
    const o = Object.assign({ speed: 7, maxZoom: 4.5 }, opts || {});
    let paused = false, user = false;
    function step() {
      if (paused || user || map.getZoom() > o.maxZoom) return;
      const c = map.getCenter();
      c.lng -= o.speed;
      map.easeTo({ center: c, duration: 1000, easing: (n) => n });
    }
    const hold = () => { user = true; };
    const release = () => { user = false; step(); };
    map.on("mousedown", hold); map.on("touchstart", hold); map.on("dragstart", hold);
    map.on("mouseup", release); map.on("touchend", release);
    map.on("moveend", step);
    const collapse = () => { const a = map.getContainer().querySelector(".maplibregl-compact-show"); if (a) a.classList.remove("maplibregl-compact-show"); };
    if (map.loaded()) { collapse(); step(); } else map.once("load", () => { collapse(); step(); });
    return { pause() { paused = true; map.stop(); }, resume() { paused = false; step(); } };
  }

  /* Culture saisie librement → clé connue du moteur (sinon le texte tel quel). */
  function cropKey(text) {
    const s = String(text || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
    if (!s) return "maize";
    if (/\b(mais|maize|corn|granoturco|granturco)\b/.test(s)) return "maize";
    if (/(haricot|bean|fagiol|niebe|cowpea|frijol)/.test(s)) return "beans";
    if (/(sorgh|sorgo)/.test(s)) return "sorghum";
    if (/\b(mil|millet|miglio|petit mil)\b/.test(s)) return "millet";
    return s.slice(0, 40);
  }
  function cropLabel(p) {
    if (p && p.crop_label) return p.crop_label;
    const k = (p && p.crop) || "maize";
    const lab = t("crop." + k);
    return lab === "crop." + k ? k : lab;
  }

  window.Terra = {
    extend, cropKey, cropLabel,
    t, apply, renderNav, fmtDate, fmtWindow, riskClass, wsClass, plClass, toast,
    getPlace, setPlace, fmtCoords, hasWebGL, satStyle, spinGlobe, driftBg,
  };

  document.addEventListener("DOMContentLoaded", () => { renderNav(); apply(); });
})();
