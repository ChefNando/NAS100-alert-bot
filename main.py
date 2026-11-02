import os
import time
import threading
from flask import Flask

# 1. SERVER WEB PER KEEP-ALIVE DI RENDER
app = Flask(__name__)

@app.route('/')
def home():
    return "NAS100 Bot is running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. CICLO DI ANALISI DEL BOT (H24)
def bot_loop():
    print("[BOT] Avvio ciclo di monitoraggio NAS100...")
    while True:
        try:
            # --- Inserisci qui la tua logica di analisi candele 15m ---
            print("[CHECK] Esecuzione analisi candele...")
            
            # Attende 60 secondi prima del prossimo controllo
            time.sleep(60)
            
        except Exception as e:
            print(f"[ERRORE BOT] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # Avvia il server web in un thread separato
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Avvia il ciclo infinito del bot
    bot_loop()
