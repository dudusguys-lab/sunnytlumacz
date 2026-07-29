import os
import asyncio
import json
import websockets
from vosk import Model, KaldiRecognizer
from deep_translator import GoogleTranslator

# 1. Ładowanie modelu Vosk
print("Ładowanie modelu językowego Vosk (Polski)...", flush=True)
model = Model(lang="pl")
print("Model załadowany pomyślnie!", flush=True)

translator = GoogleTranslator(source='auto', target='en')

async def process_audio(websocket):
    print("[+] Połączono z pluginem Minecraft!", flush=True)
    recognizer = KaldiRecognizer(model, 48000)
    
    try:
        async for message in websocket:
            # Jeśli dostajemy bajty audio z MC
            if isinstance(message, bytes):
                if recognizer.AcceptWaveform(message):
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
                        
                        await websocket.send(json.dumps({
                            "original": recognized_text,
                            "translated": translated_text
                        }))
            else:
                print(f"[Tekst]: {message}", flush=True)

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Błąd transmisji: {e}", flush=True)
    finally:
        print("[-] Rozłączono z pluginem Minecraft.", flush=True)

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"\n=== SERWER TRANSLATORA GOTOWY (Port: {port}) ===", flush=True)
    
    # max_size=None pozwala na przyjmowanie dużych pakietów audio
    async with websockets.serve(process_audio, "0.0.0.0", port, max_size=None):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
