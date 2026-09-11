# Dárkomat

Cloudflare Python Worker + D1.

## Current auth flow

Registration now:

1. creates an unverified user;
2. creates a single-use email verification token valid for 24 hours;
3. sends a verification email through Resend;
4. requires the user to click the link before login is allowed.

Persistent login sessions are intentionally the next auth step.

## Email configuration

The application uses the Resend REST API. The Worker needs:

- `RESEND_API_KEY` — Cloudflare Secret
- `MAIL_FROM` — Worker variable containing the verified sender address
- `APP_URL` — Worker variable containing the public application URL

For the current Worker, `APP_URL` can be:

`https://darkomat-cloudflare.symeon-da9.workers.dev`

Do not commit the Resend API key.

Cloudflare dashboard:
Workers & Pages → darkomat-cloudflare → Settings → Variables and Secrets.

Add:

- Secret: `RESEND_API_KEY`
- Variable: `MAIL_FROM`
- Variable: `APP_URL`

For production email delivery to arbitrary recipients, verify your sending domain in Resend and use an address from that verified domain.

The code sends through `POST https://api.resend.com/emails` and includes a `User-Agent`, as required by Resend's API.

## D1 migration

Apply `migrations/0003_email_verification.sql` to the existing D1 database before testing registration.

The migration adds `users.email_verified_at` and the `email_verification_tokens` table.

## Project structure

- `src/entry.py` — routes and application flow
- `src/auth.py` — password and verification-token primitives
- `src/mailer.py` — reusable email transport
- `src/email_templates.py` — email content
- `src/templates.py` — web HTML templates/layout
- `src/i18n/` — English and Czech translations
- `public/` — CSS and browser JavaScript
- `migrations/` — D1 schema changes
