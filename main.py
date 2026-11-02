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
    # use_reloader=False evita che Flask crei thread duplicati su Render
    app.run(host="0.0.0.0", port=port, use_reloader=False)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non impostato nelle Environment Variables.")
        return False

    print(f"[DISCORD] Invio messaggio in corso...")
    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        if response.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo!")
            return True
        else:
            print(f"[DISCORD ERRORE] Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[DISCORD ERRORE] {e}")
        return False

def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...")
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Analisi completata. In attesa del prossimo controllo...")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Avvia Flask in un thread dedicato
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()

    # 2. Avvia il ciclo del bot in un altro thread dedicato
    t_bot = threading.Thread(target=bot_loop, daemon=True)
    t_bot.start()

    # 3. Mantiene il programma principale in esecuzione
    while True:
        time.sleep(3600)
