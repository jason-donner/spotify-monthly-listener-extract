# Security Guidelines

## Environment Variables
- ✅ All secrets moved to `.env` files
- ✅ `.env` files are git-ignored
- ✅ Strong Flask secret key implemented
- ✅ Debug mode controlled by environment variable

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
