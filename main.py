import os
import time
import threading
import requests
import pandas as pd
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CONFIGURAZIONE ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1565871195251933274/KUx60m4tqYpf6PMluIYcBTpP7WA5PVExtCljLfUiT7zCEqb6DwE_w1uSUMA2Sz0IOyRL"
SYMBOL = "%5ENDX"  # URL Encoded per ^NDX (Nasdaq 100)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- SERVER WEB PER PORT BINDING SU RENDER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NAS100 Bot is running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def send_discord_notification(message):
    data = {"content": message}
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        print(f"[DISCORD] Risposta server: {res.status_code}", flush=True)
        if res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", 5))
            print(f"[DISCORD] Rate limit! Attendo {retry_after} secondi...", flush=True)
            time.sleep(retry_after)
            res_retry = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
            print(f"[DISCORD] Risposta dopo attesa: {res_retry.status_code}", flush=True)
    except Exception as e:
        print(f"[DISCORD] Errore invio: {e}", flush=True)

def fetch_nasdaq_data():
    # Usiamo 10d per scaricare circa 260-300 candele a 15m e garantire precisione alla EMA 200
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=10d&interval=15m"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"[DATA] Errore API Yahoo: Status {res.status_code}", flush=True)
            return None

        data = res.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]

        df = pd.DataFrame({
            'Open': quote['open'],
            'High': quote['high'],
            'Low': quote['low'],
            'Close': quote['close'],
            'Volume': quote['volume']
        }, index=pd.to_datetime(timestamps, unit='s'))

        return df.dropna()
    except Exception as e:
        print(f"[DATA] Eccezione download: {e}", flush=True)
        return None

def check_setup():
    print("[CHECK] Avvio analisi candela...", flush=True)
    df = fetch_nasdaq_data()
    
    # Verifichiamo che ci siano almeno 200 candele per la massima precisione calcolata
    if df is None or len(df) < 200:
        print(f"[CHECK] Dati insufficienti per EMA200 ({len(df) if df is not None else 0}/200 candele).", flush=True)
        return

    # Calcolo Indicatori
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # ATR (14)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()

    # Volume SMA (20)
    df['AvgVolume'] = df['Volume'].rolling(20).mean()

    # Penultima candela CHIUSA
    candle = df.iloc[-2]

    retest_ema = (candle['Low'] <= candle['EMA20']) and (candle['High'] >= candle['EMA20'])
    clean_market = (candle['High'] - candle['Low']) <= (candle['ATR'] * 1.8)
    low_volume = candle['Volume'] <= (candle['AvgVolume'] * 1.1)

    print(f"[CHECK] Analisi completata ({len(df)} candele). Retest: {retest_ema}, Clean: {clean_market}, LowVol: {low_volume}", flush=True)

    if retest_ema and clean_market and low_volume:
        prezzo_chiusura = round(float(candle['Close']), 2)
        ema20_val = round(float(candle['EMA20']), 2)

        msg = f"🚀 **SEGNALE RE-TEST NAS100 (15M)** 🚀\n" \
              f"• **Prezzo Chiusura:** {prezzo_chiusura}\n" \
              f"• **EMA 20:** {ema20_val}\n" \
              f"• **Stato:** Re-test confermato con volumi e volatilità controllati."

        send_discord_notification(msg)

def bot_loop():
    time.sleep(5)
    print("[BOT] Invio messaggio di test a Discord...", flush=True)
    send_discord_notification("✅ **TEST BOT NAS100:** Il bot è online e collegato a Discord!")

    while True:
        try:
            check_setup()
        except Exception as e:
            print(f"[LOOP] Errore: {e}", flush=True)
        time.sleep(900)

# Avvio server HTTP in background per Render
threading.Thread(target=run_http_server, daemon=True).start()

# Avvio ciclo di trading in un thread separato
threading.Thread(target=bot_loop, daemon=True).start()

# Mantiene attivo il processo principale
while True:
    time.sleep(3600)
