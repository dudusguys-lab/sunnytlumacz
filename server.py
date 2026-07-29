import asyncio
import base64
import json
import os
import urllib.request
import zipfile
from aiohttp import web
from vosk import Model, KaldiRecognizer

MODEL_PATH = "model"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-pl-0.22.zip"
ZIP_NAME = "model.zip"

# Automatyczne pobieranie i rozpakowywanie modelu, jeśli go nie ma
if not os.path.exists(MODEL_PATH):
    print("Pobieram polski model Vosk z internetu...", flush=True)
    try:
        urllib.request.urlretrieve(MODEL_URL, ZIP_NAME)
        print("Rozpakowywuję model...", flush=True)
        with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Znajdź rozpakowany folder i zmień nazwę na "model"
        for name in os.listdir("."):
            if os.path.isdir(name) and name.startswith("vosk-model"):
                os.rename(name, MODEL_PATH)
                break
                
        if os.path.exists(ZIP_NAME):
            os.remove(ZIP_NAME)
        print("Model gotowy!", flush=True)
    except Exception as e:
        print(f"[Błąd pobierania modelu]: {e}", flush=True)

print("Ładowanie modelu Vosk do pamięci...", flush=True)
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)
print("Model załadowany pomyślnie!", flush=True)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("[+] Sukces! Połączono z pluginem Minecraft.", flush=True)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    audio_b64 = data.get("audio_data", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        process_audio(audio_bytes, recognizer)
                except json.JSONDecodeError:
                    pass
                    
            elif msg.type == web.WSMsgType.BINARY:
                process_audio(msg.data, recognizer)
                
    except Exception as e:
        print(f"[Krytyczny błąd połączenia WS]: {e}", flush=True)
        
    print("[-] Rozłączono z klientem.", flush=True)
    return ws

def process_audio(audio_bytes, rec):
    if rec.AcceptWaveform(audio_bytes):
        result = json.loads(rec.Result())
        text = result.get("text", "").strip()
        if text:
            print(f"[MOWA]: {text}", flush=True)
    else:
        partial = json.loads(rec.PartialResult()).get("partial", "").strip()
        if partial:
            print(f"[Słyszę fragment]: {partial}", flush=True)

app = web.Application()
app.router.add_get('/', websocket_handler)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, port=port)
