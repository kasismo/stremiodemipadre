from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

# TU LLAVE DE GOOGLE ACA
GOOGLE_API_KEY = "AIzaSyAULjBpVODNPLgkP547iETBPQyTbusuMxI"

@app.get("/")
async def home():
    return {"status": "Servidor de EliggiStremio activo y funcionando 🚀"}

@app.get("/stream/{video_id}")
async def stream_video(video_id: str, request: Request):
    drive_url = f"https://www.googleapis.com/drive/v3/files/{video_id}?alt=media&key={GOOGLE_API_KEY}"
    
    # 1. Capturamos el Range para permitir adelantar y retroceder el video
    headers = {}
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header

    # 2. Cliente SIN límite de tiempo para que no corte la película
    client = httpx.AsyncClient(timeout=None)
    
    req = client.build_request("GET", drive_url, headers=headers)
    
    try:
        response = await client.send(req, stream=True)
    except Exception as e:
        await client.aclose()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    if response.status_code not in (200, 206):
        await response.aclose()
        await client.aclose()
        raise HTTPException(status_code=response.status_code, detail="Google Drive bloqueó la petición")

    # ---------------------------------------------------------
    # LA SOLUCIÓN: El Filtro estricto de cabeceras para ExoPlayer
    # (Ahora está correctamente fuera del 'if' de errores)
    # ---------------------------------------------------------
    clean_headers = {}
    
    # Solo dejamos pasar estos 4 datos vitales. Todo lo demás se descarta.
    for header_name in ["Content-Length", "Content-Range", "Content-Type"]:
        # httpx guarda las cabeceras en minúscula internamente
        if header_name.lower() in response.headers:
            clean_headers[header_name] = response.headers[header_name.lower()]
            
    # Le gritamos a la tele que SÍ soportamos que adelante y atrase la película
    clean_headers["Accept-Ranges"] = "bytes"

    # 3. El generador que escupe los bytes
    async def video_streamer():
        try:
            async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    # Pasamos clean_headers en lugar del dict() entero
    return StreamingResponse(
        video_streamer(),
        status_code=response.status_code,
        headers=clean_headers
    )
