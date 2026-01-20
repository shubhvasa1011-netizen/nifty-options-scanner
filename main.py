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
SCAN_INTERVAL = 60  # 1 minute (change to 30 for faster scanning)

# Trading hours (IST)
TRADING_START = dt_time(9, 30)
TRADING_END = dt_time(15, 0)

# Error tracking
consecutive_errors = 0
MAX_CONSECUTIVE_ERRORS = 5

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
    global consecutive_errors
    
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
    startup_msg = "✅ Nifty Options Scanner is now LIVE!\n\n📊 Monitoring ATM ± 5 strikes\n⏰ Active during market hours (9:30 AM - 3:00 PM)"
    telegram.send_message(startup_msg)
    
    # Wait for NSE session to be ready
    print("\nWaiting for NSE session to initialize...")
    time.sleep(3)
    
    while True:
        try:
            if is_trading_hours():
                current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
                print(f"\n[{current_time.strftime('%H:%M:%S')}] Scanning options...")
                
                # Fetch option chain data
                option_data = nse.get_option_chain()
                
                if option_data:
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Process data through strategy engine
                    strategy.process_options(option_data)
                else:
                    consecutive_errors += 1
                    print(f"⚠️ Failed to fetch option chain data (Error {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")
                    
                    # If too many consecutive errors, try to recover
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        print("⚠️ Too many errors, reinitializing NSE connection...")
                        telegram.send_message("⚠️ Scanner experiencing issues with NSE API. Attempting to recover...")
                        nse = NSEOptionChain()  # Reinitialize
                        consecutive_errors = 0
                        time.sleep(10)  # Wait before retrying
            else:
                current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
                
                # Only print waiting message every 5 minutes to reduce spam
                if current_time.minute % 5 == 0 and current_time.second < SCAN_INTERVAL:
                    print(f"[{current_time.strftime('%H:%M:%S')}] Outside trading hours. Waiting...")
                
            # Wait before next scan
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Scanner stopped by user")
            telegram.send_message("🛑 Nifty Options Scanner has been stopped.")
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"❌ Unexpected error: {str(e)} (Error {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS})")
            
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                error_msg = f"❌ Scanner encountered multiple errors. Last error: {str(e)}\n\nAttempting to recover..."
                telegram.send_message(error_msg)
                nse = NSEOptionChain()  # Reinitialize
                consecutive_errors = 0
                time.sleep(10)
            else:
                time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
