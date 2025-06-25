# Security Guidelines

## Admin Authentication
- **🔒 .env File Password**: Admin password is stored securely in the `.env` file as `ADMIN_PASSWORD`
- **🚫 No Hardcoded Passwords**: Passwords are never stored in source code
- **🎨 Secure Login Interface**: Modern, clean admin login page with proper form handling
- **⚠️ Production Warning**: Always use strong passwords in production environments

## Environment Variables
- ✅ All secrets moved to `.env` files
- ✅ `.env` files are git-ignored
- ✅ Strong Flask secret key implemented
- ✅ Debug mode controlled by environment variable
- ✅ Admin password secured in `.env` file (no longer requires manual environment variables)

## Setting Up Admin Access

### Updated Method (Recommended)
Add your admin password directly to the `.env` file:

```env
# Add to webapp/.env file
ADMIN_PASSWORD=your_secure_password_here
```

Then start the application:
```bash
cd webapp
python app.py
# or use the batch file
start_app.bat
```

### Legacy Method (Deprecated)
**Note**: Manual environment variable setting is no longer required as the app now reads from `.env` file.

~~```bash
# Old method - no longer needed
export ADMIN_PASSWORD="your_secure_password_here"
```~~

**Important**: Never commit passwords to version control. The `.env` file is automatically git-ignored.

### Common Setup Issues
- **"Failed to fetch" Error**: Ensure `ADMIN_PASSWORD` is set in your `.env` file before starting the app
- **Admin Login Fails**: Check that the password in `.env` file matches what you're entering
- **Routes Not Accessible**: All admin routes now require proper authentication
- **App Won't Start**: Verify `.env` file exists in the webapp directory

## Production Deployment Checklist
- [ ] Set strong `ADMIN_PASSWORD` in production `.env` file
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Use a production WSGI server (not Flask dev server)
- [ ] Rotate Spotify API credentials periodically
- [ ] Set up HTTPS for production
- [ ] Consider rate limiting for admin endpoints
- [ ] Monitor for failed authentication attempts
- [ ] Secure `.env` file permissions (readable only by application user)

## File Permissions
- Ensure `.env` files have restricted permissions (600)
- Keep data directory secured from web access

## Regular Security Tasks
1. Update dependencies monthly: `pip install -U -r requirements.txt`
2. Review access logs for suspicious activity
3. Rotate Flask secret key annually
4. Monitor Spotify API usage for anomalies

## Contact
For security issues, contact the repository maintainer privately.
