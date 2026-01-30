# 📱 MPT-CRM Mobile Card Scanner

Scan business cards directly from your phone into your CRM!

## 🚀 Quick Start

### 1. Install Flask (if needed)
```bash
pip install flask
```

### 2. Start the Mobile Scanner Server

**Option A: Double-click the batch file**
- Double-click `start_mobile_scanner.bat`

**Option B: Run manually**
```bash
python mobile_scanner.py
```

### 3. Get Your Computer's IP Address

The startup script will show your IP address, or run:
```bash
ipconfig
```

Look for **IPv4 Address** (something like `192.168.1.100`)

### 4. Access from Your Phone

**Make sure your phone is on the same WiFi network as your computer!**

1. Open your phone's browser (Safari, Chrome, etc.)
2. Go to: `http://YOUR-IP-ADDRESS:5000`
   - Example: `http://192.168.1.100:5000`
3. Bookmark it for quick access!

## 📸 How to Use

1. **Tap "Start Camera"** - Allow camera access when prompted
2. **Position business card** - Fill the camera view
3. **Tap "Capture Card"** - AI extracts contact info instantly
4. **Review & edit** - Verify extracted data
5. **Tap "Import to CRM"** - Contact saved!
6. **Scan another** - Repeat for next card

## ✨ Features

- ✅ Native camera access on phone
- ✅ Instant AI contact extraction
- ✅ Quick review and edit
- ✅ Auto-enrollment in drip campaigns
- ✅ Works offline (processes on your computer)
- ✅ No app installation needed
- ✅ iPhone & Android compatible

## 🔧 Troubleshooting

### Can't access from phone?

1. **Check WiFi** - Phone and computer must be on same network
2. **Check firewall** - Allow port 5000 in Windows Firewall
3. **Try HTTPS** - Some phones require secure connection

### Camera not working?

1. **Allow permissions** - Grant camera access when prompted
2. **Use HTTPS** - Modern browsers require secure connection for camera
3. **Try different browser** - Safari/Chrome work best

### To enable HTTPS (optional):

The mobile scanner works with HTTP on local network, but for production use HTTPS.

## 🎯 Best Practices

- **At networking events**: Scan cards immediately while chatting
- **Add event name**: Makes follow-up emails more personal
- **Review accuracy**: AI is 90%+ accurate but double-check emails
- **Enroll wisely**: Uncheck campaign if not appropriate

## 🔐 Security

- Runs locally on your network
- No data sent to external servers (except Claude API for OCR)
- Same security as main CRM
- Uses your existing .env credentials

## 📊 Integration

The mobile scanner saves directly to your Supabase database:
- Creates contacts in `contacts` table
- Enrolls in `campaign_enrollments` table
- Same data as main CRM
- Instantly visible in Streamlit app

## 🌐 Making it Accessible from Anywhere (Advanced)

To access from outside your local network:

1. **Use ngrok** (easiest):
   ```bash
   ngrok http 5000
   ```
   Use the provided ngrok URL on your phone

2. **Port forwarding** (more permanent):
   - Configure router to forward port 5000
   - Use your public IP address
   - Consider security implications

3. **Cloud deployment**:
   - Deploy to Heroku, Railway, or similar
   - Add SSL certificate
   - Always accessible

## 💡 Tips

- Bookmark the URL on your phone home screen
- Works best with good lighting
- Hold card flat against contrasting background
- Clean camera lens for best OCR accuracy

---

**Need help?** Check the main CRM documentation or contact support.
