from workers import Response, WorkerEntrypoint
import hashlib
from js import crypto, TextEncoder, Object
from pyodide.ffi import to_js as _to_js

def to_js(value):
    return _to_js(value, dict_converter=Object.fromEntries)


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

        if request.url.endswith("/api/db-test"):
            result = await self.env.DB.prepare(
                "SELECT COUNT(*) AS count FROM users"
            ).first()

            return Response.json({
                "ok": True,
                "database": result,
            })

        if request.method == "POST" and request.url.endswith("/api/register"):
            data = await request.json()

            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()

            if not name or not email:
                return Response.json(
                    {
                        "ok": False,
                        "error": "Name and email are required",
                    },
                    status=400,
                )

            try:
                result = await self.env.DB.prepare(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (?, ?, ?)
                    RETURNING id, name, email
                    """
                ).bind(name, email, "TEMP").first()

                return Response.json(
                    {
                        "ok": True,
                        "user": result,
                    },
                    status=201,
                )

            except Exception:
                return Response.json(
                    {
                        "ok": False,
                        "error": "Could not create user",
                    },
                    status=400,
                )

        if request.url.endswith("/api/hash-test"):
            password = "tajne-heslo"

            hashed = hashlib.sha256(
                password.encode("utf-8")
            ).hexdigest()

            return Response.json({
                "ok": True,
                "hash": hashed,
            })

        if request.url.endswith("/api/argon2-test"):
            try:
                from argon2 import PasswordHasher
                argon2_available = True
            except ImportError:
                argon2_available = False

            return Response.json({
                "ok": True,
                "argon2_available": argon2_available,
            })

        if request.url.endswith("/api/crypto-test"):
            return Response.json({
                "ok": True,
                "crypto_available": str(crypto),
                "subtle_available": str(crypto.subtle),
            })

        if request.url.endswith("/api/ffi-test"):
            from js import Object

            return Response.json({
                "ok": True,
                "ffi_available": True,
                "object_type": str(Object),
            })

        if request.url.endswith("/api/pbkdf2-test"):
            password = "tajne-heslo"
            salt = b"test-salt"

            hashed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                600_000,
            ).hex()

            return Response.json({
                "ok": True,
                "algorithm": "PBKDF2-HMAC-SHA256",
                "iterations": 600_000,
                "hash": hashed,
            })

        return Response(
            HTML,
            headers={"content-type": "text/html; charset=UTF-8"},
        )