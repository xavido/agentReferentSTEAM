# Cercador de Referents STEAM

Aquest agent d'IA permet cercar institucions STEAM (Science, Technology, Engineering, Arts, Mathematics) en una ubicació específica utilitzant l'API de Google Places i OpenStreetMap.

## Característiques

- 🎯 Cerca intel·ligent d'institucions STEAM
- 🗺️ Visualització en mapa interactiu
- 📊 Resultats detallats amb informació de contacte
- 🎨 Marcadors de colors segons el tipus d'institució
- 📧 Cerca automàtica d'emails de contacte
- 🔗 Integració amb LinkedIn

## Tipus d'institucions que cerca

- 🔴 Universitats i Facultats
- 🟢 Instituts de Recerca
- 🟣 Museus de Ciència
- 🟠 Biblioteques especialitzades
- 🟤 Laboratoris
- 🟢 Parcs Tecnològics

## Requisits previs

- Python 3.7 o superior
- Clau API de Google Places

## Instal·lació

1. Instal·la les dependències:
```bash
pip install streamlit pandas requests folium streamlit-folium python-dotenv beautifulsoup4
```

2. Crea un arxiu `.env` a l'arrel del projecte i afegeix la teva clau API de Google Places:
```
GOOGLE_PLACES_API_KEY=la_teva_clau_api
```

## Ús

Executa l'aplicació amb Streamlit:
```bash
streamlit run dtecla_STEAM_finder.py
```

### Com utilitzar-lo

1. Introdueix una ubicació (per exemple: "Barcelona") o coordenades (per exemple: "41.3851,2.1734")
2. Fes clic a "Buscar Referents"
3. L'aplicació mostrarà:
   - Taula amb tots els resultats trobats
   - Mapa interactiu amb marcadors de colors
   - Informació detallada de cada institució:
     - Nom i adreça
     - Tipus d'institució
     - Telèfon i web
     - Enllaç a LinkedIn
     - Emails de contacte
4. Pots descarregar els resultats en format CSV

## Notes

- Els resultats es filtren automàticament per evitar establiments no relacionats amb STEAM
- La cerca d'emails analitza les pàgines web de les institucions
- Els marcadors al mapa tenen colors diferents segons el tipus d'institució
- Es poden fer cerques tant per nom de ciutat com per coordenades geogràfiques 