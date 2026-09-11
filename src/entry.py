from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from auth import (
    hash_password,
    verify_password,
    generate_verification_token,
    hash_verification_token,
)
from mailer import send_email
from email_templates import verification_email
from i18n import get_language, t
from templates import (
    auth_page,
    home_page,
    message_page,
    not_found_page,
)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path
        language = get_language(request)

        if request.method == "GET":
            if path == "/":
                return self.html(home_page(language))

            if path == "/login":
                return self.html(auth_page(language, "login"))

            if path == "/register":
                query = parse_qs(url.query)
                pending = query.get("sent", [""])[0] == "1"
                return self.html(auth_page(language, "register", pending=pending))

            if path == "/verify-email":
                token = parse_qs(url.query).get("token", [""])[0]
                return await self.verify_email(token, language)

            if path == "/api/health":
                return Response.json({
                    "ok": True,
                    "app": "darkomat",
                    "version": "2.1",
                    "language": "python",
                    "database": "connected",
                })

            if path == "/api/db-test":
                result = await self.env.DB.prepare(
                    "SELECT COUNT(*) AS count FROM users"
                ).first()
                return Response.json({"ok": True, "database": result})

            return self.html(not_found_page(language), status=404)

        if request.method == "POST":
            if path == "/api/register":
                return await self.register(request, language)

            if path == "/api/login":
                return await self.login(request, language)

        return Response("Not found", status=404)

    def html(self, content: str, status: int = 200):
        return Response(
            content,
            status=status,
            headers={"content-type": "text/html; charset=UTF-8"},
        )

    async def register(self, request, language):
        try:
            data = await request.json()
        except Exception:
            return Response.json({
                "ok": False,
                "error": "invalid_request",
                "message": t("auth.invalid_request", language),
            }, status=400)

        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not name or not email or not password:
            return Response.json({
                "ok": False,
                "error": "required",
                "message": t("auth.required", language),
            }, status=400)

        if len(name) > 100:
            return Response.json({
                "ok": False,
                "error": "name_too_long",
                "message": t("auth.name_too_long", language),
            }, status=400)

        if "@" not in email or len(email) > 254:
            return Response.json({
                "ok": False,
                "error": "invalid_email",
                "message": t("auth.invalid_email", language),
            }, status=400)

        if len(password) < 8:
            return Response.json({
                "ok": False,
                "error": "password_short",
                "message": t("auth.password_short", language),
            }, status=400)

        existing = await self.env.DB.prepare(
            "SELECT id FROM users WHERE email = ?"
        ).bind(email).first()

        if existing:
            return Response.json({
                "ok": False,
                "error": "email_exists",
                "message": t("auth.email_exists", language),
            }, status=409)

        password_hash = await hash_password(password)
        verification_token = generate_verification_token()
        token_hash = hash_verification_token(verification_token)

        user = None

        try:
            user = await self.env.DB.prepare(
                "INSERT INTO users "
                "(name, email, password_hash) "
                "VALUES (?, ?, ?) "
                "RETURNING id, name, email"
            ).bind(name, email, password_hash).first()

            await self.env.DB.prepare(
                "INSERT INTO email_verification_tokens "
                "(user_id, token_hash, expires_at) "
                "VALUES (?, ?, datetime('now', '+24 hours'))"
            ).bind(user["id"], token_hash).run()

            email_data = verification_email(
                name=name,
                verification_url=(
                    f"{self.env.APP_URL.rstrip('/')}"
                    f"/verify-email?token={verification_token}"
                ),
                language=language,
            )

            await send_email(
                self.env,
                to=email,
                subject=email_data["subject"],
                html=email_data["html"],
                text=email_data["text"],
                tag="email_verification",
            )

            return Response.json({
                "ok": True,
                "redirect": "/register?sent=1",
            }, status=201)

        except Exception:
            # Registration is not considered complete if the verification
            # email could not be created/sent.
            if user:
                try:
                    await self.env.DB.prepare(
                        "DELETE FROM users WHERE id = ?"
                    ).bind(user["id"]).run()
                except Exception:
                    pass

            return Response.json({
                "ok": False,
                "error": "register_failed",
                "message": t("auth.register_failed", language),
            }, status=500)

    async def verify_email(self, token, language):
        if not token:
            return self.html(
                message_page(
                    language,
                    "auth.verify_failed_title",
                    "auth.verify_failed_text",
                    "auth.login_link",
                    "/login",
                ),
                status=400,
            )

        token_hash = hash_verification_token(token)

        record = await self.env.DB.prepare(
            "SELECT user_id "
            "FROM email_verification_tokens "
            "WHERE token_hash = ? "
            "AND used_at IS NULL "
            "AND expires_at > CURRENT_TIMESTAMP"
        ).bind(token_hash).first()

        if not record:
            return self.html(
                message_page(
                    language,
                    "auth.verify_failed_title",
                    "auth.verify_failed_text",
                    "auth.login_link",
                    "/login",
                ),
                status=400,
            )

        await self.env.DB.prepare(
            "UPDATE users "
            "SET email_verified_at = CURRENT_TIMESTAMP "
            "WHERE id = ?"
        ).bind(record["user_id"]).run()

        await self.env.DB.prepare(
            "UPDATE email_verification_tokens "
            "SET used_at = CURRENT_TIMESTAMP "
            "WHERE token_hash = ?"
        ).bind(token_hash).run()

        return self.html(
            message_page(
                language,
                "auth.verify_success_title",
                "auth.verify_success_text",
                "auth.login_link",
                "/login",
            )
        )

    async def login(self, request, language):
        try:
            data = await request.json()
        except Exception:
            return Response.json({
                "ok": False,
                "error": "invalid_request",
                "message": t("auth.invalid_request", language),
            }, status=400)

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return Response.json({
                "ok": False,
                "error": "required",
                "message": t("auth.required", language),
            }, status=400)

        user = await self.env.DB.prepare(
            "SELECT id, name, email, password_hash, email_verified_at "
            "FROM users WHERE email = ?"
        ).bind(email).first()

        if not user or not await verify_password(
            password,
            user["password_hash"],
        ):
            return Response.json({
                "ok": False,
                "error": "login_failed",
                "message": t("auth.login_failed", language),
            }, status=401)

        if not user["email_verified_at"]:
            return Response.json({
                "ok": False,
                "error": "email_not_verified",
                "message": t("auth.email_not_verified", language),
            }, status=403)

        # Persistent sessions will be added in the next auth step.
        return Response.json({
            "ok": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
            },
        })
