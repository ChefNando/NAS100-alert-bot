import os
import time
import threading
import requests
import pandas as pd
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CONFIGURAZIONE ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1565779847014387825/p9gdYL8v3UxNuy926BMGFY8dedrL9Dt5P6Kz7ID9GGwdCWf8jTqiNuKhfrsr3GNmnL8S"
SYMBOL = "%5ENDX"  # URL Encoded per ^NDX

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
        print(f"[DISCORD] Status: {res.status_code}")
    except Exception as e:
        print(f"[DISCORD] Errore invio: {e}")

def fetch_nasdaq_data():
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?range=5d&interval=15m"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"[DATA] Errore API Yahoo: Status {res.status_code}")
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
        print(f"[DATA] Eccezione download: {e}")
        return None

def check_setup():
    df = fetch_nasdaq_data()
    if df is None or len(df) < 200:
        print("[CHECK] Dati storici insufficienti.")
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

    if retest_ema and clean_market and low_volume:
        prezzo_chiusura = round(float(candle['Close']), 2)
        ema20_val = round(float(candle['EMA20']), 2)

        msg = f"🚀 **SEGNALE RE-TEST NAS100 (15M)** 🚀\n" \
              f"• **Prezzo Chiusura:** {prezzo_chiusura}\n" \
              f"• **EMA 20:** {ema20_val}\n" \
              f"• **Stato:** Re-test confermato con volumi e volatilità controllati."

        send_discord_notification(msg)

def bot_loop():
    print("[BOT] Avvio sequenza e test notifica...")
    send_discord_notification("✅ **TEST BOT NAS100:** Il bot è online e collegato a Discord!")

    while True:
        try:
            check_setup()
        except Exception as e:
            print(f"[LOOP] Errore: {e}")
        time.sleep(900)

# Avvio server HTTP in background per Render
threading.Thread(target=run_http_server, daemon=True).start()

# Avvio ciclo di trading in un thread separato
threading.Thread(target=bot_loop, daemon=True).start()

# Mantiene attivo il processo principale
while True:
    time.sleep(3600)
