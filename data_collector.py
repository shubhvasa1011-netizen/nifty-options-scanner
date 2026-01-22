import os
import json
from datetime import datetime
import time
from angel_api import AngelOneAPI

class OptionsDataCollector:
    """
    Collect live options data and save to file for backtesting
    Run this during market hours to build your own historical database
    """
    
    def __init__(self, angel_api):
        self.angel = angel_api
        self.data_file = "options_historical_data.json"
        self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing historical data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.historical_data = json.load(f)
                print(f"✓ Loaded {len(self.historical_data)} existing records")
            else:
                self.historical_data = []
                print("✓ Starting fresh data collection")
        except Exception as e:
            print(f"⚠ Error loading data: {str(e)}")
            self.historical_data = []
    
    def collect_snapshot(self):
        """Collect current options data snapshot"""
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Collecting data...")
            
            # Get current option chain
            option_data = self.angel.get_option_chain()
            
            if option_data:
                # Add timestamp
                option_data['collected_at'] = datetime.now().isoformat()
                
                # Save to historical data
                self.historical_data.append(option_data)
                
                # Save to file
                with open(self.data_file, 'w') as f:
                    json.dump(self.historical_data, f, indent=2)
                
                print(f"✓ Saved snapshot with {len(option_data['options'])} options")
                print(f"✓ Total snapshots: {len(self.historical_data)}")
                
                return True
            else:
                print("⚠ Failed to collect data")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def run_collection(self, interval_seconds=60, duration_hours=6):
        """
        Run data collection for specified duration
        
        Args:
            interval_seconds: How often to collect (default 60 = 1 minute)
            duration_hours: How long to run (default 6 hours = full trading day)
        """
        print("\n" + "="*60)
        print("📊 OPTIONS DATA COLLECTOR")
        print("="*60)
        print(f"⏱️  Collection Interval: {interval_seconds} seconds")
        print(f"⏰ Duration: {duration_hours} hours")
        print(f"💾 Saving to: {self.data_file}")
        print("="*60 + "\n")
        
        start_time = datetime.now()
        end_time = start_time.replace(hour=15, minute=30)  # Market close
        
        snapshots_collected = 0
        
        try:
            while datetime.now() < end_time:
                if self.collect_snapshot():
                    snapshots_collected += 1
                
                print(f"⏳ Next collection in {interval_seconds} seconds...")
                print(f"📈 Snapshots today: {snapshots_collected}")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Collection stopped by user")
        
        print("\n" + "="*60)
        print("✅ DATA COLLECTION COMPLETED")
        print("="*60)
        print(f"📊 Total snapshots collected: {snapshots_collected}")
        print(f"💾 Data saved to: {self.data_file}")
        print("="*60 + "\n")


def main():
    """Run data collector"""
    
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
    
    # Initialize collector
    collector = OptionsDataCollector(angel)
    
    # Run collection (every 1 minute during market hours)
    collector.run_collection(
        interval_seconds=60,  # Collect every minute
        duration_hours=6      # Run for full trading day
    )


if __name__ == "__main__":
    main()
