from SmartApi import SmartConnect
import pyotp
from datetime import datetime
import time

class AngelOneAPI:
    """Angel One SmartAPI integration for fetching Nifty options data"""
    
    def __init__(self, api_key, client_id, password, totp_secret):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.smart_api = None
        self.auth_token = None
        self.feed_token = None
        
        # Login to Angel One
        self._login()
    
    def _generate_totp(self):
        """Generate TOTP for login"""
        try:
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except Exception as e:
            print(f"Error generating TOTP: {str(e)}")
            return None
    
    def _login(self):
        """Login to Angel One SmartAPI"""
        try:
            print("Logging into Angel One...")
            
            # Initialize SmartAPI
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP
            totp = self._generate_totp()
            if not totp:
                print("❌ Failed to generate TOTP")
                return False
            
            # Login
            data = self.smart_api.generateSession(
                clientCode=self.client_id,
                password=self.password,
                totp=totp
            )
            
            if data['status']:
                self.auth_token = data['data']['jwtToken']
                self.feed_token = data['data']['feedToken']
                print("✓ Angel One login successful")
                print(f"✓ Client: {self.client_id}")
                return True
            else:
                print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def get_nifty_spot_price(self):
        """Get current Nifty 50 spot price"""
        try:
            # Nifty 50 token for NSE
            nifty_token = "99926000"  # NSE Nifty 50 token
            
            ltp_data = self.smart_api.ltpData(
                exchange="NSE",
                tradingsymbol="NIFTY 50",
                symboltoken=nifty_token
            )
            
            if ltp_data and ltp_data['status']:
                spot_price = float(ltp_data['data']['ltp'])
                print(f"✓ Nifty Spot: ₹{spot_price:.2f}")
                return spot_price
            else:
                print("⚠ Could not fetch Nifty spot price")
                return None
                
        except Exception as e:
            print(f"Error fetching Nifty spot: {str(e)}")
            return None
    
    def get_atm_strike(self, spot_price):
        """Calculate ATM strike (rounded to nearest 50)"""
        return round(spot_price / 50) * 50
    
    def _get_option_symbol(self, strike, option_type, expiry_date):
        """
        Generate option symbol for Angel One
        Format: NIFTY23JAN26C23500 or NIFTY23JAN26P23500
        """
        # Convert expiry date format: "23-Jan-2026" to "23JAN26"
        try:
            date_obj = datetime.strptime(expiry_date, "%d-%b-%Y")
            expiry_str = date_obj.strftime("%d%b%y").upper()
            
            symbol = f"NIFTY{expiry_str}{option_type[0]}{strike}"
            return symbol
        except Exception as e:
            print(f"Error generating symbol: {str(e)}")
            return None
    
    def get_weekly_expiry(self):
        """Get nearest weekly expiry for Nifty"""
        # You can hardcode this or fetch from Angel One
        # For now, let's use a simple logic
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        # Nifty weekly expiry is on Thursday
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0 and today.hour >= 15:
            days_until_thursday = 7
        
        expiry_date = today + timedelta(days=days_until_thursday)
        expiry_str = expiry_date.strftime("%d-%b-%Y")
        
        print(f"✓ Weekly Expiry: {expiry_str}")
        return expiry_str
    
    def get_option_chain(self):
        """Fetch option chain data for Nifty weekly options (ATM ± 5 strikes)"""
        try:
            # Get Nifty spot price
            spot_price = self.get_nifty_spot_price()
            if not spot_price:
                return None
            
            # Calculate ATM strike
            atm_strike = self.get_atm_strike(spot_price)
            print(f"✓ ATM Strike: {atm_strike}")
            
            # Get weekly expiry
            weekly_expiry = self.get_weekly_expiry()
            
            # Get strikes to scan (ATM ± 5)
            strikes_to_scan = [atm_strike + (i * 50) for i in range(-5, 6)]
            
            # Fetch option prices
            options = []
            
            for strike in strikes_to_scan:
                # Call option
                ce_symbol = self._get_option_symbol(strike, "CE", weekly_expiry)
                if ce_symbol:
                    try:
                        # Search for token
                        search_result = self.smart_api.searchScrip("NFO", ce_symbol)
                        
                        if search_result and search_result['status'] and search_result['data']:
                            token = search_result['data'][0]['symboltoken']
                            
                            # Get LTP
                            ltp_data = self.smart_api.ltpData(
                                exchange="NFO",
                                tradingsymbol=ce_symbol,
                                symboltoken=token
                            )
                            
                            if ltp_data and ltp_data['status']:
                                ltp = float(ltp_data['data']['ltp'])
                                if ltp > 0:
                                    options.append({
                                        'strike': strike,
                                        'type': 'CE',
                                        'ltp': ltp,
                                        'volume': 0,  # Angel One doesn't provide volume in LTP
                                        'oi': 0,
                                        'expiry': weekly_expiry,
                                        'symbol': ce_symbol
                                    })
                    except Exception as e:
                        print(f"⚠ Error fetching {ce_symbol}: {str(e)}")
                
                # Put option
                pe_symbol = self._get_option_symbol(strike, "PE", weekly_expiry)
                if pe_symbol:
                    try:
                        search_result = self.smart_api.searchScrip("NFO", pe_symbol)
                        
                        if search_result and search_result['status'] and search_result['data']:
                            token = search_result['data'][0]['symboltoken']
                            
                            ltp_data = self.smart_api.ltpData(
                                exchange="NFO",
                                tradingsymbol=pe_symbol,
                                symboltoken=token
                            )
                            
                            if ltp_data and ltp_data['status']:
                                ltp = float(ltp_data['data']['ltp'])
                                if ltp > 0:
                                    options.append({
                                        'strike': strike,
                                        'type': 'PE',
                                        'ltp': ltp,
                                        'volume': 0,
                                        'oi': 0,
                                        'expiry': weekly_expiry,
                                        'symbol': pe_symbol
                                    })
                    except Exception as e:
                        print(f"⚠ Error fetching {pe_symbol}: {str(e)}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
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
                print("⚠ No option data found")
                return None
                
        except Exception as e:
            print(f"❌ Error in get_option_chain: {str(e)}")
            return None
