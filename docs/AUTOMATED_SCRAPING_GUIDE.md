# Automated Daily Scraping Setup Guide

Your Spotify Monthly Listener Extract app now supports automated daily scraping! Here are the different ways to set it up:

## 🚀 Option 1: Built-in Python Scheduler (Recommended)

### What's Included:
- **Built-in scheduler** that runs within your Flask app
- **Admin panel controls** to set the daily time
- **Automatic startup** when the app starts
- **Status monitoring** and manual trigger options

### Setup:
1. **Install the schedule library:**
   ```bash
   cd webapp
   pip install -r requirements.txt
   ```

2. **Start your Flask app:**
   ```bash
   python app.py
   ```

3. **Configure the schedule:**
   - Go to the Admin Panel
   - Find the "Automated Daily Scraping" section
   - Set your preferred time (e.g., 2:00 AM)
   - Click "Update Schedule"

### Features:
- ✅ **Visual admin controls** for schedule management
- ✅ **Status monitoring** shows next run time
- ✅ **Manual trigger** for immediate full scraping
- ✅ **Automatic startup** when app restarts
- ✅ **Headless mode** for unattended operation
- ✅ **Duplicate protection** prevents re-scraping same day

---

## 🖥️ Option 2: System Cron Job (Linux/Mac)

For production servers, you might prefer using system cron:

### Setup:
1. **Create a daily script:**
   ```bash
   # Create script file
   nano /home/user/daily_scrape.sh
   ```

2. **Add this content:**
   ```bash
   #!/bin/bash
   cd /path/to/your/Spotify\ Monthly\ Listener\ Extract/scraping
   python scrape.py --headless --no-prompt
   ```

3. **Make executable:**
   ```bash
   chmod +x /home/user/daily_scrape.sh
   ```

4. **Add to cron:**
   ```bash
   crontab -e
   # Add this line for 2 AM daily:
   0 2 * * * /home/user/daily_scrape.sh
   ```

---

## 🪟 Option 3: Windows Task Scheduler

For Windows servers:

### Setup:
1. **Open Task Scheduler**
2. **Create Basic Task**
3. **Set trigger:** Daily at 2:00 AM
4. **Action:** Start a program
5. **Program:** `python`
6. **Arguments:** `scrape.py --headless --no-prompt`
7. **Start in:** `C:\path\to\scraping\folder`

---

## ☁️ Option 4: Cloud Hosting Solutions

### Heroku:
- Use **Heroku Scheduler** add-on
- Command: `python scraping/scrape.py --headless --no-prompt`

### Railway/Render:
- Use built-in cron job features
- Schedule daily Python script execution

### AWS/GCP:
- Use **CloudWatch Events** or **Cloud Scheduler**
- Trigger Lambda/Cloud Function to run scraping

---

## 🔧 Configuration Tips

### Recommended Schedule Times:
- **2:00 AM - 4:00 AM** (low traffic, stable data)
- **Avoid peak hours** (9 AM - 11 PM)

### Environment Setup:
Make sure these are configured:
```bash
# Required environment variables
CHROMEDRIVER_PATH=/path/to/chromedriver
ADMIN_PASSWORD=your-secure-password
```

### Login Requirements:
- **Manual runs:** Require Spotify login in browser
- **Automated runs:** Need persistent login session or API integration

---

## 📊 Monitoring & Logs

### Built-in Monitoring:
- **Admin panel** shows scheduler status
- **Log files** in `webapp/logs/`
- **Job status** tracking for each run

### Log Locations:
- **App logs:** `webapp/logs/app.log`
- **Admin logs:** `webapp/logs/admin.log`
- **Scraping output:** Captured in job status

---

## 🛠️ Troubleshooting

### Common Issues:

1. **Chrome/ChromeDriver issues:**
   - Install latest Chrome and ChromeDriver
   - Set `CHROMEDRIVER_PATH` environment variable

2. **Login session expires:**
   - Consider implementing session persistence
   - Or use Spotify Web API for authentication

3. **Scheduler not running:**
   - Check admin panel status
   - Verify app is running continuously
   - Check logs for errors

### Support:
- Check the admin panel for real-time status
- Review log files for detailed error information
- Use "Run Full Scrape Now" for immediate testing

Your automated scraping system is now ready! 🎉
