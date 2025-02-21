import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
import os
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Carregar variables d'entorn
load_dotenv()

# Configuración de APIs
try:
    # Primer intentem obtenir la clau dels secrets de Streamlit (per la versió online)
    GOOGLE_PLACES_API_KEY = st.secrets["GOOGLE_PLACES_API_KEY"]
except:
    # Si no funciona, intentem obtenir-la del fitxer .env (per desenvolupament local)
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

if not GOOGLE_PLACES_API_KEY:
    st.error("❌ No s'ha trobat la clau de l'API de Google Places. L'aplicació no funcionarà correctament.")
    st.info("👉 Si estàs executant l'aplicació localment, assegura't de tenir un fitxer .env amb la clau API.")
    st.info("👉 Si estàs al servidor de Streamlit, configura la clau API als Secrets del projecte.")
    st.stop()

#LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY", "")

# Tipos de lugares relevantes para STEAM
TIPOS_VALIDOS = {
    'university',           # Universitats
    'school',              # Escoles
    'research_institute',   # Instituts de recerca
    'museum',              # Museus
    'science_museum',      # Museus de ciència
    'library',             # Biblioteques
    'laboratory',          # Laboratoris
    'educational_institution', # Institucions educatives
    'college',             # Facultats
    'institute',           # Instituts
    'technology_park'      # Parcs tecnològics
}

# Tipos a excluir explícitamente
TIPOS_EXCLUIDOS = {
    'restaurant',
    'bar',
    'cafe',
    'food',
    'store',
    'shop',
    'lodging',
    'hotel'
}

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# Colors per cada tipus d'institució
TIPOS_COLORES = {
    'university': 'red',           # Vermell per universitats
    'school': 'blue',             # Blau per escoles
    'research_institute': 'green', # Verd per instituts de recerca
    'museum': 'purple',           # Lila per museus
    'science_museum': 'purple',    # Lila per museus de ciència
    'library': 'orange',          # Taronja per biblioteques
    'laboratory': 'darkred',      # Vermell fosc per laboratoris
    'educational_institution': 'darkblue', # Blau fosc per institucions educatives
    'college': 'red',             # Vermell per facultats
    'institute': 'green',         # Verd per instituts
    'technology_park': 'darkgreen' # Verd fosc per parcs tecnològics
}

# Función para buscar contactos en LinkedIn
def buscar_linkedin(nombre_institucion, website):
    contactos = []
    if LINKEDIN_API_KEY:
        try:
            # Aquí aniria la crida a l'API de LinkedIn
            pass
        except Exception as e:
            st.warning(f"Error al connectar amb LinkedIn: {str(e)}")
    else:
        # Cerca bàsica sense API
        linkedin_url = f"https://www.linkedin.com/company/{nombre_institucion.lower().replace(' ', '-')}"
        contactos.append({
            "url": linkedin_url,
            "mensaje": "Visita el perfil de LinkedIn de la institució"
        })
    return contactos

# Función para buscar emails en una página web
def buscar_emails(website):
    if not website or website == "No disponible":
        return []
    
    emails = set()
    paginas_visitadas = set()
    
    def extraer_emails_de_texto(texto):
        patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(patron_email, texto)
    
    def analizar_pagina(url):
        if url in paginas_visitadas or len(paginas_visitadas) > 5:
            return
        
        try:
            # Configurar la sessió amb paràmetres més permissius
            session = requests.Session()
            session.verify = False  # Desactivar verificació SSL
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Intentar primer amb HTTPS
            try:
                response = session.get(url, timeout=10)
            except:
                # Si falla HTTPS, provar amb HTTP
                if url.startswith('https://'):
                    url = url.replace('https://', 'http://')
                    response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar en el texto
                emails.update(extraer_emails_de_texto(response.text))
                
                # Buscar específicament en pàgines de contacte
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    text = link.text.lower()
                    if 'contact' in text or 'contacte' in text or 'contacto' in text:
                        try:
                            next_url = urljoin(url, href)
                            if next_url not in paginas_visitadas:
                                paginas_visitadas.add(next_url)
                                analizar_pagina(next_url)
                        except:
                            continue
                            
        except Exception as e:
            # Reduïm el nivell de detall dels errors per no omplir la interfície
            st.warning(f"No s'ha pogut accedir a {url}")
    
    # Desactivar els warnings de SSL
    import warnings
    import urllib3
    warnings.filterwarnings('ignore')
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    analizar_pagina(website)
    return list(emails)

# Función para obtener detalles adicionales de un lugar
def obtener_detalles_lugar(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,opening_hours,rating,review&key={GOOGLE_PLACES_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        detalles = response.json().get("result", {})
        website = detalles.get("website", "No disponible")
        
        # Buscar contactes adicionals
        linkedin_info = buscar_linkedin(detalles.get("name", ""), website)
        emails = buscar_emails(website)
        
        return {
            "Telèfon": detalles.get("formatted_phone_number", "No disponible"),
            "Web": website,
            "Valoració": detalles.get("rating", "No disponible"),
            "LinkedIn": linkedin_info[0]["url"] if linkedin_info else "No disponible",
            "Emails": ", ".join(emails) if emails else "No disponible"
        }
    return None

# Función para buscar instituciones científicas en Google Places
def buscar_google_places(ubicacion, tipos):
    datos = []
    for tipo in tipos:
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={tipo}+in+{ubicacion}&key={GOOGLE_PLACES_API_KEY}"
        response = requests.get(url)
        resultados = response.json().get("results", [])
        
        for lugar in resultados:
            # Obtenir els tipus del lloc
            tipos_lugar = set(lugar.get("types", []))
            
            # Comprovar si és un tipus vàlid i no està en els exclosos
            if (tipos_lugar & TIPOS_VALIDOS) and not (tipos_lugar & TIPOS_EXCLUIDOS):
                detalles = obtener_detalles_lugar(lugar.get("place_id"))
                datos.append({
                    "Nombre": lugar.get("name", "N/A"),
                    "Dirección": lugar.get("formatted_address", "N/A"),
                    "Latitud": lugar["geometry"]["location"]["lat"],
                    "Longitud": lugar["geometry"]["location"]["lng"],
                    "Tipus": ", ".join(tipos_lugar & TIPOS_VALIDOS),  # Mostrem només els tipus rellevants
                    "Telèfon": detalles.get("Telèfon", "No disponible") if detalles else "No disponible",
                    "Web": detalles.get("Web", "No disponible") if detalles else "No disponible",
                    "Valoració": detalles.get("Valoració", "No disponible") if detalles else "No disponible",
                    "LinkedIn": detalles.get("LinkedIn", "No disponible") if detalles else "No disponible",
                    "Emails": detalles.get("Emails", "No disponible") if detalles else "No disponible",
                    "Fuente": "Google Places"
                })
                # Afegir un petit delay per no sobrecarregar les APIs
                time.sleep(0.5)
    return datos

# Función para buscar en OpenStreetMap
def buscar_openstreetmap(lat, lon, tipos, radio=5000):
    datos = []
    for tipo in tipos:
        query = f"""
        [out:json];
        node(around:{radio},{lat},{lon})["amenity"="{tipo}"];
        out body;
        """
        response = requests.get(OVERPASS_URL, params={'data': query})
        resultados = response.json().get("elements", [])
        
        for lugar in resultados:
            datos.append({
                "Nombre": lugar.get("tags", {}).get("name", "Desconocido"),
                "Dirección": "No disponible",
                "Latitud": lugar.get("lat"),
                "Longitud": lugar.get("lon"),
                "Fuente": "OpenStreetMap"
            })
    return datos

def get_marker_color(tipos):
    """Retorna el color del marcador segons el tipus d'institució"""
    for tipo in tipos:
        if tipo in TIPOS_COLORES:
            return TIPOS_COLORES[tipo]
    return 'gray'  # Color per defecte

# Interfaz en Streamlit
st.title("🔍 Agent - DTecla per facilitar la búsqueda de Referents STEAM ")

st.markdown("""
### Tipus d'institucions que busquem:
- 🔴 Universitats i Facultats
- 🟢 Instituts de Recerca
- 🟣 Museus de Ciència
- 🟠 Biblioteques especialitzades
- 🟤 Laboratoris
- 🟢 Parcs Tecnològics
""")

ubicacion = st.text_input("Introdueix una ciutat o coordenades (lat,lon):")

palabras_clave = ["science", "technology", "engineering", "mathematics", "art", "steam", "university", "research_institute"]

if st.button("Buscar Referents"):
    if ubicacion:
        try:
            # Contenidors per actualitzacions en temps real
            progress_container = st.empty()
            results_container = st.container()
            map_container = st.container()
            
            with results_container:
                st.write("### Resultats de la cerca:")
                df = pd.DataFrame()
                table_placeholder = st.empty()
                table_placeholder.dataframe(df)
            
            resultados = []
            markers_to_add = []  # Llista per acumular els marcadors
            
            if "," in ubicacion:  # Si se ingresan coordenadas
                lat, lon = map(float, ubicacion.split(","))
                with progress_container:
                    st.info("Cercant en OpenStreetMap...")
                resultados_osm = buscar_openstreetmap(lat, lon, tipos=palabras_clave)
                for lugar in resultados_osm:
                    resultados.append(lugar)
                    markers_to_add.append({
                        "location": [lugar["Latitud"], lugar["Longitud"]],
                        "popup": lugar["Nombre"],
                        "color": "red"
                    })
                
                df = pd.DataFrame(resultados)
                table_placeholder.dataframe(df)
            else:
                total_tipos = len(palabras_clave)
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                for i, tipo in enumerate(palabras_clave, 1):
                    status_text.text(f"Cercant {tipo}... ({i}/{total_tipos})")
                    progress_bar.progress(i/total_tipos)
                    
                    try:
                        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={tipo}+in+{ubicacion}&key={GOOGLE_PLACES_API_KEY}"
                        response = requests.get(url)
                        places_results = response.json().get("results", [])
                        
                        for lugar in places_results:
                            try:
                                tipos_lugar = set(lugar.get("types", []))
                                if (tipos_lugar & TIPOS_VALIDOS) and not (tipos_lugar & TIPOS_EXCLUIDOS):
                                    detalles = obtener_detalles_lugar(lugar.get("place_id"))
                                    if detalles:  # Només afegim si hem pogut obtenir els detalls
                                        nuevo_lugar = {
                                            "Nombre": lugar.get("name", "N/A"),
                                            "Dirección": lugar.get("formatted_address", "N/A"),
                                            "Latitud": lugar["geometry"]["location"]["lat"],
                                            "Longitud": lugar["geometry"]["location"]["lng"],
                                            "Tipus": ", ".join(tipos_lugar & TIPOS_VALIDOS),
                                            "Telèfon": detalles.get("Telèfon", "No disponible"),
                                            "Web": detalles.get("Web", "No disponible"),
                                            "Valoració": detalles.get("Valoració", "No disponible"),
                                            "LinkedIn": detalles.get("LinkedIn", "No disponible"),
                                            "Emails": detalles.get("Emails", "No disponible"),
                                            "Fuente": "Google Places"
                                        }
                                        resultados.append(nuevo_lugar)
                                        
                                        # Afegir marcador a la llista
                                        color = get_marker_color(tipos_lugar & TIPOS_VALIDOS)
                                        markers_to_add.append({
                                            "location": [nuevo_lugar["Latitud"], nuevo_lugar["Longitud"]],
                                            "popup": f"{nuevo_lugar['Nombre']}<br>Tipus: {nuevo_lugar['Tipus']}",
                                            "color": color
                                        })
                                        
                                        # Actualitzar només la taula
                                        df = pd.DataFrame(resultados)
                                        table_placeholder.dataframe(df)
                            except:
                                continue
                            
                            time.sleep(0.5)
                    except:
                        continue
                
                progress_container.empty()
            
            # Un cop tenim tots els resultats, mostrem el mapa
            if resultados:
                with map_container:
                    st.write("### Mapa de Referents STEAM:")
                    # Calcular el centre del mapa
                    center_lat = sum(r["Latitud"] for r in resultados) / len(resultados)
                    center_lon = sum(r["Longitud"] for r in resultados) / len(resultados)
                    
                    # Crear el mapa
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
                    
                    # Afegir tots els marcadors
                    for marker in markers_to_add:
                        folium.Marker(
                            marker["location"],
                            popup=marker["popup"],
                            icon=folium.Icon(color=marker["color"], icon='info-sign')
                        ).add_to(m)
                    
                    # Mostrar el mapa
                    folium_static(m)
                
                st.success(f"S'han trobat {len(resultados)} resultats!")
                st.download_button("Descargar Resultados", df.to_csv(index=False), "resultados.csv", "text/csv")
            else:
                st.warning("No s'han trobat resultats per aquesta ubicació.")
                
        except Exception as e:
            st.error("Hi ha hagut un error en la cerca. Si us plau, torna-ho a provar.")
    else:
        st.error("Si us plau, introdueix una ubicació vàlida.")