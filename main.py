import os
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Configuration from Environment Variables or hardcoded
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "AAPKA_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "AAPKA_CHAT_ID")

class TVSignal(BaseModel):
    signal: str
    ticker: str
    price: float
    sl: float
    adx: float = 25.0

def get_live_nse_pcr():
    """NSE Live Option Chain se PCR calculate karta hai"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    try:
        session = requests.Session()
        # Initial handshake for cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tot_ce_oi = data.get("filtered", {}).get("CE", {}).get("totOI", 0)
            tot_pe_oi = data.get("filtered", {}).get("PE", {}).get("totOI", 0)
            
            if tot_ce_oi > 0:
                pcr = round(tot_pe_oi / tot_ce_oi, 2)
                return pcr
    except Exception as e:
        print(f"NSE OI Fetch Error: {e}")
    
    # Fallback agar NSE site down/slow ho (Trade miss na ho)
    return 1.0 

def send_telegram_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Dispatch Error: {e}")

@app.get("/")
def home():
    return {"status": "Algo Server Running with Live NSE OI Filter"}

@app.post("/tv_webhook")
async def receive_webhook(signal_data: TVSignal):
    price = signal_data.price
    signal_type = signal_data.signal.upper()
    sl = signal_data.sl
    
    # 1. Round to nearest 50 for Nifty ATM Strike
    atm_strike = int(round(price / 50.0) * 50)
    
    # 2. Check Live NSE OI / PCR Filter
    live_pcr = get_live_nse_pcr()
    
    # 3. Validation Logic
    if signal_type == "BUY_CE":
        # PCR < 0.85 means Call writers dominate (High Trap Risk)
        if live_pcr < 0.85:
            print(f"BUY_CE Rejected! Fake Breakout Detected. PCR: {live_pcr}")
            return {"status": "REJECTED_TRAP", "reason": f"Low PCR ({live_pcr}) - Call writers dominating"}
        
        rec_strike = f"{atm_strike} CE"
        msg = (
            f"🚀 <b>CONFIRMED BUY CALL (CE)</b>\n\n"
            f"📈 <b>Index:</b> {signal_data.ticker} @ {price:.2f}\n"
            f"🎯 <b>Recommended ATM:</b> <b>{rec_strike}</b>\n"
            f"🛑 <b>Spot SL:</b> {sl:.2f}\n"
            f"📊 <b>Live Market PCR:</b> <b>{live_pcr}</b> (Bullish Writing)\n"
            f"⚡ <i>Action: Open Groww/Lemonn and Punch {rec_strike}!</i>"
        )
        send_telegram_alert(msg)
        return {"status": "SENT", "strike": rec_strike, "pcr": live_pcr}

    elif signal_type == "BUY_PE":
        # PCR > 1.25 means Put writers dominate (High Bounce Risk)
        if live_pcr > 1.25:
            print(f"BUY_PE Rejected! Fake Breakdown Detected. PCR: {live_pcr}")
            return {"status": "REJECTED_TRAP", "reason": f"High PCR ({live_pcr}) - Put writers supporting"}
        
        rec_strike = f"{atm_strike} PE"
        msg = (
            f"🔻 <b>CONFIRMED BUY PUT (PE)</b>\n\n"
            f"📉 <b>Index:</b> {signal_data.ticker} @ {price:.2f}\n"
            f"🎯 <b>Recommended ATM:</b> <b>{rec_strike}</b>\n"
            f"🛑 <b>Spot SL:</b> {sl:.2f}\n"
            f"📊 <b>Live Market PCR:</b> <b>{live_pcr}</b> (Bearish Writing)\n"
            f"⚡ <i>Action: Open Groww/Lemonn and Punch {rec_strike}!</i>"
        )
        send_telegram_alert(msg)
        return {"status": "SENT", "strike": rec_strike, "pcr": live_pcr}

    return {"status": "UNKNOWN_SIGNAL"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
    
