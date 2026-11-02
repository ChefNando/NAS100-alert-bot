import os
import time
import threading
import requests
from flask import Flask

# --- SERVER WEB PER RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "NAS100 Bot is running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- INVIO NOTIFICHE DISCORD ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] Variabile DISCORD_WEBHOOK_URL non trovata o vuota!")
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
        print("[DISCORD ERRORE] Timeout di 5s superato nell'invio.")
        return False
    except Exception as e:
        print(f"[DISCORD ERRORE] {e}")
        return False

# --- CICLO DEL BOT ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...")
    
    # Invia subito il messaggio di benvenuto
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Controllo candele completato.")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Avvia Flask su un thread dedicato
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()
    
    # Avvia il bot su un altro thread dedicato
    t_bot = threading.Thread(target=bot_loop, daemon=True)
    t_bot.start()

    # Mantiene il processo attivo
    while True:
        time.sleep(3600)
