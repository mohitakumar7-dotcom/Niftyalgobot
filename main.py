import os
import requests
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()

# --- YAHAN APNA TOKEN8821572601:AAGsflinihBXysjy42-QNpIzE023xVlEf8I AUR CHAT ID DALEIN ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRA8821572601:AAGsflinihBXysjy42-QNpIzE023xVlEf8IM_BOT_TOKEN", "AAPKA_TELEGRAM_BOT_TOKEN_YAHAN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRA6444488708M_CHAT_ID", "AAPKI_NUMERIC_CHAT_ID_YAHAN")

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=6)
    except Exception as e:
        print(f"Telegram error: {e}")

@app.get("/")
def home():
    return {"status": "Algo Server Running on Cloud"}

@app.post("/tv_webhook")
async def receive_tv_alert(request: Request):
    try:
        data = await request.json()
        signal = data.get("signal", "UNKNOWN")
        spot_price = float(data.get("price", 0.0))
        sl_level = float(data.get("sl", 0.0))
        adx_val = float(data.get("adx", 0.0))

        # ATM Strike Calculation (Round off to nearest 50)
        atm_strike = round(spot_price / 50) * 50

        if signal == "BUY_CE":
            msg = (
                f"🚀 *HIGH-CONFIDENCE BUY CALL (CE)* 🚀\n\n"
                f"• *Index:* NIFTY 50 @ {spot_price:.1f}\n"
                f"• *Recommended Strike:* *{atm_strike} CE*\n"
                f"• *Spot Stop-Loss:* {sl_level:.1f}\n"
                f"• *ADX Strength:* {adx_val:.1f} (Strong Trend)\n\n"
                f"👉 *Open Groww / Lemonn and punch {atm_strike} CE!*"
            )
            send_telegram(msg)
            return {"status": "SUCCESS_CE"}

        elif signal == "BUY_PE":
            msg = (
                f"🔥 *HIGH-CONFIDENCE BUY PUT (PE)* 🔥\n\n"
                f"• *Index:* NIFTY 50 @ {spot_price:.1f}\n"
                f"• *Recommended Strike:* *{atm_strike} PE*\n"
                f"• *Spot Stop-Loss:* {sl_level:.1f}\n"
                f"• *ADX Strength:* {adx_val:.1f} (Strong Breakdown)\n\n"
                f"👉 *Open Groww / Lemonn and punch {atm_strike} PE!*"
            )
            send_telegram(msg)
            return {"status": "SUCCESS_PE"}

    except Exception as e:
        return {"error": str(e)}

    return {"status": "IGNORED"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
