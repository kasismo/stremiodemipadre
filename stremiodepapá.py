import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd


st.set_page_config(page_title="Eliggi Stremio", page_icon="🍿", layout="wide")

# ==========================================
# --- 1. MEMORIA Y ESTADO ---
# ==========================================
# Aquí guardamos qué película está viendo el usuario para no perderla al recargar
if 'pelicula_seleccionada' not in st.session_state:
    st.session_state['pelicula_seleccionada'] = None

# ==========================================
# --- 2. CONEXIÓN A LA BÓVEDA (SUPABASE) ---
# ==========================================
@st.cache_resource
def iniciar_conexion():
    """Conecta a la base de datos una sola vez para máxima velocidad."""
    return create_engine("DB_URI")

motor = iniciar_conexion()

def obtener_catalogo():
    """Trae toda la cartelera."""
    query = text("SELECT id, titulo, sinopsis, poster_url FROM contenido")
    with motor.connect()as conexion:
        return pd.read_sql(query, conexion)
    
def obtener_fuentes(contenido_id):
    """Busca los 'links' exactos que coincidan con la película seleccionada."""
    query = text("SELECT, calidad, tipo, url_video FROM fuentes WHERE contenido_id = :id")
    with motor.connect() as conexion:
        return pd.read_sql(query, conexion, params={"id": contenido_id})

# ==========================================
# --- 3. INTERFAZ GRÁFICA (EL FRONTEND) ---
# ==========================================
st.title("🍿 Eliggi Nuestro Stremio")
# ---> VISTA A: EL CATÁLOGO <---
if st.session_state['pelicula_seleccionada'] is None:
    st.subheader("Catálogo Disponible")
    
    try:
        df_catalogo = obtener_catalogo()
        
        if df_catalogo.empty:
            st.info("La base de datos está vacía. Añade tu primera película en Supabase.")
        else:
            # Creamos una cuadrícula dinámica (4 pósters por fila)
            columnas_por_fila = 4
            filas = [st.columns(columnas_por_fila) for _ in range((len(df_catalogo) // columnas_por_fila) + 1)]
            
            for index, fila in df_catalogo.iterrows():
                col = filas[index // columnas_por_fila][index % columnas_por_fila]
                with col:
                    # Dibujamos el póster y el título
                    st.image(fila['poster_url'], use_container_width=True)
                    st.markdown(f"**{fila['titulo']}**")
                    
                    # El botón mágico que cambia la vista
                    if st.button("▶️ Reproducir", key=f"btn_{fila['id']}", use_container_width=True):
                        st.session_state['pelicula_seleccionada'] = fila.to_dict()
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")

# ---> VISTA B: LA SALA DE CINE <---
else:
    peli = st.session_state['pelicula_seleccionada']
    
    # Botón de escape
    if st.button("⬅️ Volver al Catálogo"):
        st.session_state['pelicula_seleccionada'] = None
        st.rerun()
        
    st.divider()
    
    # Dividimos la pantalla: Izquierda info, Derecha video
    col_info, col_video = st.columns([1, 2])
    
    with col_info:
        st.image(peli['poster_url'], use_container_width=True)
        st.title(peli['titulo'])
        st.write(peli['sinopsis'])
        
    with col_video:
        st.subheader("Reproductor")
        
        # Consultamos a los "Addons" (Nuestra tabla de fuentes)
        df_fuentes = obtener_fuentes(peli['id'])
        
        if df_fuentes.empty:
            st.warning("Aún no hay enlaces de video disponibles para este título.")
        else:
            # Simulamos el selector de servidores de Stremio
            opciones_fuente = df_fuentes['calidad'] + " - " + df_fuentes['tipo']
            fuente_elegida = st.selectbox("Selecciona un servidor:", opciones_fuente)
            
            # Filtramos la URL exacta según lo que eligió el usuario
            url_reproducir = df_fuentes.loc[opciones_fuente == fuente_elegida, 'url_video'].values[0]
            
            # Encendemos el reproductor nativo
            st.video(url_reproducir)
            st.caption(f"Transmitiendo mágicamente desde: {url_reproducir}")