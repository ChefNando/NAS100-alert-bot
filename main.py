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
    print(f"[DISCORD] Invio in corso...")
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] WEBHOOK URL mancante.")
        return False

    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        # Timeout di 5 secondi per non bloccare lo script se la rete rallenta
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        
        if response.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo!")
            return True
        elif response.status_code == 429:
            data = response.json()
            retry_after = min(data.get("retry_after", 5), 10)
            print(f"[DISCORD RATE LIMIT] Attendo {retry_after}s...")
            time.sleep(retry_after)
            return False
        else:
            print(f"[DISCORD ERRORE] Status: {response.status_code} - Resp: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("[DISCORD ERRORE] Timeout connessione (5s superati).")
        return False
    except Exception as e:
        print(f"[DISCORD ERRORE ERRORE SCONOSCIUTO] {e}")
        return False

def bot_loop():
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...")
    
    # Invia il messaggio iniziale
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            # Sostituire con la logica di analisi candele 15m
            print("[CHECK] Controllo candele completato.")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Avvia Flask prima su un thread separato
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()
    
    # Avvia il bot
    bot_loop()
