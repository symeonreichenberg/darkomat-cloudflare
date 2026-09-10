# Dárkomat 2.0

Nová verze Dárkomatu na Cloudflare Workers + Python.

## Aktuální stav
- jednoduchá webová stránka
- `/api/health`
- databáze D1 zatím není připojená

## Deploy
Cloudflare Workers Builds:
`npx wrangler deploy`

Python Workers jsou na Cloudflare aktuálně v open beta. D1 lze z Python Workeru používat přes binding.

## Plán
1. první Python Worker
2. D1
3. registrace a přihlášení
4. skupiny
5. dárky
6. rezervace
7. pozvánky
8. e-mail přes Resend
9. frontend
10. bezpečnost a produkční úklid
