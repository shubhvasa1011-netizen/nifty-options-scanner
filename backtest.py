import os
from datetime import datetime, timedelta
import time
from angel_api import AngelOneAPI
import json

class StrategyBacktest:
    """Backtest the Nifty options strategy using historical data"""
    
    def __init__(self, angel_api):
        self.angel = angel_api
        self.trades = []
        self.total_profit = 0
        self.total_loss = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
    def get_historical_candles(self, symbol, token, from_date, to_date, interval="ONE_MINUTE"):
        """
        Fetch historical candle data from Angel One
        interval options: ONE_MINUTE, THREE_MINUTE, FIVE_MINUTE, TEN_MINUTE, 
                         FIFTEEN_MINUTE, THIRTY_MINUTE, ONE_HOUR, ONE_DAY
        """
        try:
            params = {
                "exchange": "NFO",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            data = self.angel.smart_api.getCandleData(params)
            
            if data and data['status']:
                return data['data']
            else:
                print(f"⚠ No historical data for {symbol}")
                return None
                
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def simulate_trade(self, entry_price, exit_price, quantity, trade_type):
        """Simulate a single trade"""
        if trade_type == "BUY":
            profit = (exit_price - entry_price) * quantity
        else:  # SELL
            profit = (entry_price - exit_price) * quantity
        
        trade = {
            'type': trade_type,
            'entry': entry_price,
            'exit': exit_price,
            'quantity': quantity,
            'profit': profit,
            'profit_percent': (profit / (entry_price * quantity)) * 100
        }
        
        self.trades.append(trade)
        
        if profit > 0:
            self.total_profit += profit
            self.winning_trades += 1
        else:
            self.total_loss += abs(profit)
            self.losing_trades += 1
        
        return trade
    
    def check_strategy_conditions(self, option_data, prev_data):
        """
        Check if strategy conditions are met
        This uses the same logic as strategy.py
        """
        signals = []
        
        for option in option_data:
            strike = option['strike']
            option_type = option['type']
            current_ltp = option['ltp']
            
            # Find previous data for this option
            prev_option = None
            if prev_data:
                for prev in prev_data:
                    if prev['strike'] == strike and prev['type'] == option_type:
                        prev_option = prev
                        break
            
            if not prev_option:
                continue
            
            prev_ltp = prev_option['ltp']
            
            # Calculate price change percentage
            price_change = ((current_ltp - prev_ltp) / prev_ltp) * 100
            
            # Strategy conditions (customize these based on your strategy.py)
            
            # BUY Signal: Price dropped by 2% or more
            if price_change <= -2.0:
                signals.append({
                    'action': 'BUY',
                    'strike': strike,
                    'type': option_type,
                    'entry_price': current_ltp,
                    'reason': f'Price dropped {abs(price_change):.2f}%'
                })
            
            # SELL Signal: Price increased by 2% or more
            elif price_change >= 2.0:
                signals.append({
                    'action': 'SELL',
                    'strike': strike,
                    'type': option_type,
                    'entry_price': current_ltp,
                    'reason': f'Price increased {price_change:.2f}%'
                })
        
        return signals
    
    def run_backtest(self, start_date, end_date, initial_capital=100000):
        """
        Run backtest for specified date range
        
        Args:
            start_date: datetime object for start date
            end_date: datetime object for end date
            initial_capital: Starting capital in INR
        """
        print("\n" + "="*60)
        print("🔬 STARTING BACKTEST")
        print("="*60)
        print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Initial Capital: ₹{initial_capital:,.2f}")
        print("="*60 + "\n")
        
        current_capital = initial_capital
        current_date = start_date
        
        # Store previous scan data
        prev_option_data = None
        
        # Simulate day by day
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            print(f"\n📆 Testing: {current_date.strftime('%Y-%m-%d')}")
            
            # Get Nifty spot price (you'd need to implement this)
            # For now, we'll use a placeholder
            spot_price = 23500  # This should be fetched from historical data
            
            atm_strike = self.angel.get_atm_strike(spot_price)
            strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
            
            # Get weekly expiry for this date
            # This is simplified - you'd need proper expiry calculation
            expiry_date = current_date + timedelta(days=(3 - current_date.weekday()) % 7)
            expiry_str = expiry_date.strftime("%d-%b-%Y")
            
            # Fetch option data for each strike
            option_data = []
            
            for strike in strikes_to_scan:
                # CE option
                ce_symbol = self.angel._get_option_symbol(strike, "CE", expiry_str)
                # PE option
                pe_symbol = self.angel._get_option_symbol(strike, "PE", expiry_str)
                
                # In real backtest, you'd fetch historical data here
                # For demo, we'll use placeholder data
                # You need to implement actual historical data fetching
                
                print(f"  Scanning {ce_symbol} and {pe_symbol}...")
                
                # Placeholder - replace with actual historical data
                option_data.append({
                    'strike': strike,
                    'type': 'CE',
                    'ltp': 100 + (strike % 100),  # Dummy data
                    'symbol': ce_symbol
                })
                
                option_data.append({
                    'strike': strike,
                    'type': 'PE',
                    'ltp': 100 + (strike % 100),  # Dummy data
                    'symbol': pe_symbol
                })
            
            # Check strategy conditions
            if prev_option_data:
                signals = self.check_strategy_conditions(option_data, prev_option_data)
                
                for signal in signals:
                    print(f"\n  🎯 SIGNAL: {signal['action']} {signal['type']} {signal['strike']}")
                    print(f"     Entry: ₹{signal['entry_price']:.2f}")
                    print(f"     Reason: {signal['reason']}")
                    
                    # Simulate trade with 1 lot (50 quantity for Nifty)
                    quantity = 50
                    
                    # Simulate exit after some time (simplified)
                    # In real backtest, you'd track positions and exit based on conditions
                    exit_price = signal['entry_price'] * 1.02  # 2% profit target
                    
                    trade = self.simulate_trade(
                        signal['entry_price'],
                        exit_price,
                        quantity,
                        signal['action']
                    )
                    
                    current_capital += trade['profit']
                    
                    print(f"     Exit: ₹{exit_price:.2f}")
                    print(f"     P&L: ₹{trade['profit']:,.2f} ({trade['profit_percent']:.2f}%)")
                    print(f"     Capital: ₹{current_capital:,.2f}")
            
            # Store current data for next iteration
            prev_option_data = option_data
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Print backtest results
        self.print_results(initial_capital, current_capital)
    
    def print_results(self, initial_capital, final_capital):
        """Print backtest results"""
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS")
        print("="*60)
        
        total_trades = len(self.trades)
        net_profit = final_capital - initial_capital
        roi = (net_profit / initial_capital) * 100
        
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
        
        # Save results to file
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
    
    # Get credentials from environment
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
    
    # Define backtest period
    # Last 7 days for testing
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Run backtest
    backtest.run_backtest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000  # 1 Lakh
    )


if __name__ == "__main__":
    main()
