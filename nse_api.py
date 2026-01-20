import requests
import json
from datetime import datetime
import time
import random

class NSEOptionChain:
    """Fetches Nifty option chain data from NSE"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.session = None
        self._create_session()
    
    def _create_session(self):
        """Create a new session with proper headers"""
        self.session = requests.Session()
        
        # Randomize user agent to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self.headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        self.session.headers.update(self.headers)
        
        # Initialize cookies by visiting homepage
        try:
            print("Initializing NSE session...")
            response = self.session.get(f'{self.base_url}/', timeout=10)
            
            if response.status_code == 200:
                print("✓ NSE session initialized")
                time.sleep(2)  # Wait for cookies to settle
                return True
            else:
                print(f"⚠ NSE homepage returned: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠ Session init error: {str(e)}")
            return False
    
    def _make_request(self, url, max_retries=3):
        """Make HTTP request with retries"""
        for attempt in range(max_retries):
            try:
                # Update headers for API call
                api_headers = self.headers.copy()
                api_headers.update({
                    'Accept': '*/*',
                    'Referer': f'{self.base_url}/option-chain',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                })
                
                response = self.session.get(url, headers=api_headers, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code in [401, 403]:
                    print(f"⚠ Access denied (attempt {attempt + 1}/{max_retries}), refreshing session...")
                    self._create_session()
                    time.sleep(3)
                else:
                    print(f"⚠ Status {response.status_code} (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                    
            except requests.exceptions.Timeout:
                print(f"⚠ Timeout (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            except Exception as e:
                print(f"⚠ Request error: {str(e)} (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
        
        return None
    
    def get_nifty_spot_price(self):
        """Get current Nifty spot price"""
        try:
            url = f"{self.base_url}/api/allIndices"
            response = self._make_request(url)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    for index in data.get('data', []):
                        if index.get('index') == 'NIFTY 50':
                            spot_price = float(index.get('last', 0))
                            if spot_price > 0:
                                print(f"✓ Nifty Spot: ₹{spot_price:.2f}")
                                return spot_price
                except json.JSONDecodeError as e:
                    print(f"⚠ JSON decode error for spot price: {str(e)}")
                except Exception as e:
                    print(f"⚠ Error parsing spot price: {str(e)}")
                    
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
            if expiry_dates and len(expiry_dates) > 0:
                # First expiry is usually the nearest weekly
                return expiry_dates[0]
        except Exception as e:
            print(f"⚠ Error getting expiry: {str(e)}")
        return None
    
    def get_option_chain(self):
        """Fetch option chain data for Nifty weekly options (ATM ± 5 strikes)"""
        try:
            # Get Nifty spot price first
            spot_price = self.get_nifty_spot_price()
            if not spot_price:
                print("⚠ Could not fetch spot price")
                return None
            
            # Small delay between requests
            time.sleep(1)
            
            # Fetch option chain
            url = f"{self.base_url}/api/option-chain-indices?symbol=NIFTY"
            response = self._make_request(url)
            
            if not response or response.status_code != 200:
                print("⚠ Could not fetch option chain")
                return None
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"⚠ JSON decode error: {str(e)}")
                print(f"Response text: {response.text[:200]}")  # Print first 200 chars
                return None
            
            # Get weekly expiry
            weekly_expiry = self.get_weekly_expiry(data)
            if not weekly_expiry:
                print("⚠ Could not find weekly expiry")
                return None
            
            # Calculate ATM strike
            atm_strike = self.get_atm_strike(spot_price)
            print(f"✓ ATM Strike: {atm_strike}")
            print(f"✓ Weekly Expiry: {weekly_expiry}")
            
            # Get strikes to scan (ATM ± 5)
            strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
            
            # Parse option data
            options = []
            records = data.get('records', {}).get('data', [])
            
            if not records:
                print("⚠ No option records found")
                return None
            
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
                except Exception as e:
                    # Skip problematic records
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
            print(f"❌ Error in get_option_chain: {str(e)}")
            return None
