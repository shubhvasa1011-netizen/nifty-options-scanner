import requests
import json
from datetime import datetime
import time

class NSEOptionChain:
    """Fetches Nifty option chain data from NSE"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api/option-chain-indices"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.nseindia.com/option-chain',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.cookies_initialized = False
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session by visiting NSE homepage to get cookies"""
        try:
            print("Initializing NSE session...")
            # Visit homepage to get cookies
            response = self.session.get('https://www.nseindia.com', timeout=10)
            if response.status_code == 200:
                self.cookies_initialized = True
                print("✓ NSE session initialized successfully")
                time.sleep(1)  # Small delay after initialization
            else:
                print(f"⚠ NSE homepage returned status: {response.status_code}")
        except Exception as e:
            print(f"⚠ Error initializing NSE session: {str(e)}")
    
    def _refresh_session(self):
        """Refresh session if needed"""
        try:
            self.session = requests.Session()
            self.session.headers.update(self.headers)
            self._initialize_session()
        except Exception as e:
            print(f"Error refreshing session: {str(e)}")
    
    def get_nifty_spot_price(self):
        """Get current Nifty spot price"""
        try:
            if not self.cookies_initialized:
                self._initialize_session()
            
            url = "https://www.nseindia.com/api/allIndices"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for index in data.get('data', []):
                    if index.get('index') == 'NIFTY 50':
                        spot_price = float(index.get('last', 0))
                        print(f"✓ Nifty Spot: ₹{spot_price:.2f}")
                        return spot_price
            else:
                print(f"⚠ Failed to fetch Nifty spot. Status: {response.status_code}")
                
        except Exception as e:
            print(f"Error fetching Nifty spot: {str(e)}")
        
        return None
    
    def get_atm_strike(self, spot_price):
        """Calculate ATM strike (rounded to nearest 50)"""
        return round(spot_price / 50) * 50
    
    def get_weekly_expiry(self, data):
        """Get the nearest weekly expiry date"""
        try:
            expiry_dates = data.get('records', {}).get('expiryDates', [])
            if expiry_dates:
                return expiry_dates[0]  # First expiry is usually the nearest weekly
        except:
            pass
        return None
    
    def get_option_chain(self):
        """Fetch option chain data for Nifty weekly options (ATM ± 5 strikes)"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Ensure session is initialized
                if not self.cookies_initialized:
                    self._initialize_session()
                
                # Get Nifty spot price
                spot_price = self.get_nifty_spot_price()
                if not spot_price:
                    print("⚠ Could not fetch spot price, retrying...")
                    retry_count += 1
                    time.sleep(2)
                    continue
                
                # Small delay before fetching option chain
                time.sleep(1)
                
                # Fetch option chain
                url = f"{self.base_url}?symbol=NIFTY"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 401 or response.status_code == 403:
                    print("⚠ Session expired, refreshing...")
                    self._refresh_session()
                    retry_count += 1
                    time.sleep(2)
                    continue
                
                if response.status_code != 200:
                    print(f"⚠ NSE API returned status {response.status_code}, retrying...")
                    retry_count += 1
                    time.sleep(2)
                    continue
                
                data = response.json()
                
                # Get weekly expiry
                weekly_expiry = self.get_weekly_expiry(data)
                if not weekly_expiry:
                    print("⚠ Could not find weekly expiry")
                    retry_count += 1
                    time.sleep(2)
                    continue
                
                # Calculate ATM strike
                atm_strike = self.get_atm_strike(spot_price)
                print(f"✓ ATM Strike: {atm_strike}")
                
                # Get strikes to scan (ATM ± 5)
                strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
                
                # Parse option data
                options = []
                records = data.get('records', {}).get('data', [])
                
                for record in records:
                    strike = record.get('strikePrice')
                    expiry = record.get('expiryDate')
                    
                    # Filter for weekly expiry and our strike range
                    if expiry == weekly_expiry and strike in strikes_to_scan:
                        # Call option
                        if 'CE' in record:
                            ce_data = record['CE']
                            ltp = ce_data.get('lastPrice', 0)
                            if ltp > 0:  # Only add if price is available
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
                            if ltp > 0:  # Only add if price is available
                                options.append({
                                    'strike': strike,
                                    'type': 'PE',
                                    'ltp': ltp,
                                    'volume': pe_data.get('totalTradedVolume', 0),
                                    'oi': pe_data.get('openInterest', 0),
                                    'expiry': expiry
                                })
                
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
                    print("⚠ No option data found, retrying...")
                    retry_count += 1
                    time.sleep(2)
                    continue
                
            except requests.exceptions.Timeout:
                print(f"⚠ Request timeout (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(3)
            except requests.exceptions.ConnectionError:
                print(f"⚠ Connection error (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(3)
            except Exception as e:
                print(f"⚠ Error fetching option chain: {str(e)} (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(3)
        
        print("❌ Failed to fetch option chain after all retries")
        return None
