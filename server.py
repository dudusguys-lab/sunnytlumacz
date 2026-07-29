import os
import json
from aiohttp import web
from vosk import Model, KaldiRecognizer
from deep_translator import GoogleTranslator

# 1. Pobieranie / ładowanie modelu Vosk
print("Ładowanie modelu językowego Vosk (Polski)...", flush=True)
model = Model(lang="pl")
print("Model załadowany pomyślnie!", flush=True)

translator = GoogleTranslator(source='auto', target='en')

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>MC Translator Status</title>
    <style>
        body { font-family: sans-serif; background-color: #121212; color: #e0e0e0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background-color: #1e1e1e; padding: 40px; border-radius: 12px; text-align: center; }
        .status { background-color: #2e7d32; color: #fff; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin-top: 15px; display: inline-block; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Sunny Translator</h1>
        <p>Serwer tłumaczeń dla Minecrafta</p>
        <div class="status">● SERWER DZIAŁA</div>
    </div>
</body>
</html>
"""

async def handle_request(request):
    # Sprawdzenie czy to połączenie WebSocket
    if request.headers.get("Upgrade", "").lower() == "websocket":
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        print("[+] Połączono z pluginem Minecraft!", flush=True)
        
        # Ustawienie 48000 Hz - dokładnie tyle wysyła Simple Voice Chat!
        recognizer = KaldiRecognizer(model, 48000)
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.BINARY:
                    if recognizer.AcceptWaveform(msg.data):
                        result = json.loads(recognizer.Result())
                        recognized_text = result.get("text", "").strip()
                        
                        if recognized_text:
                            print(f"[Mowa]: {recognized_text}", flush=True)
                            try:
                                translated_text = translator.translate(recognized_text)
                            except Exception as err:
                                print(f"Błąd tłumaczenia: {err}", flush=True)
                                translated_text = recognized_text
                            
                            print(f"[Tłumaczenie]: {translated_text}", flush=True)
                            
                            await ws.send_json({
                                "original": recognized_text,
                                "translated": translated_text
                            })
        except Exception as e:
            print(f"Błąd połączenia: {e}", flush=True)
        finally:
            print("[-] Rozłączono z pluginem Minecraft.", flush=True)
            
        return ws

    return web.Response(text=HTML_PAGE, content_type="text/html")

async def init_app():
    app = web.Application()
    app.router.add_get("/", handle_request)
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"\n=== SERWER TRANSLATORA GOTOWY (Port: {port}) ===", flush=True)
    web.run_app(init_app(), host="0.0.0.0", port=port, print=None)
