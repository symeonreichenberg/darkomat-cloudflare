from workers import Response, WorkerEntrypoint
from auth import hash_password


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = request.url

        if url.endswith("/api/health"):
            return Response.json({
                "ok": True,
                "app": "darkomat",
                "version": "2.0",
                "language": "python",
                "database": "connected",
            })

        if url.endswith("/api/db-test"):
            result = await self.env.DB.prepare(
                "SELECT COUNT(*) AS count FROM users"
            ).first()
            return Response.json({"ok": True, "database": result})

        if request.method == "POST" and url.endswith("/api/register"):
            data = await request.json()
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")

            if not name or not email or not password:
                return Response.json({
                    "ok": False,
                    "error": "Name, email and password are required",
                }, status=400)

            if len(password) < 8:
                return Response.json({
                    "ok": False,
                    "error": "Password must be at least 8 characters",
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
                    "error": "Could not create user",
                }, status=400)

        return Response(
            "Not found",
            status=404,
            headers={"content-type": "text/plain; charset=UTF-8"},
        )
