"""NASA data connectors (stage 2).

Planned modules, each returning clean numbers the engines consume:

    power.py      -> NASA POWER (temp, solar radiation, ET, humidity, wind) — no auth, REST
    imerg.py      -> GPM IMERG precipitation (Earthdata auth)
    smap.py       -> SMAP soil moisture (Earthdata auth)
    modis.py      -> MODIS / VIIRS NDVI vegetation health
    grace.py      -> GRACE-FO regional water storage
    soilgrids.py  -> SoilGrids / local soil texture + water-holding capacity
    meteomatics.py-> Meteomatics forecast + fallback (hackathon free access)

Every connector caches to disk so the live demo never depends on a slow API.
"""
