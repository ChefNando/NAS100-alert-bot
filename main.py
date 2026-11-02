import os
import time
import threading
import requests
import yfinance as yf
import pandas as pd
import numpy as np
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
        return

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- CONFIGURAZIONE DISCORD / MAKE ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
})

def send_discord_message(content, max_retries=3):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non trovato.", flush=True)
        return False

    payload = {"content": content}

    for attempt in range(1, max_retries + 1):
        try:
            res = session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if res.status_code in [200, 204]:
                print("[DISCORD OK] Messaggio inviato!", flush=True)
                return True
            elif res.status_code == 429:
                time.sleep(15 * attempt)
            else:
                break
        except Exception as e:
            print(f"[DISCORD EXCEPTION] {e}", flush=True)
            break

    return False

# --- CALCOLO POC (POINT OF CONTROL) ---
def calculate_poc(df_window, bins=30):
    try:
        counts, bin_edges = np.histogram(df_window['Close'], bins=bins, weights=df_window['Volume'])
        poc_index = np.argmax(counts)
        poc_price = (bin_edges[poc_index] + bin_edges[poc_index + 1]) / 2.0
        return poc_price
    except Exception:
        return df_window['Close'].mean()

# --- STRATEGIA: ESCLUSIVAMENTE RE-TEST CHIUSURA CANDELA 15M ---
def check_nas100_retest():
    try:
        ticker = yf.Ticker("NQ=F")
        df = ticker.history(period="5d", interval="15m")

        if df.empty or len(df) < 50:
            return None

        # 1. Calcolo MA 20 Semplice
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # 2. Calcolo POC ultime 50 candele
        poc_price = calculate_poc(df.tail(50))

        curr = df.iloc[-1]   # Candela appena chiusa
        prev = df.iloc[-2]   # Candela precedente

        c_close = curr['Close']
        c_high = curr['High']
        c_low = curr['Low']
        c_ma20 = curr['MA_20']
        
        p_close = prev['Close']
        p_ma20 = prev['MA_20']

        high_volume = curr['Volume'] > curr['Vol_SMA_20']
        vol_str = "🟢 **Volumi ALTI**" if high_volume else "🟡 Volumi nella media"

        # --- VERO RE-TEST LONG (SU CANDELA CHIUSA) ---
        if p_close > p_ma20 and c_low <= c_ma20 and c_close > c_ma20 and c_close >= poc_price:
            return (
                f"🚀 **CONSIGLIO TRADING: RE-TEST LONG CONFERMATO (CHIUSURA 15M)**\n\n"
                f"• **Prezzo Chiusura:** `{c_close:.2f}`\n"
                f"• **Livello MA 20:** `{c_ma20:.2f}` (Supporto tenuto)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Candela chiusa con rigetto sulla MA 20 tenuto sopra il POC."
            )

        # --- VERO RE-TEST SHORT (SU CANDELA CHIUSA) ---
        if p_close < p_ma20 and c_high >= c_ma20 and c_close < c_ma20 and c_close <= poc_price:
            return (
                f"🔻 **CONSIGLIO TRADING: RE-TEST SHORT CONFERMATO (CHIUSURA 15M)**\n\n"
                f"• **Prezzo Chiusura:** `{c_close:.2f}`\n"
                f"• **Livello MA 20:** `{c_ma20:.2f}` (Resistenza confermata)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Candela chiusa con rigetto sulla MA 20 respinto sotto il POC."
            )

        return None
    except Exception as e:
        print(f"[ANALISI ERRORE] {e}", flush=True)
        return None

# --- CICLO DI CONTROLLO OGNI 15 MINUTI ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio monitoraggio RE-TEST ad ogni chiusura di candela (15M)...", flush=True)
    send_discord_message("🤖 **NAS100 Bot online! Scansione impostata ad ogni chiusura candela 15M.**")

    last_signal_sent = ""

    while True:
        try:
            alert_msg = check_nas100_retest()
            
            if alert_msg and alert_msg != last_signal_sent:
                print("[BOT] Re-Test confermato a fine candela! Invio notifica...", flush=True)
                send_discord_message(alert_msg)
                last_signal_sent = alert_msg

            # Pausa di 15 minuti (900 secondi) per sincronizzarsi con le candele
            time.sleep(900)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(15)

if __name__ == "__main__":
    t_server = threading.Thread(target=start_http_server, daemon=True)
    t_server.start()
    bot_loop()
