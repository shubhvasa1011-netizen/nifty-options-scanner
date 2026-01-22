import json
from datetime import datetime

class SimpleBacktest:
    """Backtest strategy using collected historical data"""
    
    def __init__(self, data_file="options_historical_data.json"):
        self.data_file = data_file
        self.trades = []
        self.total_profit = 0
        self.total_loss = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        self.load_data()
    
    def load_data(self):
        """Load collected historical data"""
        try:
            with open(self.data_file, 'r') as f:
                self.historical_data = json.load(f)
            print(f"✓ Loaded {len(self.historical_data)} snapshots")
        except FileNotFoundError:
            print(f"❌ Data file not found: {self.data_file}")
            print("💡 Run data_collector.py first to collect data!")
            self.historical_data = []
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            self.historical_data = []
    
    def find_option(self, snapshot, strike, option_type):
        """Find specific option in snapshot"""
        for option in snapshot.get('options', []):
            if option['strike'] == strike and option['type'] == option_type:
                return option
        return None
    
    def simulate_trade(self, entry_price, exit_price, quantity, trade_type, symbol):
        """Simulate a trade"""
        if trade_type == "BUY":
            profit = (exit_price - entry_price) * quantity
        else:
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
    
    def run_backtest(self, initial_capital=100000):
        """Run backtest on collected data"""
        
        if len(self.historical_data) < 2:
            print("❌ Not enough data to backtest!")
            print("💡 Need at least 2 snapshots. Run data_collector.py during market hours.")
            return
        
        print("\n" + "="*60)
        print("🔬 BACKTESTING WITH COLLECTED DATA")
        print("="*60)
        print(f"📊 Snapshots: {len(self.historical_data)}")
        print(f"💰 Initial Capital: ₹{initial_capital:,.2f}")
        print(f"📈 Strategy: Buy on 2% drop, Sell on 2% rise")
        print("="*60 + "\n")
        
        current_capital = initial_capital
        
        # Compare consecutive snapshots
        for i in range(len(self.historical_data) - 1):
            prev_snapshot = self.historical_data[i]
            curr_snapshot = self.historical_data[i + 1]
            
            prev_time = prev_snapshot.get('collected_at', 'Unknown')
            curr_time = curr_snapshot.get('collected_at', 'Unknown')
            
            print(f"\n📅 Comparing: {prev_time} → {curr_time}")
            print("-" * 60)
            
            # Check each option for signals
            for prev_option in prev_snapshot.get('options', []):
                strike = prev_option['strike']
                option_type = prev_option['type']
                prev_ltp = prev_option['ltp']
                
                # Find same option in current snapshot
                curr_option = self.find_option(curr_snapshot, strike, option_type)
                
                if not curr_option:
                    continue
                
                curr_ltp = curr_option['ltp']
                
                # Calculate price change
                if prev_ltp > 0:
                    price_change = ((curr_ltp - prev_ltp) / prev_ltp) * 100
                else:
                    continue
                
                symbol = f"{option_type} {strike}"
                
                # Check strategy conditions
                if price_change <= -2.0:
                    # BUY signal
                    quantity = 50
                    
                    # Simulate holding till next snapshot
                    if i + 2 < len(self.historical_data):
                        next_snapshot = self.historical_data[i + 2]
                        next_option = self.find_option(next_snapshot, strike, option_type)
                        
                        if next_option:
                            exit_price = next_option['ltp']
                        else:
                            exit_price = curr_ltp * 1.01  # Assume 1% profit
                    else:
                        exit_price = curr_ltp * 1.01
                    
                    trade = self.simulate_trade(curr_ltp, exit_price, quantity, "BUY", symbol)
                    
                    print(f"  🎯 BUY {symbol}")
                    print(f"     Price dropped: {abs(price_change):.2f}%")
                    print(f"     Entry: ₹{curr_ltp:.2f} → Exit: ₹{exit_price:.2f}")
                    print(f"     P&L: ₹{trade['profit']:,.2f} ({trade['profit_percent']:.2f}%)")
                    
                    current_capital += trade['profit']
                    print(f"     Capital: ₹{current_capital:,.2f}")
                
                elif price_change >= 2.0:
                    # SELL signal
                    quantity = 50
                    
                    if i + 2 < len(self.historical_data):
                        next_snapshot = self.historical_data[i + 2]
                        next_option = self.find_option(next_snapshot, strike, option_type)
                        
                        if next_option:
                            exit_price = next_option['ltp']
                        else:
                            exit_price = curr_ltp * 0.99
                    else:
                        exit_price = curr_ltp * 0.99
                    
                    trade = self.simulate_trade(curr_ltp, exit_price, quantity, "SELL", symbol)
                    
                    print(f"  🎯 SELL {symbol}")
                    print(f"     Price rose: {price_change:.2f}%")
                    print(f"     Entry: ₹{curr_ltp:.2f} → Exit: ₹{exit_price:.2f}")
                    print(f"     P&L: ₹{trade['profit']:,.2f} ({trade['profit_percent']:.2f}%)")
                    
                    current_capital += trade['profit']
                    print(f"     Capital: ₹{current_capital:,.2f}")
        
        # Print results
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
        
        if self.total_loss > 0:
            profit_factor = self.total_profit / self.total_loss
            print(f"   Profit Factor: {profit_factor:.2f}")
        
        print("\n" + "="*60)
        
        # Save results
        results = {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'net_profit': net_profit,
            'roi': roi,
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'trades': self.trades
        }
        
        filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}\n")


def main():
    """Run backtest"""
    backtest = SimpleBacktest()
    backtest.run_backtest(initial_capital=100000)


if __name__ == "__main__":
    main()
