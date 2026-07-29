import os
import asyncio
import json
import websockets
from vosk import Model, KaldiRecognizer
from deep_translator import GoogleTranslator

# 1. Automatyczne pobieranie/ładowanie polskiego modelu Vosk
print("Ładowanie/pobieranie modelu językowego Vosk (Polski)...", flush=True)
model = Model(lang="pl") 
print("Model załadowany pomyślnie!", flush=True)

# 2. Inicjalizacja tłumacza (automatyczne wykrywanie -> angielski)
translator = GoogleTranslator(source='auto', target='en')

async def process_audio(websocket):
    print("[+] Połączono z pluginem Minecraft.", flush=True)
    
    # Vosk wymaga formatu audio 16kHz (standard w Simple Voice Chat / Plasmo Voice)
    recognizer = KaldiRecognizer(model, 16000)
    
    try:
        # Pętla odbierająca pakiety audio z gry
        async for message in websocket:
            # Przetwarzanie strumienia bajtów audio
            if recognizer.AcceptWaveform(message):
                result = json.loads(recognizer.Result())
                recognized_text = result.get("text", "").strip()
                
                # Jeśli Vosk wyłapał słowa
                if recognized_text:
                    print(f"[Mowa]: {recognized_text}", flush=True)
                    
                    # Przetłumaczenie tekstu
                    try:
                        translated_text = translator.translate(recognized_text)
                    except Exception as err:
                        print(f"Błąd tłumaczenia: {err}", flush=True)
                        translated_text = recognized_text
                    
                    print(f"[Tłumaczenie]: {translated_text}", flush=True)
                    
                    # Przygotowanie odpowiedzi JSON dla gry
                    response_payload = json.dumps({
                        "original": recognized_text,
                        "translated": translated_text
                    })
                    
                    # Odesłanie wyniku do Minecrafta
                    await websocket.send(response_payload)
                    
    except websockets.exceptions.ConnectionClosed:
        print("[-] Rozłączono z pluginem Minecraft.", flush=True)

async def main():
    # Pobieramy port przydzielony przez hosting (Render) lub domyślnie 8765
    port = int(os.environ.get("PORT", 8765))
    
    async with websockets.serve(process_audio, "0.0.0.0", port):
        print("\n=== SERWER TRANSLATORA GOTOWY ===", flush=True)
        print(f"Nasłuchiwanie na adresie: ws://0.0.0.0:{port}", flush=True)
        await asyncio.Future()  # Utrzymanie serwera w działaniu

if __name__ == "__main__":
    asyncio.run(main())
