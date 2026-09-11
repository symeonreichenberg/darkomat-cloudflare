# Dárkomat Cloudflare

Current foundation:

- Python Worker + D1
- server-rendered HTML templates
- English default + Czech translations
- registration with password hashing
- email verification
- login sessions with HttpOnly/Secure cookie
- logout
- Resend mailer abstraction

## Cloudflare variables

Set these on the Worker:

- `APP_URL` — the workers.dev URL
- `RESEND_API_KEY` — Secret
- `MAIL_FROM` — Variable

For development, Resend documents `onboarding@resend.dev` as a test sender. Sending to arbitrary real recipients is subject to Resend's current testing/domain rules; use a verified domain for production sending.

## D1

Apply migrations in order. The new migration is:

`migrations/0003_email_verification.sql`

It adds:

- `users.email_verified_at`
- `email_verification_tokens`

`0002_sessions.sql` is required for login sessions.
