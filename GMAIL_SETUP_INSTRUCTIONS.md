# Gmail SMTP Setup Instructions

## Why You Need This

The console email backend only prints emails to the terminal - it doesn't actually send them. To send real emails, you need to configure Gmail SMTP.

## Steps to Get Gmail App Password

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google", enable "2-Step Verification"
   - Follow the setup process

2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Or go to: Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" as the app
   - Select "Other (Custom name)" as the device, enter "JobFinder" or any name
   - Click "Generate"
   - **Copy the 16-character password** (it will look like: `abcd efgh ijkl mnop`)

3. **Add the App Password to settings.py**:
   - Open `jobfinder2340/settings.py`
   - Find the line: `EMAIL_HOST_PASSWORD = 'YOUR_APP_PASSWORD_HERE'`
   - Replace `YOUR_APP_PASSWORD_HERE` with your 16-character app password (remove spaces)
   - Example: `EMAIL_HOST_PASSWORD = 'abcdefghijklmnop'`

4. **Restart your Django server**:
   - Stop the server (Ctrl+C)
   - Start it again: `python manage.py runserver`

5. **Test sending an email** - it should now actually send to the recipient's inbox!

## Important Notes

- **Never commit your app password to git** - consider using environment variables for production
- The app password is different from your regular Gmail password
- If you change your Google password, you may need to generate a new app password
- App passwords are required because Gmail blocks "less secure apps" by default

## Alternative: Use Environment Variables (Recommended for Production)

Instead of hardcoding the password, you can use environment variables:

```python
import os

EMAIL_HOST_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
```

Then set the environment variable:
```bash
export GMAIL_APP_PASSWORD='your-app-password-here'
```

