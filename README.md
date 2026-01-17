# 🚀 Nifty Options Scanner

Automated Nifty weekly options scanner with **90→100 breakout strategy** and real-time Telegram notifications.

## 📊 Strategy Overview

### Entry Logic
1. **Qualification**: Option must touch ₹90 (from any direction - above or below)
2. **Entry Trigger**: When qualified option breaks ₹100

**Examples:**
- ✅ 120 → 90 → 100 (ENTER at 100)
- ✅ 70 → 90 → 100 (ENTER at 100)
- ❌ 95 → 100 (NO ENTRY - never touched 90)

### Trade Parameters
- **Index**: Nifty Weekly Options
- **Scan Range**: ATM ± 5 strikes (10 CE + 10 PE = 20 options)
- **Position Size**: 1 lot (25 qty)
- **Target**: ₹115
- **Stop Loss**: ₹89
- **Max Consecutive Same-Side Trades**: 3
- **Max Positions**: 1 at a time
- **Trading Hours**: 9:30 AM - 3:00 PM IST
- **Scan Frequency**: Every 1 minute

## 🏗️ Architecture

```
┌─────────────────────┐
│   main.py           │  ← Main scanner loop
│   (Entry Point)     │
└──────────┬──────────┘
           │
           ├─→ nse_api.py        (Fetch NSE option chain)
           ├─→ strategy.py       (90→100 breakout logic)
           └─→ telegram_bot.py   (Send notifications)
```

## 📱 Telegram Notifications

### Entry Signal
```
🚀 ENTRY SIGNAL

Type: CALL
Strike: 23500 CE
Entry Price: ₹100.50
Target: ₹115
Stop Loss: ₹89

Qualified: Touched ₹90
Time: 10:45:32 AM
```

### Target Hit
```
✅ TARGET HIT

Strike: 23500 CE
Entry: ₹100.50
Exit: ₹115.20
P&L: ₹14.70 per qty
Total P&L: ₹367.50 (25 qty)

Time: 11:15:18 AM
```

### Stop Loss Hit
```
❌ STOP LOSS HIT

Strike: 23500 CE
Entry: ₹100.50
Exit: ₹88.80
Loss: ₹11.70 per qty
Total P&L: -₹292.50 (25 qty)

Time: 11:30:45 AM
```

## 🚀 Deployment on Railway

### Prerequisites
1. Railway account (https://railway.app)
2. Telegram bot token
3. Telegram chat ID

### Environment Variables
Set these in Railway dashboard:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Deploy Steps
1. Fork this repository
2. Connect Railway to your GitHub account
3. Create new project from this repo
4. Add environment variables
5. Deploy! 🎉

## 🛠️ Local Development

### Setup
```bash
# Clone repository
git clone https://github.com/shubhvasa1011-netizen/nifty-options-scanner.git
cd nifty-options-scanner

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run scanner
python main.py
```

## 📁 File Structure

```
nifty-options-scanner/
├── main.py              # Main scanner loop
├── nse_api.py          # NSE option chain API
├── strategy.py         # 90→100 breakout strategy
├── telegram_bot.py     # Telegram notifications
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment config
├── runtime.txt        # Python version
└── README.md          # Documentation
```

## ⚙️ Configuration

Edit `main.py` to customize:
- `SCAN_INTERVAL`: Scan frequency (default: 60 seconds)
- `TRADING_START`: Market open time (default: 9:30 AM)
- `TRADING_END`: Market close time (default: 3:00 PM)

## 🔒 Security Notes

- Never commit API tokens to Git
- Use environment variables for sensitive data
- Keep your Telegram bot token private

## 📊 Data Source

Uses **NSE's public option chain API** (no authentication required):
- Real-time option prices
- Weekly expiry contracts
- Open Interest & Volume data

## ⚠️ Disclaimer

This is an educational project. Use at your own risk. Always:
- Test thoroughly before live trading
- Understand the strategy completely
- Never risk more than you can afford to lose
- Consult a financial advisor

## 📝 License

MIT License - Feel free to modify and use!

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

---

**Built with ❤️ for Indian options traders**
