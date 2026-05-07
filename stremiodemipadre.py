import streamlit as st
import google.generativeai as genai
import libtorrent as lt
import json
import time

st.set_page_config(page_title="Eliggi Stremio P2P", page_icon="🍿", layout="wide")

# ==========================================
# --- 1. CONFIGURACIÓN Y ESTADO ---
# ==========================================
genai.configure(api_key="TU_API_KEY_DE_GEMINI") # <--- PON TU CLAVE AQUÍ

if 'catalogo_magnet' not in st.session_state:
    st.session_state['catalogo_magnet'] = None
if 'episodio_actual' not in st.session_state:
    st.session_state['episodio_actual'] = None

# ==========================================
# --- 2. HERRAMIENTAS DEL BACKEND ---
# ==========================================
def extraer_metadata_torrent(magnet_link):
    """Se conecta a la red P2P solo para leer qué archivos contiene el enlace."""
    sesion = lt.session()
    sesion.listen_on(6881, 6891)
    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = "."
    
    handle = sesion.add_torrent(params)
    
    intentos = 0
    # Esperamos a que los 'peers' nos den el índice del archivo
    while not handle.has_metadata():
        time.sleep(1)
        intentos += 1
        if intentos > 45: # Timeout de 45 segundos
            return None
            
    info = handle.get_torrent_info()
    archivos = [info.files().file_path(i) for i in range(info.files().num_files())]
    # Filtramos la basura (archivos .txt, .nfo) y dejamos solo video
    return [f for f in archivos if f.lower().endswith(('.mp4', '.mkv', '.avi'))]

def procesar_con_ia(lista_archivos):
    """Gemini lee los nombres crudos y devuelve una estructura perfecta para la UI."""
    modelo = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Eres el backend de una app de streaming. Extrae la información de esta lista cruda: {lista_archivos}
    Devuelve ÚNICAMENTE un array JSON válido con este formato exacto:
    [
        {{"episodio": 1, "titulo": "Episodio 1", "archivo_crudo": "ruta_original.mp4"}}
    ]
    Ordena los episodios de menor a mayor. Si es una película, pon "episodio": 1.
    """
    try:
        respuesta = modelo.generate_content(prompt)
        txt = respuesta.text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except:
        return None

# ==========================================
# --- 3. INTERFAZ DE USUARIO ---
# ==========================================
st.title("🍿 Eliggi Stremio (Motor P2P)")
st.markdown("Pega un enlace Magnet. La IA lo auditará y preparará el servidor de streaming local.")

# BARRA DE BÚSQUEDA MAGNET
magnet_input = st.text_input("🔗 Enlace Magnet:", placeholder="magnet:?xt=urn:btih:...")

if st.button("🔍 Auditar Enlace", type="primary"):
    if magnet_input:
        with st.spinner("Conectando a la red Torrent mundial... (Esto puede tardar según los seeds)"):
            archivos_crudos = extraer_metadata_torrent(magnet_input)
            
        if archivos_crudos:
            with st.spinner("🧠 Gemini está estructurando los capítulos..."):
                catalogo_limpio = procesar_con_ia(archivos_crudos)
                
            if catalogo_limpio:
                st.session_state['catalogo_magnet'] = catalogo_limpio
                st.session_state['episodio_actual'] = None
                st.success("✅ ¡Enlace procesado con éxito!")
            else:
                st.error("La IA no pudo procesar los nombres de los archivos.")
        else:
            st.error("No se encontró metadata. El enlace puede estar muerto o no tener 'seeds'.")

st.divider()

# RENDERIZADO DEL CATÁLOGO
if st.session_state['catalogo_magnet']:
    col_menu, col_reproductor = st.columns([1, 2])
    
    # Menú lateral con los botones de episodios
    with col_menu:
        st.subheader("📑 Capítulos")
        for cap in st.session_state['catalogo_magnet']:
            # Streamlit dibuja un botón por cada capítulo que detectó la IA
            if st.button(f"▶️ {cap['titulo']}", key=f"btn_{cap['episodio']}", use_container_width=True):
                st.session_state['episodio_actual'] = cap
                
    # Zona del Reproductor
    with col_reproductor:
        if st.session_state['episodio_actual']:
            cap_actual = st.session_state['episodio_actual']
            st.subheader(f"Reproduciendo: {cap_actual['titulo']}")
            
            st.info(f"Archivo interno: `{cap_actual['archivo_crudo']}`")
            
            # 🔥 LA CONEXIÓN CON TU MOTOR FASTAPI LOCAL 🔥
            # Aquí asumimos que tu FastAPI (main.py) está corriendo en el puerto 8000
            # Le pasamos el nombre del archivo como parámetro para que sepa qué streamear
            url_stream_local = f"http://localhost:8000/stream?file={cap_actual['archivo_crudo']}"
            
            # Encerramos en un try/except por si el motor de FastAPI está apagado
            try:
                st.video(url_stream_local)
                st.caption("⚡ Streaming impulsado por FastAPI y HTTP 206")
            except:
                st.warning("⚠️ No se puede cargar el video. ¿Está encendido el servidor FastAPI en el puerto 8000?")
        else:
            st.info("👈 Selecciona un capítulo para iniciar la transmisión local.")
