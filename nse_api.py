from datetime import datetime
import time

try:
    from nsepython import *
    NSEPYTHON_AVAILABLE = True
    print("✓ Using nsepython library for data")
except ImportError:
    NSEPYTHON_AVAILABLE = False
    print("⚠ nsepython not available, using fallback method")
    import requests
    import json

class NSEOptionChain:
    """Fetches Nifty option chain data from NSE using nsepython library"""
    
    def __init__(self):
        self.use_nsepython = NSEPYTHON_AVAILABLE
        
        if not self.use_nsepython:
            print("⚠ Please install nsepython: pip install nsepython")
            print("⚠ Falling back to basic method (may not work)")
    
    def get_nifty_spot_price(self):
        """Get current Nifty spot price"""
        try:
            if self.use_nsepython:
                # Using nsepython library
                spot_price = nse_quote_ltp("NIFTY 50", "index")
                if spot_price and spot_price > 0:
                    print(f"✓ Nifty Spot: ₹{spot_price:.2f}")
                    return spot_price
            else:
                # Fallback method - use hardcoded approximate value
                # This is just for testing - not accurate for real trading
                print("⚠ Using approximate Nifty value (install nsepython for real data)")
                return 23500.0  # Approximate value
                
        except Exception as e:
            print(f"Error fetching Nifty spot: {str(e)}")
        
        return None
    
    def get_atm_strike(self, spot_price):
        """Calculate ATM strike (rounded to nearest 50)"""
        return round(spot_price / 50) * 50
    
    def get_option_chain(self):
        """Fetch option chain data for Nifty weekly options (ATM ± 5 strikes)"""
        try:
            # Get Nifty spot price
            spot_price = self.get_nifty_spot_price()
            if not spot_price:
                print("⚠ Could not fetch spot price")
                return None
            
            # Calculate ATM strike
            atm_strike = self.get_atm_strike(spot_price)
            print(f"✓ ATM Strike: {atm_strike}")
            
            if self.use_nsepython:
                # Using nsepython library to fetch option chain
                try:
                    # Fetch option chain data
                    print("Fetching option chain from NSE...")
                    option_chain_data = nse_optionchain_data("NIFTY")
                    
                    if not option_chain_data or 'records' not in option_chain_data:
                        print("⚠ No option chain data received")
                        return None
                    
                    # Get expiry dates
                    expiry_dates = option_chain_data.get('records', {}).get('expiryDates', [])
                    if not expiry_dates:
                        print("⚠ No expiry dates found")
                        return None
                    
                    # Use first expiry (nearest weekly)
                    weekly_expiry = expiry_dates[0]
                    print(f"✓ Weekly Expiry: {weekly_expiry}")
                    
                    # Get strikes to scan (ATM ± 5)
                    strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
                    
                    # Parse option data
                    options = []
                    records = option_chain_data.get('records', {}).get('data', [])
                    
                    for record in records:
                        try:
                            strike = record.get('strikePrice')
                            expiry = record.get('expiryDate')
                            
                            # Filter for weekly expiry and our strike range
                            if expiry == weekly_expiry and strike in strikes_to_scan:
                                # Call option
                                if 'CE' in record:
                                    ce_data = record['CE']
                                    ltp = ce_data.get('lastPrice', 0)
                                    if ltp > 0:
                                        options.append({
                                            'strike': strike,
                                            'type': 'CE',
                                            'ltp': ltp,
                                            'volume': ce_data.get('totalTradedVolume', 0),
                                            'oi': ce_data.get('openInterest', 0),
                                            'expiry': expiry
                                        })
                                
                                # Put option
                                if 'PE' in record:
                                    pe_data = record['PE']
                                    ltp = pe_data.get('lastPrice', 0)
                                    if ltp > 0:
                                        options.append({
                                            'strike': strike,
                                            'type': 'PE',
                                            'ltp': ltp,
                                            'volume': pe_data.get('totalTradedVolume', 0),
                                            'oi': pe_data.get('openInterest', 0),
                                            'expiry': expiry
                                        })
                        except Exception as e:
                            continue
                    
                    if len(options) > 0:
                        print(f"✓ Fetched {len(options)} options successfully")
                        return {
                            'spot_price': spot_price,
                            'atm_strike': atm_strike,
                            'expiry': weekly_expiry,
                            'options': options,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        print("⚠ No valid option data found")
                        return None
                        
                except Exception as e:
                    print(f"❌ Error fetching option chain: {str(e)}")
                    return None
            else:
                # Fallback - generate dummy data for testing
                print("⚠ Generating test data (install nsepython for real data)")
                return self._generate_test_data(spot_price, atm_strike)
                
        except Exception as e:
            print(f"❌ Error in get_option_chain: {str(e)}")
            return None
    
    def _generate_test_data(self, spot_price, atm_strike):
        """Generate test data when nsepython is not available"""
        import random
        
        print("⚠ WARNING: Using simulated data - NOT REAL MARKET DATA")
        print("⚠ Install nsepython for real trading: pip install nsepython")
        
        options = []
        strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
        
        for strike in strikes_to_scan:
            # Generate random prices for testing
            ce_price = random.uniform(50, 150)
            pe_price = random.uniform(50, 150)
            
            options.append({
                'strike': strike,
                'type': 'CE',
                'ltp': round(ce_price, 2),
                'volume': random.randint(1000, 50000),
                'oi': random.randint(10000, 100000),
                'expiry': '23-Jan-2026'
            })
            
            options.append({
                'strike': strike,
                'type': 'PE',
                'ltp': round(pe_price, 2),
                'volume': random.randint(1000, 50000),
                'oi': random.randint(10000, 100000),
                'expiry': '23-Jan-2026'
            })
        
        return {
            'spot_price': spot_price,
            'atm_strike': atm_strike,
            'expiry': '23-Jan-2026',
            'options': options,
            'timestamp': datetime.now().isoformat()
        }
