import asyncio
import base64
import json
import os
from aiohttp import web
from vosk import Model, KaldiRecognizer

# Ładowanie modelu Vosk
print("Ładowanie modelu Vosk...", flush=True)
model = Model("model")  # upewnij się, że folder z modelem tak się nazywa
recognizer = KaldiRecognizer(model, 16000)
print("Model gotowy!", flush=True)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("[+] Sukces! Połączono z pluginem Minecraft.", flush=True)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    # Sprawdzamy czy to pakiet audio
                    audio_b64 = data.get("audio_data", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        process_audio(audio_bytes, recognizer)
                    else:
                        print(f"[Ostrzeżenie] Otrzymano JSON bez 'audio_data': {list(data.keys())}", flush=True)
                except json.JSONDecodeError:
                    print(f"[Błąd] Otrzymano niepoprawny JSON: {msg.data[:50]}...", flush=True)
                    
            elif msg.type == web.WSMsgType.BINARY:
                # Jeśli plugin wysyła czyste bajty PCM
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
