# Email Configuration Guide

## Current Setup

The application is currently configured to use the **Console Email Backend** for development. This means emails are printed to the console/terminal instead of being actually sent.

## How to Verify Console Backend is Working

1. Start your Django development server: `python manage.py runserver`
2. Send an email through the application
3. Check your terminal/console where the server is running
4. You should see the email content printed there

## To Enable Actual Email Sending (SMTP)

To send real emails, you need to configure SMTP settings in `jobfinder2340/settings.py`:

### For Gmail:

1. Uncomment and update these lines in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use App Password, not regular password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

2. **Important for Gmail**: You need to use an **App Password**, not your regular password:
   - Go to your Google Account settings
   - Enable 2-Step Verification
   - Generate an App Password for "Mail"
   - Use that App Password in `EMAIL_HOST_PASSWORD`

### For Other Email Providers:

- **Outlook/Hotmail**: Use `smtp-mail.outlook.com` on port 587
- **Yahoo**: Use `smtp.mail.yahoo.com` on port 587
- **Custom SMTP**: Use your provider's SMTP server details

## Requirements for Email Sending

1. **Recruiter must have an email address** set in their user profile
2. **Candidate must have an email address** set in their user profile
3. **Candidate must allow contact** (privacy setting)

## Troubleshooting

- **"Email sent successfully" but no email received**: Check if console backend is active (emails print to terminal)
- **SMTP errors**: Verify your email credentials and SMTP settings
- **"Failed to send email"**: Check the error message and verify:
  - Email addresses are valid
  - SMTP credentials are correct
  - Firewall/network allows SMTP connections
  - For Gmail: App Password is used (not regular password)

