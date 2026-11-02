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

# --- CALCOLO POC (POINT OF CONTROL) ---
def calculate_poc(df_window, bins=30):
    try:
        counts, bin_edges = np.histogram(df_window['Close'], bins=bins, weights=df_window['Volume'])
        poc_index = np.argmax(counts)
        poc_price = (bin_edges[poc_index] + bin_edges[poc_index + 1]) / 2.0
        return poc_price
    except Exception:
        return df_window['Close'].mean()

# --- LOGICA STRATEGIA: NASDAQ SPOT (ETORO) ---
def check_nas100_strategy():
    try:
        # USA ^NDX PER AVERE I PREZZI IDENTICI AD ETORO (NSDQ100)
        ticker = yf.Ticker("^NDX")
        df = ticker.history(period="5d", interval="15m")

        if df.empty or len(df) < 50:
            print("[BOT ERRORE] Impossibile scaricare i dati ^NDX.", flush=True)
            return None

        # 1. Calcolo EMA 20 sull'indice Spot
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

        # 2. Calcolo Media Volumi
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # 3. Calcolo POC
        poc_price = calculate_poc(df.tail(50))

        last_candle = df.iloc[-1]
        close_price = last_candle['Close']
        high_price = last_candle['High']
        low_price = last_candle['Low']
        ema_20 = last_candle['EMA_20']
        volume = last_candle['Volume']
        avg_volume = last_candle['Vol_SMA_20']

        high_volume = volume > avg_volume

        # --- SEGNALE LONG ---
        if low_price <= ema_20 and close_price > ema_20 and close_price >= poc_price:
            vol_str = "🟢 **Volumi ALTI**" if high_volume else "🟡 Volumi nella media"
            return (
                f"🚀 **CONSIGLIO TRADING: ENTRATA LONG (NAS100 15M)**\n\n"
                f"• **Prezzo eToro:** `{close_price:.2f}`\n"
                f"• **EMA 20:** `{ema_20:.2f}` (Supporto tenuto)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto sulla EMA 20 tenuto sopra il POC."
            )

        # --- SEGNALE SHORT ---
        if high_price >= ema_20 and close_price < ema_20 and close_price <= poc_price:
            vol_str = "🔴 **Volumi ALTI**" if high_volume else "🟡 Volumi nella media"
            return (
                f"🔻 **CONSIGLIO TRADING: ENTRATA SHORT (NAS100 15M)**\n\n"
                f"• **Prezzo eToro:** `{close_price:.2f}`\n"
                f"• **EMA 20:** `{ema_20:.2f}` (Resistenza confermata)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto sulla EMA 20 respinto sotto il POC."
            )

        return None
    except Exception as e:
        print(f"[ANALISI ERRORE] {e}", flush=True)
        return None

# --- CICLO PRINCIPALE AD ALTA FREQUENZA (60 SECONDI) ---
def bot_loop():
    time.sleep(2)
    print("[BOT] Avvio monitoraggio in tempo reale Nasdaq (eToro)...", flush=True)
    
    send_discord_message("🤖 **NAS100 Bot online! Allineato ai prezzi eToro con scansione veloce (60s).**")

    last_signal_sent = ""

    while True:
        try:
            print("[CHECK] Scansione candela 15M in corso...", flush=True)
            alert_msg = check_nas100_strategy()
            
            if alert_msg and alert_msg != last_signal_sent:
                print("[BOT] Segnale tempestivo trovato! Inoltro a Discord...", flush=True)
                send_discord_message(alert_msg)
                last_signal_sent = alert_msg

            # Controlla ogni minuto invece di attendere 15 minuti!
            time.sleep(60)
        except Exception as e:
            print(f"[ERRORE LOOP] {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    t_server = threading.Thread(target=start_http_server, daemon=True)
    t_server.start()
    bot_loop()
