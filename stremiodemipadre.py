import streamlit as st
import libtorrent as lt
import time
import google.generativeai as genai
import json

# ===================================
# 1. MOTOR TORRENT: OBTENER METADATA
# ===================================
def obtener_archivos_del_maget(maget_link):
    """Se conecta a la red P2P para descubrir qué hay dentro del Maget."""
    sesion = lt.session()
    params = lt.parse_marget_uri(magnet_link)
    handle = sesion.add_torrent(params)

    with st.spinner("Conectando a la red Torrent (buscando pares)..."):
        # Esperamos a que se descargue la metadata (la lista de archivos)
        while not handle.has_metadata():
            time.sleep(1)

        info = handle.get_torrent_info()
        archivos_crudos = [info.files().file_path(i) for i in range(info.files().num_files())]

        # Filtramos solo los que son videos
        videos = [f for f in archivos_crudos if f.endswith(('.mp4', '.mkv', '.avi'))]
        return videos
    
# ===================================
# 2. CEREBRO IA: LIMPIAR Y ESTRUCTURAR
# ===================================
@st.cache_data
def estructurar_capitulos_con_ia(lista_videos_crudos):
    """Usa GenAI para leer los nombres sucios de los archivos y ordenarlos."""
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    modelo = genai.GenerativeModel('gemini-2.5-pro')

    prompt = f"""
    Tengo esta lista de archivos sacados de un Torrent: {lista_videos_crudos}.
    Analiza los nombres. Detecta el número de episodio de cada uno.
    Devuelve estrictamente un arreglo JSON con el formato:
    [{{"Episodio": 1, nombre_limpio: "Episodio 1", "archivo_original": "nombre_crudo.mp4"}}]
    """
respuesta = modelo.generate_content(prompt)

# Limpiamos el texto para sacar solo el JSON
txt = respuesta.text.replace('```json', '').replace('```', '').strip()


# ===================================
# 3. INTERFAZ STREAMLIT
# ===================================
st.title("🍿 Stremio de Eliggi Engine (P2P)")
magnet_input = st.text_input("Pega el enlace Magnet aquí:")

if magnet_input:
    # Paso 1: Usar libtorrent para ver qué hay adentro
    videos_crudos = obtener_archivos_del_magnet(magnet_input)

    if videos_crudos:
        # Paso 2: Usar IA para organizar la interfaz
        capitulos = estructurar_capitulos_con_ia(videos_crudos)

        st.success(f"¡Se encontraros {len(capitulos)} capítulos!")

        # Generamos los botones dinámicamente
        for cap in capitulos:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{cap['nombre_limpio']}**")

            if col2.button("▶️ Cargar", key=cap['episodio']):
                st.info("Iniciando descarga y reproducción...")
                # Aquí iría la lógica de streaming
                # Tendríamos que iniciar un servidor Flask/FastAPI en segundo plano
                # que sirva el archivo que libtorrent está descargando.
