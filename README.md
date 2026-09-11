# Dárkomat — Cloudflare Worker

## Structure

- `src/` — Python Worker and reusable application code.
- `src/i18n/` — English and Czech translation dictionaries.
- `src/templates.py` — shared HTML layout and page components.
- `public/` — static browser assets such as CSS and JavaScript.
- `migrations/` — D1 schema migrations.

Pages currently implemented:

- `/` — homepage
- `/register` — registration form
- `/login` — login form
- unmatched paths — custom 404 page

API endpoints currently implemented:

- `GET /api/health`
- `GET /api/db-test`
- `POST /api/register`
- `POST /api/login`

Authentication sessions are intentionally not implemented yet. Login currently verifies credentials and returns a successful API response; the next backend step is a persistent session/cookie layer.
