import os
import time
import threading
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- CONFIGURAZIONE ---
DISCORD_WEBHOOK_URL ="https://discord.com/api/webhooks/1565779847014387825/p9gdYL8v3UxNuy926BMGFY8dedrL9Dt5P6Kz7ID9GGwdCWf8jTqiNuKhfrsr3GNMnl8S"
SYMBOL = "^NDX"  # Ticker Nasdaq 100 su Yahoo Finance
TIMEFRAME = "15m"

# --- MINI SERVER PER MANTENERE ATTIVO RENDER (PORT BINDING) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NAS100 Bot is running!")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def send_discord_notification(message):
    data = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Notifica inviata su Discord!")
    except Exception as e:
        print(f"Errore invio Discord: {e}")

def check_setup():
    df = yf.download(tickers=SYMBOL, period="5d", interval=TIMEFRAME, progress=False)
    
    if df.empty or len(df) < 200:
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

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

    # Penultima candela (l'ultima appena CHIUSA)
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

# Avvio del server HTTP in background per Render
threading.Thread(target=run_http_server, daemon=True).start()

# Loop continuo ogni 15 minuti
print("Bot avviato e in ascolto...")
send_discord_notification("✅ **TEST BOT NAS100:** Il bot è online e collegato a Discord!")
while True:
    try:
        check_setup()
    except Exception as e:
        print(f"Errore: {e}")
    
    time.sleep(900)
