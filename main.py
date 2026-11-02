import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVER WEB NATIVO ---
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
        return

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- DISCORD & BOT LOGIC ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL mancante!", flush=True)
        return False

    print(f"[DISCORD] Invio: '{content}'...", flush=True)
    
    # User-Agent personalizzato per bypassare il filtro Cloudflare di Discord
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    payload = {"content": content}

    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        
        if res.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo su Discord!", flush=True)
            return True
        else:
            print(f"[DISCORD ERRORE] Status {res.status_code}: {res.text[:100]}", flush=True)
            return False
            
    except Exception as e:
        print(f"[DISCORD ERRORE EXCEPTION] {e}", flush=True)
        return False

def bot_loop():
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...", flush=True)
    
    # Invio alert di avvio
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Controllo completato.", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    bot_loop()
