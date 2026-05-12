from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

# Tu llave maestra de Google
GOOGLE_API_KEY = "AIzaSyDc2SOs8D3v8lnq9120JdFX6LDpgnhOBaw"

@app.get("/stream/{video_id}")
async def stream_video(video_id: str, request: Request):
    """
    Este endpoint es el que va a llamar la televisión.
    Recibe el ID del video y los 'Headers' (como el rango de bytes que pide ExoPlayer).
    """
    # 1. Armamos la URL oficial de Google Drive
    drive_url = f"https://www.googleapis.com/drive/v3/files/{video_id}?alt=media&key={GOOGLE_API_KEY}"
    
    # 2. Capturamos el "Range" que pide la TV (ej: "bytes=1000-2000")
    headers = {}
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header # Pasamos la petición de ExoPlayer intacta a Drive

    # 3. Nos conectamos a Google Drive pasándole el rango solicitado
    # Usamos un cliente asincrónico para no bloquear el servidor
    # El Timeout(None) le dice a Python que mantenga la conexión viva el tiempo que haga falta
    client = httpx.AsyncClient(timeout=httpx.Timeout(None))
    
    # Hacemos la petición a Google (stream=True es la clave para no descargar todo de golpe)
    req = client.build_request("GET", drive_url, headers=headers)
    response = await client.send(req, stream=True)

    # Si Google nos tira un error (ej. 404 o 403), le avisamos a la TV
    if response.status_code not in (200, 206):
        await response.aclose()
        raise HTTPException(status_code=response.status_code, detail="Error al contactar a Drive")

    # 4. Esta es la función generadora que va escupiendo los bytes a la TV
    async def video_streamer():
        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024): # Leemos de a 1MB
            yield chunk
        await response.aclose()

    # 5. Respondemos a la TV con el flujo constante de bytes y el código correcto (206 Partial Content)
    return StreamingResponse(
        video_streamer(),
        status_code=response.status_code,
        headers=dict(response.headers)
    )
