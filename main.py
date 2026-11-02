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
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non trovato nelle Environment Variables.", flush=True)
        return False

    payload = {"content": content}

    for attempt in range(1, max_retries + 1):
        print(f"[DISCORD] Tentativo {attempt}/{max_retries} invio...", flush=True)
        try:
            res = session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if res.status_code in [200, 204]:
                print("[DISCORD OK] Messaggio inviato con successo!", flush=True)
                return True
            elif res.status_code == 429:
                wait_time = 15 * attempt
                print(f"[DISCORD RATE LIMIT] Cooldown di {wait_time}s...", flush=True)
                time.sleep(wait_time)
            else:
                print(f"[DISCORD ERRORE] Status: {res.status_code}", flush=True)
                break
        except Exception as e:
            print(f"[DISCORD EXCEPTION] {e}", flush=True)
            break

    return False

# --- CALCOLO POC (POINT OF CONTROL SUI FUTURES) ---
def calculate_poc(df_window, bins=30):
    """Calcola il livello di prezzo con il maggior volume scambiato (POC)."""
    try:
        counts, bin_edges = np.histogram(df_window['Close'], bins=bins, weights=df_window['Volume'])
        poc_index = np.argmax(counts)
        poc_price = (bin_edges[poc_index] + bin_edges[poc_index + 1]) / 2.0
        return poc_price
    except Exception:
        return df_window['Close'].mean()

# --- LOGICA STRATEGIA: RE-TEST EMA 20 + POC + VOLUMI ---
def check_nas100_strategy():
    try:
        # Usiamo NQ=F (E-mini Nasdaq Futures) per avere i volumi reali!
        ticker = yf.Ticker("NQ=F")
        df = ticker.history(period="5d", interval="15m")

        if df.empty or len(df) < 50:
            print("[BOT ERRORE] Impossibile scaricare i dati dei Futures NQ=F.", flush=True)
            return None

        # 1. Calcolo EMA 20
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

        # 2. Calcolo Media Volumi (sulle ultime 20 candele)
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # 3. Calcolo POC (ultime 50 candele = circa 12 ore di contrattazione)
        poc_price = calculate_poc(df.tail(50))

        last_candle = df.iloc[-1]
        close_price = last_candle['Close']
        high_price = last_candle['High']
        low_price = last_candle['Low']
        ema_20 = last_candle['EMA_20']
        volume = last_candle['Volume']
        avg_volume = last_candle['Vol_SMA_20']

        # Filtro Volumi: True se la candela corrente ha volumi superiori alla media
        high_volume = volume > avg_volume

        # --- SEGNALE LONG (BULLISH RE-TEST) ---
        # Il prezzo scende a testare la EMA 20 (low <= EMA_20), chiude sopra la EMA 20 e si trova sopra/vicino al POC
        if low_price <= ema_20 and close_price > ema_20 and close_price >= poc_price:
            vol_str = "🟢 **Volumi ALTI** (Sopra la media)" if high_volume else "🟡 Volumi nella media"
            return (
                f"🚀 **CONSIGLIO TRADING: ENTRATA LONG (NAS100 15M)**\n\n"
                f"• **Prezzo Attuale:** `{close_price:.2f}`\n"
                f"• **Re-Test EMA 20:** `{ema_20:.2f}` (Supporto tenuto)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto al ripasso sulla EMA 20 con struttura supportata dai volumi del POC."
            )

        # --- SEGNALE SHORT (BEARISH RE-TEST) ---
        # Il prezzo sale a testare la EMA 20 (high >= EMA_20), chiude sotto la EMA 20 e si trova sotto/vicino al POC
        if high_price >= ema_20 and close_price < ema_20 and close_price <= poc_price:
            vol_str = "🔴 **Volumi ALTI** (Sopra la media)" if high_volume else "🟡 Volumi nella media"
            return (
                f"🔻 **CONSIGLIO TRADING: ENTRATA SHORT (NAS100 15M)**\n\n"
                f"• **Prezzo Attuale:** `{close_price:.2f}`\n"
                f"• **Re-Test EMA 20:** `{ema_20:.2f}` (Resistenza confermata)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto al rialzo sulla EMA 20 con pressione di vendita sotto il POC."
            )

        return None
    except Exception as e:
        print(f"[ANALISI ERRORE] {e}", flush=True)
        return None

# --- CICLO PRINCIPALE ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio monitoraggio automatico Futures NAS100 (NQ=F)...", flush=True)
    
    send_discord_message("🤖 **NAS100 Bot online! Analisi automatica EMA 20 + POC + Volumi (Futures) attiva.**")

    last_signal_sent = ""

    while True:
        try:
            print("[CHECK] Analisi candela 15M in corso...", flush=True)
            alert_msg = check_nas100_strategy()
            
            if alert_msg and alert_msg != last_signal_sent:
                print("[BOT] Segnale confermato! Invio su Discord via Make...", flush=True)
                send_discord_message(alert_msg)
                last_signal_sent = alert_msg
            else:
                print("[CHECK] Nessuna conferma di re-test sulla candela attuale.", flush=True)

            # Controlla ad ogni chiusura di candela 15M (900 secondi = 15 minuti)
            time.sleep(900)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(15)

if __name__ == "__main__":
    t_server = threading.Thread(target=start_http_server, daemon=True)
    t_server.start()
    bot_loop()
