import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from auth import hash_password, verify_password
from i18n import get_language
from templates import account_page, auth_page, home_page, not_found_page

SESSION_DAYS = 30


def now_utc():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token():
    return secrets.token_urlsafe(32)


def session_cookie(token):
    return (
        f"darkomat_session={token}; Path=/; Max-Age={SESSION_DAYS * 86400}; "
        "HttpOnly; Secure; SameSite=Lax"
    )


def clear_session_cookie():
    return "darkomat_session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax"


def form_values(body):
    values = parse_qs(body, keep_blank_values=True)
    return {key: items[0] if items else "" for key, items in values.items()}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path
        language = get_language(request)

        if request.method == "GET":
            if path == "/":
                user = await self.current_user(request)
                return self.html(home_page(language, user))

            if path == "/login":
                if await self.current_user(request):
                    return self.redirect(request, "/account")
                return self.html(auth_page(language, "login"))

            if path == "/register":
                if await self.current_user(request):
                    return self.redirect(request, "/account")
                return self.html(auth_page(language, "register"))

            if path in ("/account", "/app"):
                user = await self.current_user(request)
                if not user:
                    return self.redirect(request, "/login")
                return self.html(account_page(language, user))

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
            if path == "/register":
                return await self.register_form(request, language)
            if path == "/login":
                return await self.login_form(request, language)
            if path == "/logout":
                return await self.logout(request)
            if path == "/api/register":
                return await self.register_json(request)
            if path == "/api/login":
                return await self.login_json(request)
            if path == "/api/logout":
                return await self.logout(request, json_response=True)

        return Response("Not found", status=404)

    def html(self, body, status=200, headers=None):
        response_headers = {"content-type": "text/html; charset=UTF-8"}
        if headers:
            response_headers.update(headers)
        return Response(body, status=status, headers=response_headers)

    def redirect(self, request, path):
        url = urlparse(request.url)
        return Response.redirect(
            f"{url.scheme}://{url.netloc}{path}",
            status=303,
        )

    async def register_form(self, request, language):
        data = form_values(await request.text())
        result = await self.create_user(
            data.get("name", ""),
            data.get("email", ""),
            data.get("password", ""),
        )
        if not result["ok"]:
            return self.html(
                auth_page(language, "register", result["error"], data),
                status=400,
            )
        return await self.create_session_response(request, result["user"])

    async def login_form(self, request, language):
        data = form_values(await request.text())
        user, error = await self.authenticate(
            data.get("email", ""),
            data.get("password", ""),
        )
        if error:
            return self.html(
                auth_page(language, "login", error, data),
                status=401,
            )
        return await self.create_session_response(request, user)

    async def create_user(self, name, email, password):
        name = name.strip()
        email = email.strip().lower()
        if not name or not email or not password:
            return {"ok": False, "error": "required"}
        if "@" not in email or len(email) > 254:
            return {"ok": False, "error": "invalid_email"}
        if len(password) < 8:
            return {"ok": False, "error": "password_short"}

        existing = await self.env.DB.prepare(
            "SELECT id FROM users WHERE email = ?"
        ).bind(email).first()
        if existing:
            return {"ok": False, "error": "email_exists"}

        password_hash = await hash_password(password)
        try:
            user = await self.env.DB.prepare(
                "INSERT INTO users (name, email, password_hash) "
                "VALUES (?, ?, ?) RETURNING id, name, email"
            ).bind(name, email, password_hash).first()
        except Exception:
            return {"ok": False, "error": "register_failed"}
        return {"ok": True, "user": user}

    async def authenticate(self, email, password):
        email = email.strip().lower()
        if not email or not password:
            return None, "required"
        user = await self.env.DB.prepare(
            "SELECT id, name, email, password_hash "
            "FROM users WHERE email = ?"
        ).bind(email).first()
        if not user or not await verify_password(password, user["password_hash"]):
            return None, "login_failed"
        return user, None

    async def create_session_response(self, request, user):
        token = new_token()
        await self.env.DB.prepare(
            "INSERT INTO sessions (token_hash, user_id, expires_at) "
            "VALUES (?, ?, ?)"
        ).bind(
            hash_token(token),
            user["id"],
            timestamp(now_utc() + timedelta(days=SESSION_DAYS)),
        ).run()
        response = self.redirect(request, "/account")
        response.headers.set("Set-Cookie", session_cookie(token))
        return response

    async def register_json(self, request):
        try:
            data = await request.json()
        except Exception:
            return Response.json({"ok": False, "error": "required"}, status=400)
        result = await self.create_user(
            data.get("name", ""),
            data.get("email", ""),
            data.get("password", ""),
        )
        if not result["ok"]:
            return Response.json(result, status=400)
        return Response.json({"ok": True, "user": result["user"]}, status=201)

    async def login_json(self, request):
        try:
            data = await request.json()
        except Exception:
            return Response.json({"ok": False, "error": "required"}, status=400)
        user, error = await self.authenticate(
            data.get("email", ""), data.get("password", "")
        )
        if error:
            return Response.json({"ok": False, "error": error}, status=401)
        token = new_token()
        await self.env.DB.prepare(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)"
        ).bind(
            hash_token(token),
            user["id"],
            timestamp(now_utc() + timedelta(days=SESSION_DAYS)),
        ).run()
        response = Response.json({
            "ok": True,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        })
        response.headers.set("Set-Cookie", session_cookie(token))
        return response

    async def logout(self, request, json_response=False):
        token = self.cookie_value(
            request.headers.get("Cookie", ""),
            "darkomat_session",
        )
        if token:
            await self.env.DB.prepare(
                "DELETE FROM sessions WHERE token_hash = ?"
            ).bind(hash_token(token)).run()
        response = Response.json({"ok": True}) if json_response else self.redirect(request, "/")
        response.headers.set("Set-Cookie", clear_session_cookie())
        return response

    async def current_user(self, request):
        token = self.cookie_value(
            request.headers.get("Cookie", ""),
            "darkomat_session",
        )
        if not token:
            return None
        return await self.env.DB.prepare(
            "SELECT users.id, users.name, users.email "
            "FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ?"
        ).bind(
            hash_token(token), timestamp(now_utc())
        ).first()

    @staticmethod
    def cookie_value(cookie_header, name):
        for part in cookie_header.split(";"):
            key, separator, value = part.strip().partition("=")
            if separator and key == name:
                return value
        return None
