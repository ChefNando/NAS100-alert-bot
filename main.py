def check_nas100_strategy():
    try:
        # Ticker QQQ per dati di prezzo precisi e in tempo reale
        ticker = yf.Ticker("QQQ")
        df = ticker.history(period="5d", interval="15m")

        if df.empty or len(df) < 50:
            print("[BOT ERRORE] Impossibile scaricare i dati QQQ.", flush=True)
            return None

        # Facciamo il rescale del prezzo sull'indice effettivo
        # (QQQ quota circa 1/40 dell'indice Nasdaq, oppure usiamo i prezzi diretti calibrati)
        
        # 1. Calcolo MA 20 Semplice (stessa di eToro MA 20)
        df['MA_20'] = df['Close'].rolling(window=20).mean()

        # 2. Calcolo Media Volumi
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()

        # 3. Calcolo POC
        poc_price = calculate_poc(df.tail(50))

        last_candle = df.iloc[-1]
        close_price = last_candle['Close']
        high_price = last_candle['High']
        low_price = last_candle['Low']
        ma_20 = last_candle['MA_20']
        volume = last_candle['Volume']
        avg_volume = last_candle['Vol_SMA_20']

        high_volume = volume > avg_volume

        # --- SEGNALE LONG ---
        if low_price <= ma_20 and close_price > ma_20 and close_price >= poc_price:
            vol_str = "🟢 **Volumi ALTI**" if high_volume else "🟡 Volumi nella media"
            return (
                f"🚀 **CONSIGLIO TRADING: ENTRATA LONG (NAS100 15M)**\n\n"
                f"• **Prezzo Riferimento:** `{close_price:.2f}`\n"
                f"• **MA 20 (eToro):** `{ma_20:.2f}` (Supporto tenuto)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto al ribasso sulla MA 20 tenuto sopra il POC."
            )

        # --- SEGNALE SHORT ---
        if high_price >= ma_20 and close_price < ma_20 and close_price <= poc_price:
            vol_str = "🔴 **Volumi ALTI**" if high_volume else "🟡 Volumi nella media"
            return (
                f"🔻 **CONSIGLIO TRADING: ENTRATA SHORT (NAS100 15M)**\n\n"
                f"• **Prezzo Riferimento:** `{close_price:.2f}`\n"
                f"• **MA 20 (eToro):** `{ma_20:.2f}` (Resistenza confermata)\n"
                f"• **Livello POC:** `{poc_price:.2f}`\n"
                f"• **Volumi:** {vol_str}\n\n"
                f"💡 *Conferma:* Rigetto al rialzo sulla MA 20 respinto sotto il POC."
            )

        return None
    except Exception as e:
        print(f"[ANALISI ERRORE] {e}", flush=True)
        return None
