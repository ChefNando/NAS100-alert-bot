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

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

def send_discord_message(content):
    print(f"[DEBUG] Tentativo invio a Discord... URL presente: {bool(DISCORD_WEBHOOK_URL)}")
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD] WEBHOOK URL non trovato nelle variabili d'ambiente!")
        return False

    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code in [200, 204]:
            print("[DISCORD] Messaggio inviato con successo!")
            return True
        else:
            print(f"[DISCORD] Errore risposta server: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[DISCORD] Errore connessione: {e}")
        return False

def bot_loop():
    print("[BOT] Avvio ciclo di monitoraggio...")
    
    # FORZA L'INVIO DEL MESSAGGIO DI BENVENUTO
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Controllo candele in corso...")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE] {e}")
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot_loop()
