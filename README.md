# Dárkomat

Functional MVP on Cloudflare Workers + D1.

## Current pages

- `/` landing page
- `/register` registration
- `/login` login
- `/app` dashboard
- `/groups/new` create family
- `/groups/<id>` family: members, occasions, wishes and reservations
- `/account` account
- logout

Email verification is intentionally disabled for this MVP. Existing D1 email-verification columns/tables may remain in the database; they are simply unused.

## Deploy

Cloudflare Workers Builds runs the configured deploy command on push to `main`.
