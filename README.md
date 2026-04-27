# AI Emergency System Backend

Starter backend scaffold for a multi-actor emergency coordination platform built with Django, DRF, Channels, Redis, PostgreSQL, and GeoDjango.

## Apps

- `accounts`: custom users, roles, email OTP authentication, JWT entry points
- `emergencies`: emergency lifecycle scaffolding
- `hospitals`: hospital availability and capacity
- `ambulances`: ambulance registry and driver assignment
- `tracking`: geospatial tracking and WebSocket transport
- `ai`: AI messaging and RAG placeholders

## Quick start

1. Copy `.env.example` to `.env`.
2. Build and start services: `docker compose up --build`
3. Run migrations: `python manage.py migrate`
4. Create an admin user: `python manage.py createsuperuser`

## Email OTP Demo

This branch supports email-only OTP auth.

1. Start the server.
2. Open [http://127.0.0.1:8000/api/v1/auth/otp/request/](http://127.0.0.1:8000/api/v1/auth/otp/request/).
3. Submit:
```json
{"email":"test@gmail.com"}
```
4. Check the recipient inbox for the OTP email.
6. Open [http://127.0.0.1:8000/api/v1/auth/otp/verify/](http://127.0.0.1:8000/api/v1/auth/otp/verify/) and submit:
```json
{"email":"test@gmail.com","code":"123456"}
```
7. Replace `123456` with the real OTP from the email.

Before running the server, configure real SMTP credentials in `.env`:

```env
OTP_DELIVERY_BACKEND=email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

For Gmail, `EMAIL_HOST_PASSWORD` should be a Google App Password, not your normal account password.
