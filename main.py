import requests
import time

def send_discord_message(webhook_url, content):
    headers = {"Content-Type": "application/json"}
    payload = {"content": content}
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        if response.status_code in [200, 204]:
            print("[DISCORD] Messaggio inviato con successo.")
            return True
        elif response.status_code == 429:
            data = response.json()
            # Legge il tempo di retry da Discord o imposta 5 secondi di default
            retry_after = data.get("retry_after", 5)
            
            # SE IL RATE LIMIT È SUPERIORE A 30 SECONDI, IGNORA LO SLEEP LUNGO
            if retry_after > 30:
                print(f"[DISCORD] Rate limit anomalo ({retry_after}s). Salto lo sleep e riproverò al prossimo ciclo.")
                return False
            
            print(f"[DISCORD] Rate limit! Attendo {retry_after} secondi...")
            time.sleep(retry_after)
            return False
        else:
            print(f"[DISCORD] Errore {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"[DISCORD] Errore di connessione: {e}")
        return False
