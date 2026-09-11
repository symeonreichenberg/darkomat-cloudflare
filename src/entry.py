from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from auth import hash_password, verify_password
from i18n import get_language
from templates import auth_page, home_page, not_found_page


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path
        language = get_language(request)

        if request.method == "GET":
            if path == "/":
                return Response(
                    home_page(language),
                    headers={"content-type": "text/html; charset=UTF-8"},
                )

            if path == "/login":
                return Response(
                    auth_page(language, "login"),
                    headers={"content-type": "text/html; charset=UTF-8"},
                )

            if path == "/register":
                return Response(
                    auth_page(language, "register"),
                    headers={"content-type": "text/html; charset=UTF-8"},
                )

            if path == "/api/health":
                return Response.json({
                    "ok": True,
                    "app": "darkomat",
                    "version": "2.0",
                    "language": "python",
                    "database": "connected",
                })

            if path == "/api/db-test":
                result = await self.env.DB.prepare(
                    "SELECT COUNT(*) AS count FROM users"
                ).first()
                return Response.json({"ok": True, "database": result})

            return Response(
                not_found_page(language),
                status=404,
                headers={"content-type": "text/html; charset=UTF-8"},
            )

        if request.method == "POST":
            if path == "/api/register":
                return await self.register(request)

            if path == "/api/login":
                return await self.login(request)

        return Response("Not found", status=404)


    async def register(self, request):
        data = await request.json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not name or not email or not password:
            return Response.json({
                "ok": False,
                "error": "required",
            }, status=400)

        if len(password) < 8:
            return Response.json({
                "ok": False,
                "error": "password_short",
            }, status=400)

        password_hash = await hash_password(password)

        try:
            result = await self.env.DB.prepare(
                "INSERT INTO users (name, email, password_hash) "
                "VALUES (?, ?, ?) RETURNING id, name, email"
            ).bind(name, email, password_hash).first()

            return Response.json(
                {"ok": True, "user": result},
                status=201,
            )
        except Exception:
            return Response.json({
                "ok": False,
                "error": "register_failed",
            }, status=400)


    async def login(self, request):
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return Response.json({
                "ok": False,
                "error": "required",
            }, status=400)

        user = await self.env.DB.prepare(
            "SELECT id, name, email, password_hash "
            "FROM users WHERE email = ?"
        ).bind(email).first()

        if not user or not await verify_password(
            password,
            user["password_hash"],
        ):
            return Response.json({
                "ok": False,
                "error": "login_failed",
            }, status=401)

        return Response.json({
            "ok": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
            },
        })
