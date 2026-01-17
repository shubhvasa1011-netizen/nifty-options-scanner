import os
import time
import requests
from datetime import datetime, time as dt_time
import pytz
from strategy import StrategyEngine
from telegram_bot import TelegramBot
from nse_api import NSEOptionChain

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SCAN_INTERVAL = 60  # 1 minute

# Trading hours (IST)
TRADING_START = dt_time(9, 30)
TRADING_END = dt_time(15, 0)

def is_trading_hours():
    """Check if current time is within trading hours"""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).time()
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if datetime.now(ist).weekday() >= 5:
        return False
    
    return TRADING_START <= now <= TRADING_END

def main():
    """Main scanner loop"""
    print("🚀 Nifty Options Scanner Started!")
    print(f"📱 Telegram Bot: Connected")
    print(f"⏰ Trading Hours: 9:30 AM - 3:00 PM IST")
    print(f"🔍 Scan Interval: {SCAN_INTERVAL} seconds")
    print("-" * 50)
    
    # Initialize components
    telegram = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    nse = NSEOptionChain()
    strategy = StrategyEngine(telegram)
    
    # Send startup notification
    telegram.send_message("✅ Nifty Options Scanner is now LIVE!\n\n📊 Monitoring ATM ± 5 strikes\n⏰ Active during market hours (9:30 AM - 3:00 PM)")
    
    while True:
        try:
            if is_trading_hours():
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning options...")
                
                # Fetch option chain data
                option_data = nse.get_option_chain()
                
                if option_data:
                    # Process data through strategy engine
                    strategy.process_options(option_data)
                else:
                    print("⚠️ Failed to fetch option chain data")
            else:
                current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
                print(f"[{current_time.strftime('%H:%M:%S')}] Outside trading hours. Waiting...")
                
            # Wait before next scan
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Scanner stopped by user")
            telegram.send_message("🛑 Nifty Options Scanner has been stopped.")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
