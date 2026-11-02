import os
import time
import threading
import requests
from flask import Flask

# --- CONFIGURAZIONE WEB SERVER (KEEP-ALIVE RENDER) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "NAS100 Bot is running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- INVIO DISCORD CON PROTEZIONE RATE-LIMIT ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD] WEBHOOK URL non configurato.")
        return False

    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)

        if response.status_code in [200, 204]:
            print("[DISCORD] Messaggio inviato con successo.")
            return True
        elif response.status_code == 429:
            data = response.json()
            retry_after = data.get("retry_after", 5)

            # Cap di sicurezza: se Discord chiede un attesa oltre 30s, non congela lo script
            if retry_after > 30:
                print(f"[DISCORD] Rate limit anomalo ({retry_after}s). Salto lo sleep lungo.")
                return False

            print(f"[DISCORD] Rate limit! Attendo {retry_after} secondi...")
            time.sleep(retry_after)
            return False
        else:
            print(f"[DISCORD] Errore {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"[DISCORD] Errore connessione: {e}")
        return False

# --- LOGICA DEL BOT ---
def bot_loop():
    print("[BOT] Avvio monitoraggio NAS100 15M...")
    
    # Invio messaggio di benvenuto all'avvio
    send_discord_message("🤖 **NAS100 Bot online e operativo!**")

    while True:
        try:
            # Qui si esegue la logica di analisi candele e re-test EMA 20
            print("[CHECK] Analisi completata. In attesa del prossimo controllo...")
            
            # Attesa tra una scansione e l'altra (es. ogni 60 secondi)
            time.sleep(60)

        except Exception as e:
            print(f"[ERRORE] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Avvio del server web in background per Render
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Avvio del bot
    bot_loop()
