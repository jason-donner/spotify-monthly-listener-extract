# Quick Start Guide

## Setting Up Admin Access

### Windows (PowerShell)
```powershell
# Set the admin password
$env:ADMIN_PASSWORD = "your_secure_password_here"

# Navigate to webapp directory
cd "c:\path\to\your\project\webapp"

# Start the application
python app.py
```

### Linux/Mac (Bash)
```bash
# Set the admin password
export ADMIN_PASSWORD="your_secure_password_here"

# Navigate to webapp directory
cd /path/to/your/project/webapp

# Start the application
python app.py
```

### Using a .env File (Recommended)
Create a `.env` file in the `webapp` directory:
```env
ADMIN_PASSWORD=your_secure_password_here
FLASK_DEBUG=false
FLASK_SECRET_KEY=your_secret_key_here
```

Then start the app:
```bash
cd webapp
python app.py
```

## First Time Setup

1. **Set Admin Password** (required)
   ```powershell
   $env:ADMIN_PASSWORD = "admin123"
   ```

2. **Start the Web App**
   ```powershell
   cd webapp
   python app.py
   ```

3. **Access Admin Panel**
   - Go to: http://127.0.0.1:5000/admin_login
   - Login with your password
   - Admin panel will be at: http://127.0.0.1:5000/admin/

4. **Test Scraping**
   - Click "Run Scraping" in the admin panel
   - Choose your options (headless recommended)
   - Monitor progress in real-time

## Common Issues

### "Failed to fetch" Error
- ✅ **Fixed**: Ensure `ADMIN_PASSWORD` environment variable is set
- ✅ **Fixed**: Admin routes now have proper authentication

### Admin Login Not Working
- Check that `ADMIN_PASSWORD` environment variable is set
- Restart the Flask app after setting the environment variable
- Check the console for "ADMIN_PASSWORD environment variable not set!" message

### Scraping Issues
- Ensure Chrome browser is installed and updated
- Try running with `--headless` flag first
- Check network connectivity to Spotify

## Security Notes

- **Never commit passwords to version control**
- Use strong passwords in production
- Consider using a `.env` file for easier management
- Rotate passwords regularly in production environments
