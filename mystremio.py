from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

# TU LLAVE DE GOOGLE ACA
GOOGLE_API_KEY = "AIzaSyAULjBpVODNPLgkP547iETBPQyTbusuMxI"

@app.get("/")
async def home():
    return {"status": "Servidor de EliggiStremio activo y funcionando 🚀"}

@app.get("/stream/{video_id}")
async def stream_video(video_id: str):
    # Armamos el link directo al CDN de Google Drive
    drive_url = f"https://www.googleapis.com/drive/v3/files/{video_id}?alt=media&key={GOOGLE_API_KEY}"
    
    # El Redireccionamiento: Le pasamos la carga pesada a los servidores de Google
    return RedirectResponse(url=drive_url, status_code=307)
