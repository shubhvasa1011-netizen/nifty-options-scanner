# 📊 Backtesting Guide for Nifty Options Strategy

Complete guide to backtest your strategy using Angel One SmartAPI historical data.

---

## **🎯 What is Backtesting?**

Backtesting allows you to test your trading strategy on **historical data** to see how it would have performed in the past. This helps you:

- ✅ Validate strategy profitability
- ✅ Calculate win rate and risk/reward
- ✅ Optimize entry/exit conditions
- ✅ Build confidence before live trading

---

## **📥 Setup**

### **1. Download Backtest Files**

Download these files from GitHub:
- `backtest.py` - Main backtesting engine
- `run_backtest.bat` - Easy run script

Or download complete ZIP:
https://github.com/shubhvasa1011-netizen/nifty-options-scanner/archive/refs/heads/main.zip

### **2. Update Credentials**

Edit `run_backtest.bat` with your Angel One credentials:

```batch
set ANGEL_API_KEY=your_api_key
set ANGEL_CLIENT_ID=your_client_id
set ANGEL_PASSWORD=your_mpin
set ANGEL_TOTP_SECRET=your_totp_secret
```

---

## **🚀 How to Run Backtest**

### **Method 1: Using Batch File (Easiest)**

1. **Double-click** `run_backtest.bat`
2. Wait for backtest to complete
3. Check results in console and saved JSON file

### **Method 2: Using Command Line**

```bash
python backtest.py
```

---

## **📊 What You'll Get**

### **Console Output:**

```
🔬 STARTING BACKTEST
====================================
📅 Period: 2026-01-13 to 2026-01-20
💰 Initial Capital: ₹100,000.00
====================================

📆 Testing: 2026-01-13
  Scanning NIFTY13JAN26C23500...
  🎯 SIGNAL: BUY CE 23500
     Entry: ₹125.50
     Exit: ₹127.81
     P&L: ₹115.50 (2.00%)
     Capital: ₹100,115.50

📊 BACKTEST RESULTS
====================================
💰 CAPITAL:
   Initial: ₹100,000.00
   Final:   ₹105,250.00
   Net P&L: ₹5,250.00
   ROI:     5.25%

📈 TRADES:
   Total:   25
   Winners: 18 (72.00%)
   Losers:  7 (28.00%)

💵 PROFIT/LOSS:
   Total Profit: ₹8,500.00
   Total Loss:   ₹3,250.00
   Avg Win:      ₹472.22
   Avg Loss:     ₹464.29
   Profit Factor: 2.62
```

### **JSON Results File:**

A detailed JSON file is saved with all trade data:

```json
{
  "initial_capital": 100000,
  "final_capital": 105250,
  "net_profit": 5250,
  "roi": 5.25,
  "total_trades": 25,
  "winning_trades": 18,
  "losing_trades": 7,
  "trades": [...]
}
```

---

## **⚙️ Customization**

### **Change Backtest Period**

Edit `backtest.py`, line ~280:

```python
# Last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Or specific dates
start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 1, 20)
```

### **Change Initial Capital**

```python
backtest.run_backtest(
    start_date=start_date,
    end_date=end_date,
    initial_capital=200000  # 2 Lakhs
)
```

### **Modify Strategy Conditions**

Edit the `check_strategy_conditions` method in `backtest.py`:

```python
# BUY Signal: Price dropped by 3% or more
if price_change <= -3.0:
    signals.append({...})

# SELL Signal: Price increased by 3% or more
elif price_change >= 3.0:
    signals.append({...})
```

---

## **📈 Understanding Results**

### **Key Metrics:**

1. **ROI (Return on Investment)**
   - Total profit/loss as percentage of initial capital
   - Higher is better

2. **Win Rate**
   - Percentage of profitable trades
   - 60%+ is considered good

3. **Profit Factor**
   - Total profit ÷ Total loss
   - Above 2.0 is excellent
   - Above 1.5 is good
   - Below 1.0 means losing strategy

4. **Average Win vs Average Loss**
   - Ideally, Avg Win > Avg Loss
   - Shows risk/reward ratio

---

## **⚠️ Important Notes**

### **Limitations:**

1. **Historical Data Access**
   - Angel One provides limited historical data
   - May need to run backtest in smaller chunks

2. **Slippage Not Included**
   - Real trades may have price slippage
   - Backtest assumes perfect fills

3. **Brokerage Not Included**
   - Add brokerage costs manually
   - Angel One: ~₹20 per order

4. **Market Conditions**
   - Past performance ≠ Future results
   - Market conditions change

### **Best Practices:**

1. **Test Multiple Periods**
   - Bull markets
   - Bear markets
   - Sideways markets

2. **Walk-Forward Testing**
   - Test on recent data
   - Validate on older data

3. **Paper Trading**
   - After backtest, do paper trading
   - Then move to live with small capital

---

## **🔧 Advanced Features**

### **Add Stop Loss**

Edit `simulate_trade` method:

```python
# Add 1% stop loss
stop_loss = signal['entry_price'] * 0.99
if current_price <= stop_loss:
    exit_price = stop_loss
```

### **Add Trailing Stop**

```python
# Trail stop by 0.5%
trailing_stop = max_price * 0.995
```

### **Position Sizing**

```python
# Risk 2% of capital per trade
risk_amount = current_capital * 0.02
quantity = risk_amount / entry_price
```

---

## **📊 Export Results to Excel**

Install pandas:
```bash
pip install pandas openpyxl
```

Add to `backtest.py`:
```python
import pandas as pd

df = pd.DataFrame(self.trades)
df.to_excel('backtest_results.xlsx', index=False)
```

---

## **🎯 Next Steps**

1. **Run backtest** on last 30 days
2. **Analyze results** - Is ROI positive? Win rate good?
3. **Optimize strategy** - Adjust entry/exit conditions
4. **Re-test** with new parameters
5. **Paper trade** for 1 week
6. **Go live** with small capital

---

## **💡 Tips**

- Start with **small date ranges** (7 days)
- Test **different market conditions**
- **Document** what works and what doesn't
- **Don't overfit** - simple strategies often work best
- **Consider transaction costs** in final calculations

---

## **🆘 Troubleshooting**

**"No historical data available"**
- Angel One may have limited data
- Try shorter date ranges
- Use recent dates only

**"Too many API calls"**
- Add delays between requests
- Reduce date range
- Use higher timeframes

**"Login failed"**
- Check credentials in batch file
- Ensure TOTP secret is correct

---

**Ready to backtest? Double-click `run_backtest.bat` and see how your strategy performs!** 🚀
