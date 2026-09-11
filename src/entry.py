import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

from workers import Response, WorkerEntrypoint

from auth import hash_password, verify_password
from i18n import get_language, t
from templates import (
    account_page,
    auth_page,
    home_page,
    message_page,
    not_found_page,
)


SESSION_DAYS = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _cookie(name: str, value: str, max_age: int) -> str:
    return (
        f"{name}={value}; Path=/; Max-Age={max_age}; "
        "HttpOnly; Secure; SameSite=Lax"
    )


def _clear_cookie(name: str) -> str:
    return f"{name}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax"


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
                return self.html(auth_page(language, "register"))

            if path == "/verify-email":
                return await self.verify_email(request, language)

            if path == "/account":
                user = await self.current_user(request)
                if not user:
                    return Response.redirect(
                        self.absolute_url(request, "/login"),
                        status=302,
                    )
                return self.html(account_page(language, user))

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

            return self.html(not_found_page(language), status=404)

        if request.method == "POST":
            if path == "/register":
                return await self.register(request, language)

            if path == "/login":
                return await self.login(request, language)

            if path == "/logout":
                return await self.logout(request)

        return Response("Not found", status=404)

    def html(self, body: str, status: int = 200, headers=None):
        response_headers = {
            "content-type": "text/html; charset=UTF-8",
        }
        if headers:
            response_headers.update(headers)
        return Response(body, status=status, headers=response_headers)

    def absolute_url(self, request, path: str) -> str:
        return f"{urlparse(request.url).scheme}://{urlparse(request.url).netloc}{path}"

    async def form_data(self, request):
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" not in content_type:
            return {}

        body = await request.text()
        values = parse_qs(body, keep_blank_values=True)

        return {
            key: items[0] if items else ""
            for key, items in values.items()
        }

    async def register(self, request, language):
        data = await self.form_data(request)

        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not name or not email or not password:
            return Response.json({"ok": False, "error": "required"}, status=400)

        if len(name) > 100:
            return Response.json({"ok": False, "error": "name_too_long"}, status=400)

        if "@" not in email or len(email) > 254:
            return Response.json({"ok": False, "error": "invalid_email"}, status=400)

        if len(password) < 8:
            return Response.json({"ok": False, "error": "password_short"}, status=400)

        existing = await self.env.DB.prepare(
            "SELECT id FROM users WHERE email = ?"
        ).bind(email).first()

        if existing:
            return Response.json({"ok": False, "error": "email_exists"}, status=409)

        password_hash = await hash_password(password)

        user = None
        try:
            user = await self.env.DB.prepare(
                "INSERT INTO users (name, email, password_hash, email_verified_at) "
                "VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
                "RETURNING id, name, email"
            ).bind(name, email, password_hash).first()

            session_token = _new_token()
            session_hash = _hash_token(session_token)
            session_expires = _timestamp(
                _now() + timedelta(days=SESSION_DAYS)
            )

            await self.env.DB.prepare(
                "INSERT INTO sessions "
                "(token_hash, user_id, expires_at) VALUES (?, ?, ?)"
            ).bind(session_hash, user["id"], session_expires).run()

            response = Response.redirect(
                self.absolute_url(request, "/account"),
                status=303,
            )
            response.headers.set(
                "Set-Cookie",
                _cookie(
                    "darkomat_session",
                    session_token,
                    SESSION_DAYS * 86400,
                ),
            )
            return response

        except Exception:
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
            }, status=500)

    async def verify_email(self, request, language):
        return self.html(
            message_page(
                language,
                t("auth.verification_not_available", language),
                t("error.back_home", language),
                "/",
            ),
            status=404,
        )

    async def login(self, request, language):
        data = await self.form_data(request)

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return Response.json({"ok": False, "error": "required"}, status=400)

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

        session_token = _new_token()
        session_hash = _hash_token(session_token)
        expires_at = _timestamp(
            _now() + timedelta(days=SESSION_DAYS)
        )

        await self.env.DB.prepare(
            "INSERT INTO sessions "
            "(token_hash, user_id, expires_at) VALUES (?, ?, ?)"
        ).bind(session_hash, user["id"], expires_at).run()

        response = Response.redirect(
            self.absolute_url(request, "/account"),
            status=303,
        )
        response.headers.set(
            "Set-Cookie",
            _cookie("darkomat_session", session_token, SESSION_DAYS * 86400),
        )
        return response

    async def logout(self, request):
        cookies = request.headers.get("Cookie", "")
        token = self.cookie_value(cookies, "darkomat_session")

        if token:
            await self.env.DB.prepare(
                "DELETE FROM sessions WHERE token_hash = ?"
            ).bind(_hash_token(token)).run()

        response = Response.redirect(
            self.absolute_url(request, "/"),
            status=303,
        )
        response.headers.set(
            "Set-Cookie",
            _clear_cookie("darkomat_session"),
        )
        return response

    async def current_user(self, request):
        token = self.cookie_value(
            request.headers.get("Cookie", ""),
            "darkomat_session",
        )

        if not token:
            return None

        session = await self.env.DB.prepare(
            "SELECT users.id, users.name, users.email "
            "FROM sessions "
            "JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? "
            "AND sessions.expires_at > ?"
        ).bind(_hash_token(token), _timestamp(_now())).first()

        return session

    @staticmethod
    def cookie_value(cookie_header: str, name: str):
        for part in cookie_header.split(";"):
            key, separator, value = part.strip().partition("=")
            if separator and key == name:
                return value
        return None
