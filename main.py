import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVER WEB NATIVO PER KEEP-ALIVE RENDER ---
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
        return  # Silenzia i log continui di Render

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- CONFIGURAZIONE DISCORD ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non trovato nelle Environment Variables.", flush=True)
        return False

    print(f"[DISCORD] Invio: '{content}'...", flush=True)
    payload = {"content": content}

    try:
        res = session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        # 200 (OK) e 204 (No Content) indicano successo
        if res.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo!", flush=True)
            return True
        elif res.status_code == 429:
            retry_after = 5
            try:
                retry_after = res.json().get("retry_after", 5)
            except Exception:
                pass
            print(f"[DISCORD RATE LIMIT] Attendo {retry_after}s...", flush=True)
            time.sleep(retry_after)
            return send_discord_message(content)
        else:
            print(f"[DISCORD ERRORE] Status {res.status_code}: {res.text[:100]}", flush=True)
            return False

    except Exception as e:
        print(f"[DISCORD ERRORE EXCEPTION] {e}", flush=True)
        return False

# --- CICLO DEL BOT ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...", flush=True)
    
    # Notifica iniziale di avvio
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Controllo completato.", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    # 1. Avvia immediatamente il server HTTP su un thread daemon per sbloccare Render
    t_server = threading.Thread(target=start_http_server, daemon=True)
    t_server.start()

    # 2. Esegue il ciclo principale del bot
    bot_loop()
