import requests
import json
from datetime import datetime

class NSEOptionChain:
    """Fetches Nifty option chain data from NSE"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api/option-chain-indices"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Initialize session with NSE homepage
        try:
            self.session.get('https://www.nseindia.com', timeout=10)
        except:
            pass
    
    def get_nifty_spot_price(self):
        """Get current Nifty spot price"""
        try:
            url = "https://www.nseindia.com/api/allIndices"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for index in data.get('data', []):
                    if index.get('index') == 'NIFTY 50':
                        return float(index.get('last', 0))
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
        try:
            # Get Nifty spot price
            spot_price = self.get_nifty_spot_price()
            if not spot_price:
                return None
            
            # Fetch option chain
            url = f"{self.base_url}?symbol=NIFTY"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Get weekly expiry
            weekly_expiry = self.get_weekly_expiry(data)
            if not weekly_expiry:
                return None
            
            # Calculate ATM strike
            atm_strike = self.get_atm_strike(spot_price)
            
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
                        options.append({
                            'strike': strike,
                            'type': 'CE',
                            'ltp': ce_data.get('lastPrice', 0),
                            'volume': ce_data.get('totalTradedVolume', 0),
                            'oi': ce_data.get('openInterest', 0),
                            'expiry': expiry
                        })
                    
                    # Put option
                    if 'PE' in record:
                        pe_data = record['PE']
                        options.append({
                            'strike': strike,
                            'type': 'PE',
                            'ltp': pe_data.get('lastPrice', 0),
                            'volume': pe_data.get('totalTradedVolume', 0),
                            'oi': pe_data.get('openInterest', 0),
                            'expiry': expiry
                        })
            
            return {
                'spot_price': spot_price,
                'atm_strike': atm_strike,
                'expiry': weekly_expiry,
                'options': options,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error fetching option chain: {str(e)}")
            return None
