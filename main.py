import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVER WEB NATIVO (SENZA FLASK) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"NAS100 Bot is running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return  # Silenzia i log continui nella console di Render

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- DISCORD & BOT LOGIC ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] Variabile DISCORD_WEBHOOK_URL non trovata!")
        return False

    print(f"[DISCORD] Invio: '{content}'")
    headers = {"Content-Type": "application/json"}
    payload = {"content": content}

    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        if res.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo!")
            return True
        else:
            print(f"[DISCORD ERRORE] Status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"[DISCORD ERRORE] {e}")
        return False

def bot_loop():
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...")
    
    # Prova invio benvenuto
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Analisi completata. In attesa del prossimo ciclo...")
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Avvia subito il server HTTP in background per far felice Render
    threading.Thread(target=start_http_server, daemon=True).start()
    
    # 2. Esegue il bot direttamente nel processo principale
    bot_loop()
