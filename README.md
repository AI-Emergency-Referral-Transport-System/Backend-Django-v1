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

## Notes

- AI flows are placeholders only.
- JWT settings are wired, but OTP-to-token issuance should be completed by the team.
- The structure is split by app ownership to reduce merge conflicts during parallel development.
