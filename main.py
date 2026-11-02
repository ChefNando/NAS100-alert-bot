import os
import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "NAS100 Bot is running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] Variable DISCORD_WEBHOOK_URL mancante o vuota.")
        return False

    print(f"[DISCORD] Invio messaggio: '{content}'...")
    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        
        if response.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo a Discord!")
            return True
        else:
            print(f"[DISCORD ERRORE] Status HTTP: {response.status_code} | Risposta: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("[DISCORD ERRORE] Timeout di 5 secondi superato nell'invio a Discord.")
        return False
    except Exception as e:
        print(f"[DISCORD ERRORE SCONOSCIUTO] {e}")
        return False

def bot_loop():
    # Attende 3 secondi per permettere a Flask di avviarsi completamente
    time.sleep(3)
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...")
    
    # Invio messaggio di test
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Analisi completata. In attesa del prossimo controllo...")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Avvia il server Flask in background
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()
    
    # 2. Avvia il ciclo del Bot in un ALTRO thread in background per non bloccare il programma
    t_bot = threading.Thread(target=bot_loop, daemon=True)
    t_bot.start()

    # Mantiene il processo principale attivo
    while True:
        time.sleep(3600)
