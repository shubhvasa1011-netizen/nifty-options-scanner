# 🔧 Angel One Setup Guide

Complete step-by-step guide to set up Nifty Options Scanner with Angel One API.

---

## **Step 1: Get Angel One API Credentials**

### **A) Create API App**

1. Login to Angel One SmartAPI portal: https://smartapi.angelbroking.com/
2. Click on **"My Profile"** → **"My API"**
3. Click **"Create App"**
4. Fill in details:
   - **App Name**: Nifty Scanner
   - **Redirect URL**: http://localhost (or any URL)
5. Click **"Create"**

You'll receive:
- **API Key** (e.g., `aBcD1234`)
- Save this API Key

### **B) Enable TOTP (Time-based OTP)**

1. In the same API section, find **"TOTP"** or **"2FA"** settings
2. Click **"Enable TOTP"**
3. You'll get a **TOTP Secret Key** (long string of characters)
4. **IMPORTANT**: Save this secret key - you'll need it for auto-login

### **C) Note Your Login Details**

You need:
- **Client ID**: Your Angel One client ID (e.g., A123456)
- **Password**: Your Angel One login password
- **MPIN**: Your 4-digit MPIN (if required)

---

## **Step 2: Install Required Libraries**

Open Command Prompt in your scanner folder and run:

```bash
pip install smartapi-python pyotp pytz requests
```

---

## **Step 3: Download New Files**

1. Download these new files from GitHub:
   - `angel_api.py`
   - `main_angel.py`
   
2. Place them in your scanner folder alongside existing files

---

## **Step 4: Set Environment Variables**

### **Method 1: Using Command Prompt (Each Time)**

Every time you run the scanner, set these variables:

```bash
set ANGEL_API_KEY=your_api_key_here
set ANGEL_CLIENT_ID=your_client_id_here
set ANGEL_PASSWORD=your_password_here
set ANGEL_TOTP_SECRET=your_totp_secret_here
set TELEGRAM_BOT_TOKEN=8516916749:AAETCiJvG7AlXV7DSzQ_2GpM3PtAc1zT_bE
set TELEGRAM_CHAT_ID=2028900350
```

### **Method 2: Create Config File (Recommended)**

Create a file named `config_angel.bat` in your scanner folder:

```batch
@echo off
set ANGEL_API_KEY=your_api_key_here
set ANGEL_CLIENT_ID=your_client_id_here
set ANGEL_PASSWORD=your_password_here
set ANGEL_TOTP_SECRET=your_totp_secret_here
set TELEGRAM_BOT_TOKEN=8516916749:AAETCiJvG7AlXV7DSzQ_2GpM3PtAc1zT_bE
set TELEGRAM_CHAT_ID=2028900350

python main_angel.py
pause
```

Replace the placeholder values with your actual credentials.

Then just double-click `config_angel.bat` to run!

---

## **Step 5: Run the Scanner**

### **If using Method 1:**
```bash
python main_angel.py
```

### **If using Method 2:**
Just double-click `config_angel.bat`

---

## **✅ What You Should See:**

```
🚀 Nifty Options Scanner Started (Angel One)
📱 Telegram Bot: Connected
⏰ Trading Hours: 9:30 AM - 3:00 PM IST
🔍 Scan Interval: 60 seconds
--------------------------------------------------
Logging into Angel One...
✓ Angel One login successful
✓ Client: A123456

[XX:XX:XX] Scanning options...
✓ Nifty Spot: ₹23,456.78
✓ ATM Strike: 23450
✓ Weekly Expiry: 23-Jan-2026
✓ Fetched 20 options successfully
```

And on Telegram:
```
✅ Nifty Options Scanner is now LIVE! (Angel One)

📊 Monitoring ATM ± 5 strikes
⏰ Active during market hours (9:30 AM - 3:00 PM)
```

---

## **🔒 Security Notes:**

1. **Never share your API credentials** with anyone
2. **Don't commit config files** to GitHub
3. **Use strong passwords**
4. **Enable 2FA** on your Angel One account

---

## **⚠️ Troubleshooting:**

### **"Login failed" error:**
- Check your Client ID, Password, and TOTP Secret
- Make sure TOTP is enabled in Angel One portal
- Try logging in manually to Angel One web/app first

### **"Invalid TOTP" error:**
- Check your TOTP Secret is correct
- Make sure your system time is accurate

### **"API Key invalid" error:**
- Verify your API Key from Angel One portal
- Make sure the app is active (not suspended)

---

## **📊 Advantages of Angel One:**

✅ **Reliable**: Official broker API, no blocking
✅ **Fast**: Real-time data with minimal delay
✅ **Accurate**: Direct from exchange
✅ **Free**: No additional charges for API usage
✅ **Stable**: No session expiry issues

---

## **🎯 Next Steps:**

Once the scanner is working:
1. Test during market hours
2. Verify signals are accurate
3. Consider adding auto-trading (if needed)
4. Set up auto-start on boot (optional)

---

**Need help? Check the main README.md or raise an issue on GitHub!**
