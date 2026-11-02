def send_discord_message(content):
    if not DISCORD_WEBHOOK_URL:
        print("[DISCORD ERRORE] DISCORD_WEBHOOK_URL non impostato.", flush=True)
        return False

    print(f"[DISCORD] Invio: '{content}'...", flush=True)
    payload = {"content": content}

    try:
        res = session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        
        # 200 e 204 sono i codici di successo di Discord
        if res.status_code in [200, 204]:
            print("[DISCORD OK] Messaggio inviato con successo su Discord!", flush=True)
            return True
        elif res.status_code == 429:
            # Se va in rate limit, usa il valore di retry se presente
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
