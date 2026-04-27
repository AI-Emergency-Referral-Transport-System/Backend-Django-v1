# Accounts Module

This module handles email-based OTP authentication, JWT issuance, and profile management.

## Email Delivery

OTP emails are sent with Django's configured email backend.

For local development, the default console backend prints the email to the terminal.
For real delivery, configure:

- `EMAIL_BACKEND`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS` or `EMAIL_USE_SSL`

## OTP Endpoints

- `POST /api/v1/auth/otp/request/`
- `POST /api/v1/auth/otp/verify/`
- `POST /api/v1/auth/token/refresh/`
- `GET/PATCH /api/v1/auth/profile/`

## Real Email Test Flow

1. Install dependencies with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Set your email backend and SMTP credentials if you want real delivery.
4. Run `python manage.py migrate`.
5. Start the server with `python manage.py runserver`.
6. Request an OTP with `POST /api/v1/auth/otp/request/`.
7. Check the inbox for the OTP.
8. Verify it with `POST /api/v1/auth/otp/verify/`.

## Notes

- OTPs are hashed before storage.
- OTPs expire after 5 minutes.
- Unused older OTPs are invalidated when a new one is issued.
- The console email backend is useful for local testing.
