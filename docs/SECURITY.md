# Security Guidelines

## Admin Authentication
- **🔒 Environment Variable Password**: Admin password is stored securely as `ADMIN_PASSWORD` environment variable
- **🚫 No Hardcoded Passwords**: Passwords are never stored in source code
- **🎨 Secure Login Interface**: Modern, clean admin login page with proper form handling
- **⚠️ Production Warning**: Always use strong passwords in production environments

## Environment Variables
- ✅ All secrets moved to `.env` files
- ✅ `.env` files are git-ignored
- ✅ Strong Flask secret key implemented
- ✅ Debug mode controlled by environment variable
- ✅ Admin password secured via `ADMIN_PASSWORD` environment variable

## Setting Up Admin Access
```bash
# Set admin password (required)
export ADMIN_PASSWORD="your_secure_password_here"

# Start the application
cd webapp
python app.py
```

**Important**: Never commit passwords to version control. Always use environment variables.

## Production Deployment Checklist
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Use a production WSGI server (not Flask dev server)
- [ ] Rotate Spotify API credentials periodically
- [ ] Set up HTTPS for production
- [ ] Consider rate limiting for admin endpoints
- [ ] Monitor for failed authentication attempts

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
