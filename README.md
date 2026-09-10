# Dárkomat 2.0

Nová verze Dárkomatu postavená na Cloudflare Workers + Python + D1.

## Aktuální stav

- minimální Python Worker
- `/api/health`
- první návrh D1 schématu
- D1 zatím není připojená

## Cloudflare Workers Builds

Production deploy command:

```text
uv run pywrangler deploy
```

Python Workers používají `pywrangler` pro lokální vývoj a deployment.

## Další kroky

1. první deploy
2. vytvořit D1 databázi
3. přidat D1 binding
4. první SQL dotaz z Pythonu
5. registrace a přihlášení
6. skupiny
7. dárky
8. rezervace
9. pozvánky
10. e-mail přes Resend
