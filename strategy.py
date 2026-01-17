from datetime import datetime
from collections import defaultdict

class StrategyEngine:
    """
    Implements the 90→100 breakout strategy:
    1. Option must touch ₹90 (from any direction) to become "qualified"
    2. Entry trigger: When qualified option breaks ₹100
    3. Target: ₹115 | Stop Loss: ₹89
    4. Max 3 consecutive same-side trades
    5. Only 1 position at a time
    """
    
    def __init__(self, telegram_bot):
        self.telegram = telegram_bot
        
        # Track qualified options (touched 90)
        self.qualified_options = set()
        
        # Track price history for qualification check
        self.price_history = defaultdict(list)
        
        # Current open position
        self.open_position = None
        
        # Consecutive trade counter
        self.consecutive_trades = {'CE': 0, 'PE': 0}
        
        # Track entered options to avoid re-entry
        self.entered_options = set()
    
    def _get_option_key(self, strike, option_type):
        """Generate unique key for option"""
        return f"{strike}_{option_type}"
    
    def _check_qualification(self, option_key, current_price):
        """Check if option has touched ₹90"""
        # Add current price to history
        self.price_history[option_key].append(current_price)
        
        # Keep only last 100 prices to avoid memory issues
        if len(self.price_history[option_key]) > 100:
            self.price_history[option_key] = self.price_history[option_key][-100:]
        
        # Check if price has touched 90 (with ±0.5 tolerance)
        for price in self.price_history[option_key]:
            if 89.5 <= price <= 90.5:
                if option_key not in self.qualified_options:
                    self.qualified_options.add(option_key)
                    print(f"✅ QUALIFIED: {option_key} touched ₹90")
                return True
        
        return option_key in self.qualified_options
    
    def _check_entry_trigger(self, option, option_key):
        """Check if qualified option breaks ₹100"""
        if option_key not in self.qualified_options:
            return False
        
        if option_key in self.entered_options:
            return False
        
        current_price = option['ltp']
        
        # Entry trigger: breaks 100
        if current_price >= 100:
            return True
        
        return False
    
    def _check_max_consecutive_trades(self, option_type):
        """Check if max consecutive same-side trades reached"""
        return self.consecutive_trades[option_type] >= 3
    
    def _enter_position(self, option):
        """Enter a new position"""
        option_key = self._get_option_key(option['strike'], option['type'])
        
        # Check max consecutive trades
        if self._check_max_consecutive_trades(option['type']):
            print(f"⚠️ Max 3 consecutive {option['type']} trades reached. Skipping entry.")
            return
        
        self.open_position = {
            'strike': option['strike'],
            'type': option['type'],
            'entry_price': option['ltp'],
            'target': 115,
            'stop_loss': 89,
            'entry_time': datetime.now(),
            'option_key': option_key
        }
        
        self.entered_options.add(option_key)
        
        # Send entry notification
        message = f"""🚀 ENTRY SIGNAL

Type: {option['type']}
Strike: {option['strike']} {option['type']}
Entry Price: ₹{option['ltp']:.2f}
Target: ₹115
Stop Loss: ₹89

Qualified: Touched ₹90
Time: {datetime.now().strftime('%I:%M:%S %p')}
"""
        self.telegram.send_message(message)
        print(f"\n🚀 ENTRY: {option['strike']} {option['type']} @ ₹{option['ltp']:.2f}")
    
    def _exit_position(self, current_price, exit_type):
        """Exit current position"""
        if not self.open_position:
            return
        
        entry_price = self.open_position['entry_price']
        pnl_per_qty = current_price - entry_price
        total_pnl = pnl_per_qty * 25  # 25 qty per lot
        
        # Update consecutive trade counter
        option_type = self.open_position['type']
        if exit_type == 'TARGET':
            self.consecutive_trades[option_type] += 1
            self.consecutive_trades['CE' if option_type == 'PE' else 'PE'] = 0
            emoji = "✅"
        else:
            self.consecutive_trades[option_type] = 0
            emoji = "❌"
        
        # Send exit notification
        message = f"""{emoji} {exit_type} HIT

Strike: {self.open_position['strike']} {self.open_position['type']}
Entry: ₹{entry_price:.2f}
Exit: ₹{current_price:.2f}
P&L: ₹{pnl_per_qty:.2f} per qty
Total P&L: ₹{total_pnl:.2f} (25 qty)

Consecutive {option_type} trades: {self.consecutive_trades[option_type]}/3

Time: {datetime.now().strftime('%I:%M:%S %p')}
"""
        self.telegram.send_message(message)
        print(f"\n{emoji} {exit_type}: {self.open_position['strike']} {self.open_position['type']} @ ₹{current_price:.2f} | P&L: ₹{total_pnl:.2f}")
        
        # Clear position
        self.open_position = None
    
    def _monitor_position(self, option):
        """Monitor open position for target/stop loss"""
        if not self.open_position:
            return
        
        # Check if this is the same option as open position
        if (option['strike'] == self.open_position['strike'] and 
            option['type'] == self.open_position['type']):
            
            current_price = option['ltp']
            
            # Check target
            if current_price >= self.open_position['target']:
                self._exit_position(current_price, 'TARGET')
            
            # Check stop loss
            elif current_price <= self.open_position['stop_loss']:
                self._exit_position(current_price, 'STOP LOSS')
    
    def process_options(self, option_data):
        """Process option chain data and execute strategy"""
        if not option_data or 'options' not in option_data:
            return
        
        options = option_data['options']
        
        for option in options:
            if option['ltp'] == 0:  # Skip options with no price
                continue
            
            option_key = self._get_option_key(option['strike'], option['type'])
            
            # Step 1: Check qualification (touched 90)
            is_qualified = self._check_qualification(option_key, option['ltp'])
            
            # Step 2: Monitor open position (if any)
            if self.open_position:
                self._monitor_position(option)
            
            # Step 3: Check entry trigger (only if no open position)
            if not self.open_position and is_qualified:
                if self._check_entry_trigger(option, option_key):
                    self._enter_position(option)
