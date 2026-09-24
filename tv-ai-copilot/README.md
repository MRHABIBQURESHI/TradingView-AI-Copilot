# TradingView AI Copilot (v1 — MVP)

Chrome extension jo TradingView chart ke upar ek overlay panel dikhata hai:
Structure (uptrend/downtrend), MACD, ADX(32), RSI, Stochastic, CMF, OBV,
Fibonacci levels, pichle 10-15 candles ke naam/pattern, aur alag-alag time
horizons (1h se 48h tak) ke liye ek rule-based bullish/bearish probability +
projected price range.

**Ye extension khud koi trade nahi leta. Sirf information dikhata hai — decision
hamesha aapka.**

---

## 1. Backend chalana (apne PC par)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Test karne ke liye browser mein kholein:
`http://127.0.0.1:8000/analyze?symbol=BTCUSDT&interval=1h`

Agar JSON response mil raha hai, backend sahi chal raha hai.

## 2. Extension load karna (Chrome mein)

1. Chrome mein jaayein: `chrome://extensions`
2. Top-right "Developer mode" ON karein
3. "Load unpacked" click karein
4. `extension` folder select karein
5. Ab TradingView.com kholein, koi bhi chart — panel top-right corner mein
   dikhega (draggable hai, kahin bhi move kar sakte hain)

Panel automatically har 15 second mein refresh hota hai. Interval
(15m/30m/1h/4h/1D) dropdown se change kar sakte hain.

---

## Important Notes

- **Data source:** Abhi Binance ka public API use ho raha hai (free, no API
  key). Agar aap kisi aur exchange/broker ka data chahte hain, sirf
  `backend/data.py` ka `fetch_klines()` function badalna hoga — baaki sab
  code same rahega.
- **"AI Confidence" / Probability:** Ye ek transparent rule-based weighted
  score hai (indicators ka combination), machine-learning prediction nahi.
  `backend/structure.py` mein `composite_score()` function mein weights
  dekh/badal sakte hain.
- **Projected price ranges:** ATR (volatility) based extrapolation hain —
  jitna lamba horizon (48h), utni wide aur kam reliable range hogi. Ye
  guarantee nahi, ek statistical estimate hai.
- **Symbol detection:** Extension TradingView URL se symbol read karta hai
  (`?symbol=BINANCE:BTCUSDT` jaisa). Agar kabhi galat symbol dikhe, URL check
  karein.

## Git par push karna

```bash
cd tv-ai-copilot
git init
git add .
git commit -m "Initial MVP: TradingView AI Copilot"
git remote add origin <your-repo-url>
git push -u origin main
```

## Next Steps (v2 ideas)

- Real ML model (LightGBM/XGBoost) train karke composite_score ko replace
  karna historical data pe backtested probability se
- WebSocket use karke real-time updates (15s polling ki jagah)
- Multiple timeframe confluence (1h + 4h + 1D signal ek saath dekhna)
- Alerts (browser notification jab signal change ho)
- Backend ko VPS par deploy karna taake extension kahin se bhi kaam kare
