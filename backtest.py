import os
from datetime import datetime, timedelta
import time
from angel_api import AngelOneAPI
import json

class StrategyBacktest:
    """Backtest the Nifty options strategy using Angel One historical data"""
    
    def __init__(self, angel_api):
        self.angel = angel_api
        self.trades = []
        self.total_profit = 0
        self.total_loss = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.open_positions = {}
        
    def get_historical_candles(self, symbol, token, from_date, to_date, interval="FIVE_MINUTE"):
        """Fetch historical candle data from Angel One"""
        try:
            params = {
                "exchange": "NFO",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            print(f"  Fetching {symbol} data...")
            data = self.angel.smart_api.getCandleData(params)
            
            if data and data.get('status'):
                candles = data.get('data', [])
                if candles:
                    print(f"  ✓ Got {len(candles)} candles for {symbol}")
                    return candles
                else:
                    print(f"  ⚠ No candle data for {symbol}")
            else:
                print(f"  ⚠ API returned no data for {symbol}")
            
            return None
                
        except Exception as e:
            print(f"  ❌ Error fetching {symbol}: {str(e)}")
            return None
    
    def get_nifty_historical_price(self, date):
        """Get Nifty spot price for a specific date"""
        try:
            # Nifty 50 index token
            nifty_token = "99926000"
            
            # Get data for that day
            from_date = date.replace(hour=9, minute=15)
            to_date = date.replace(hour=15, minute=30)
            
            params = {
                "exchange": "NSE",
                "symboltoken": nifty_token,
                "interval": "FIVE_MINUTE",
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            data = self.angel.smart_api.getCandleData(params)
            
            if data and data.get('status') and data.get('data'):
                # Get first candle's close price
                first_candle = data['data'][0]
                spot_price = float(first_candle[4])  # Close price
                return spot_price
            
            return None
            
        except Exception as e:
            print(f"  ❌ Error fetching Nifty price: {str(e)}")
            return None
    
    def simulate_trade(self, entry_price, exit_price, quantity, trade_type, symbol):
        """Simulate a single trade"""
        if trade_type == "BUY":
            profit = (exit_price - entry_price) * quantity
        else:  # SELL
            profit = (entry_price - exit_price) * quantity
        
        trade = {
            'symbol': symbol,
            'type': trade_type,
            'entry': entry_price,
            'exit': exit_price,
            'quantity': quantity,
            'profit': profit,
            'profit_percent': (profit / (entry_price * quantity)) * 100 if entry_price > 0 else 0
        }
        
        self.trades.append(trade)
        
        if profit > 0:
            self.total_profit += profit
            self.winning_trades += 1
        else:
            self.total_loss += abs(profit)
            self.losing_trades += 1
        
        return trade
    
    def run_simple_backtest(self, days_back=7, initial_capital=100000):
        """
        Run a simplified backtest using recent data
        This version tests the strategy on intraday price movements
        """
        print("\n" + "="*60)
        print("🔬 STARTING SIMPLIFIED BACKTEST")
        print("="*60)
        print(f"📅 Testing last {days_back} trading days")
        print(f"💰 Initial Capital: ₹{initial_capital:,.2f}")
        print(f"📊 Strategy: Buy on 2% drop, Sell on 2% rise")
        print("="*60 + "\n")
        
        current_capital = initial_capital
        
        # Get current date and go back
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get a recent trading day
        test_date = datetime.now() - timedelta(days=1)
        
        # Skip if weekend
        while test_date.weekday() >= 5:
            test_date -= timedelta(days=1)
        
        print(f"📆 Testing date: {test_date.strftime('%Y-%m-%d')}\n")
        
        # Get Nifty spot price
        print("Fetching Nifty spot price...")
        spot_price = self.get_nifty_historical_price(test_date)
        
        if not spot_price:
            print("⚠ Could not fetch Nifty historical price")
            print("💡 Using current spot price instead...")
            spot_price = self.angel.get_nifty_spot_price()
        
        if not spot_price:
            print("❌ Cannot proceed without spot price")
            self.print_results(initial_capital, current_capital)
            return
        
        print(f"✓ Nifty Spot: ₹{spot_price:.2f}\n")
        
        # Calculate ATM and strikes
        atm_strike = self.angel.get_atm_strike(spot_price)
        print(f"✓ ATM Strike: {atm_strike}\n")
        
        # Test with ATM and ATM±1 strikes only (to reduce API calls)
        strikes_to_test = [atm_strike - 50, atm_strike, atm_strike + 50]
        
        # Get expiry
        expiry_date = test_date + timedelta(days=(3 - test_date.weekday()) % 7)
        if expiry_date == test_date and test_date.hour >= 15:
            expiry_date += timedelta(days=7)
        expiry_str = expiry_date.strftime("%d-%b-%Y")
        
        print(f"✓ Testing Expiry: {expiry_str}\n")
        print("="*60)
        
        # Test each strike
        for strike in strikes_to_test:
            print(f"\n📊 Testing Strike: {strike}")
            print("-" * 40)
            
            # Test CE option
            ce_symbol = self.angel._get_option_symbol(strike, "CE", expiry_str)
            print(f"\n  Testing {ce_symbol}...")
            
            # Search for token
            try:
                search_result = self.angel.smart_api.searchScrip("NFO", ce_symbol)
                
                if search_result and search_result.get('status') and search_result.get('data'):
                    token = search_result['data'][0]['symboltoken']
                    
                    # Get historical data
                    from_time = test_date.replace(hour=9, minute=15)
                    to_time = test_date.replace(hour=15, minute=30)
                    
                    candles = self.get_historical_candles(ce_symbol, token, from_time, to_time)
                    
                    if candles and len(candles) >= 2:
                        # Analyze price movements
                        entry_price = float(candles[0][4])  # First candle close
                        high_price = max([float(c[2]) for c in candles])  # Highest high
                        low_price = min([float(c[3]) for c in candles])  # Lowest low
                        exit_price = float(candles[-1][4])  # Last candle close
                        
                        print(f"  Entry: ₹{entry_price:.2f}")
                        print(f"  High:  ₹{high_price:.2f}")
                        print(f"  Low:   ₹{low_price:.2f}")
                        print(f"  Exit:  ₹{exit_price:.2f}")
                        
                        # Check if strategy would have triggered
                        price_change = ((exit_price - entry_price) / entry_price) * 100
                        
                        if abs(price_change) >= 2.0:
                            # Simulate trade
                            quantity = 50  # 1 lot
                            
                            if price_change <= -2.0:
                                # BUY signal (price dropped)
                                trade = self.simulate_trade(entry_price, exit_price, quantity, "BUY", ce_symbol)
                                print(f"\n  🎯 BUY SIGNAL (Price dropped {abs(price_change):.2f}%)")
                            else:
                                # SELL signal (price rose)
                                trade = self.simulate_trade(entry_price, exit_price, quantity, "SELL", ce_symbol)
                                print(f"\n  🎯 SELL SIGNAL (Price rose {price_change:.2f}%)")
                            
                            current_capital += trade['profit']
                            print(f"  P&L: ₹{trade['profit']:,.2f} ({trade['profit_percent']:.2f}%)")
                            print(f"  Capital: ₹{current_capital:,.2f}")
                        else:
                            print(f"  ⚪ No signal (Price change: {price_change:.2f}%)")
                    
                    time.sleep(1)  # Rate limiting
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
            
            # Test PE option
            pe_symbol = self.angel._get_option_symbol(strike, "PE", expiry_str)
            print(f"\n  Testing {pe_symbol}...")
            
            try:
                search_result = self.angel.smart_api.searchScrip("NFO", pe_symbol)
                
                if search_result and search_result.get('status') and search_result.get('data'):
                    token = search_result['data'][0]['symboltoken']
                    
                    from_time = test_date.replace(hour=9, minute=15)
                    to_time = test_date.replace(hour=15, minute=30)
                    
                    candles = self.get_historical_candles(pe_symbol, token, from_time, to_time)
                    
                    if candles and len(candles) >= 2:
                        entry_price = float(candles[0][4])
                        high_price = max([float(c[2]) for c in candles])
                        low_price = min([float(c[3]) for c in candles])
                        exit_price = float(candles[-1][4])
                        
                        print(f"  Entry: ₹{entry_price:.2f}")
                        print(f"  High:  ₹{high_price:.2f}")
                        print(f"  Low:   ₹{low_price:.2f}")
                        print(f"  Exit:  ₹{exit_price:.2f}")
                        
                        price_change = ((exit_price - entry_price) / entry_price) * 100
                        
                        if abs(price_change) >= 2.0:
                            quantity = 50
                            
                            if price_change <= -2.0:
                                trade = self.simulate_trade(entry_price, exit_price, quantity, "BUY", pe_symbol)
                                print(f"\n  🎯 BUY SIGNAL (Price dropped {abs(price_change):.2f}%)")
                            else:
                                trade = self.simulate_trade(entry_price, exit_price, quantity, "SELL", pe_symbol)
                                print(f"\n  🎯 SELL SIGNAL (Price rose {price_change:.2f}%)")
                            
                            current_capital += trade['profit']
                            print(f"  P&L: ₹{trade['profit']:,.2f} ({trade['profit_percent']:.2f}%)")
                            print(f"  Capital: ₹{current_capital:,.2f}")
                        else:
                            print(f"  ⚪ No signal (Price change: {price_change:.2f}%)")
                    
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        
        # Print final results
        self.print_results(initial_capital, current_capital)
    
    def print_results(self, initial_capital, final_capital):
        """Print backtest results"""
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS")
        print("="*60)
        
        total_trades = len(self.trades)
        net_profit = final_capital - initial_capital
        roi = (net_profit / initial_capital) * 100 if initial_capital > 0 else 0
        
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = self.total_profit / self.winning_trades if self.winning_trades > 0 else 0
        avg_loss = self.total_loss / self.losing_trades if self.losing_trades > 0 else 0
        
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ₹{initial_capital:,.2f}")
        print(f"   Final:   ₹{final_capital:,.2f}")
        print(f"   Net P&L: ₹{net_profit:,.2f}")
        print(f"   ROI:     {roi:.2f}%")
        
        print(f"\n📈 TRADES:")
        print(f"   Total:   {total_trades}")
        print(f"   Winners: {self.winning_trades} ({win_rate:.2f}%)")
        print(f"   Losers:  {self.losing_trades} ({100-win_rate:.2f}%)")
        
        print(f"\n💵 PROFIT/LOSS:")
        print(f"   Total Profit: ₹{self.total_profit:,.2f}")
        print(f"   Total Loss:   ₹{self.total_loss:,.2f}")
        print(f"   Avg Win:      ₹{avg_win:,.2f}")
        print(f"   Avg Loss:     ₹{avg_loss:,.2f}")
        
        if avg_loss > 0:
            profit_factor = self.total_profit / self.total_loss
            print(f"   Profit Factor: {profit_factor:.2f}")
        
        print("\n" + "="*60)
        
        # Save results
        self.save_results(initial_capital, final_capital)
    
    def save_results(self, initial_capital, final_capital):
        """Save backtest results to JSON file"""
        results = {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'net_profit': final_capital - initial_capital,
            'roi': ((final_capital - initial_capital) / initial_capital) * 100,
            'total_trades': len(self.trades),
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'trades': self.trades
        }
        
        filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


def main():
    """Run backtest"""
    
    # Get credentials
    ANGEL_API_KEY = os.getenv('ANGEL_API_KEY')
    ANGEL_CLIENT_ID = os.getenv('ANGEL_CLIENT_ID')
    ANGEL_PASSWORD = os.getenv('ANGEL_PASSWORD')
    ANGEL_TOTP_SECRET = os.getenv('ANGEL_TOTP_SECRET')
    
    if not all([ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET]):
        print("❌ Missing Angel One credentials!")
        return
    
    # Initialize Angel One API
    print("Connecting to Angel One...")
    angel = AngelOneAPI(
        api_key=ANGEL_API_KEY,
        client_id=ANGEL_CLIENT_ID,
        password=ANGEL_PASSWORD,
        totp_secret=ANGEL_TOTP_SECRET
    )
    
    # Initialize backtest
    backtest = StrategyBacktest(angel)
    
    # Run simplified backtest
    backtest.run_simple_backtest(
        days_back=1,  # Test last trading day
        initial_capital=100000
    )


if __name__ == "__main__":
    main()
