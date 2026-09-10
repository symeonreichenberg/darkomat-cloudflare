from workers import Response, WorkerEntrypoint

HTML = """<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dárkomat 2.0</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 760px; margin: 0 auto; padding: 40px 20px; line-height: 1.5; }
.card { border: 1px solid #ddd; border-radius: 14px; padding: 24px; margin-top: 24px; }
code { background: #f2f2f2; padding: 2px 6px; border-radius: 6px; }
</style>
</head>
<body>
<h1>🎁 Dárkomat 2.0</h1>
<p>Nový Dárkomat běží na Cloudflare Workers a Pythonu.</p>
<div class="card">
<h2>První krok je hotový</h2>
<p>Backend je napsaný v Pythonu. Dalším krokem bude připojení databáze D1.</p>
<p>Stav API: <a href="/api/health"><code>/api/health</code></a></p>
</div>
</body>
</html>"""

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.url.endswith("/api/health"):
            return Response.json({
                "ok": True,
                "app": "darkomat",
                "version": "2.0",
                "language": "python",
                "database": "not-connected-yet",
            })

        return Response(
            HTML,
            headers={"content-type": "text/html; charset=UTF-8"},
        )
