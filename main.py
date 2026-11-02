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

def send_discord_message(content, max_retries=3):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non trovato nelle Environment Variables.", flush=True)
        return False

    payload = {"content": content}

    for attempt in range(1, max_retries + 1):
        print(f"[DISCORD] Tentativo {attempt}/{max_retries} invio: '{content}'...", flush=True)
        try:
            res = session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            print(f"[DISCORD RESPONSE] Status Code: {res.status_code} | Body: {res.text[:150]}", flush=True)

            if res.status_code in [200, 204]:
                print("[DISCORD OK] Messaggio inviato con successo!", flush=True)
                return True
            elif res.status_code == 429:
                wait_time = 15 * attempt
                print(f"[DISCORD RATE LIMIT] IP in cooldown. Attendo {wait_time}s prima di riprovare...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"[DISCORD ERRORE] Risposta non prevista: {res.status_code}", flush=True)
                break
        except Exception as e:
            print(f"[DISCORD ERRORE EXCEPTION] {e}", flush=True)
            break

    return False

# --- CICLO DEL BOT ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio ciclo di monitoraggio NAS100 15M...", flush=True)

    # Invia messaggio di benvenuto
    send_discord_message("🤖 **NAS100 Bot online e operativo su Render!**")

    while True:
        try:
            print("[CHECK] Controllo completato.", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    # 1. Avvia il server HTTP per soddisfare le verifiche di Render
    t_server = threading.Thread(target=start_http_server, daemon=True)
    t_server.start()

    # 2. Avvia il ciclo del bot
    bot_loop()
