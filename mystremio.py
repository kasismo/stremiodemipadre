from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

# TU LLAVE DE GOOGLE ACA
GOOGLE_API_KEY = "AIzaSyDc2SOs8D3v8lnq9120JdFX6LDpgnhOBaw"

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

    # 3. El generador que escupe los bytes a la televisión
    async def video_streamer():
        try:
            async for chunk in response.aiter_bytes(chunk_size=1024 * 1024): # Pedazos de 1MB
                yield chunk
        finally:
            # 4. CRUCIAL: Cuando la tele deja de pedir video, cerramos todo para liberar memoria RAM
            await response.aclose()
            await client.aclose()

    return StreamingResponse(
        video_streamer(),
        status_code=response.status_code,
        headers=dict(response.headers)
    )
