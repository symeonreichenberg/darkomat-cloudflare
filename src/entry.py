from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

from auth import hash_password, verify_password
from i18n import get_language, t
from templates import (
    account_page, auth_page, create_group_page, dashboard_page,
    group_page, home_page, message_page,
)


SESSION_DAYS = 30


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def token_hash(token):
    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token():
    import secrets
    return secrets.token_urlsafe(32)


def cookie(name, value, max_age):
    return f"{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; Secure; SameSite=Lax"


def clear_cookie(name):
    return f"{name}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax"


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path.rstrip("/") or "/"
        lang = get_language(request)

        if request.method == "GET":
            if path == "/":
                return self.html(home_page(lang))
            if path == "/login":
                return self.html(auth_page(lang, "login"))
            if path == "/register":
                return self.html(auth_page(lang, "register"))

            user = await self.current_user(request)
            if path == "/app":
                if not user:
                    return self.redirect(request, "/login")
                groups = await self.user_groups(user["id"])
                return self.html(dashboard_page(lang, user, groups))
            if path == "/groups/new":
                if not user:
                    return self.redirect(request, "/login")
                return self.html(create_group_page(lang))
            if path.startswith("/groups/"):
                if not user:
                    return self.redirect(request, "/login")
                try:
                    group_id = int(path.split("/")[2])
                except (IndexError, ValueError):
                    return self.html(message_page(lang, t("error.not_found_title",lang), t("error.back_home",lang), "/app"), 404)
                data = await self.group_data(group_id, user["id"])
                if not data:
                    return self.html(message_page(lang, t("error.not_found_title",lang), t("error.back_home",lang), "/app"), 404)
                return self.html(group_page(lang, user, *data))

            if path == "/account":
                if not user:
                    return self.redirect(request, "/login")
                return self.html(account_page(lang, user))

            if path == "/api/health":
                return Response.json({"ok": True, "app": "darkomat", "language": "python"})
            if path == "/api/db-test":
                result = await self.env.DB.prepare("SELECT COUNT(*) AS count FROM users").first()
                return Response.json({"ok": True, "database": result})

            return self.html(message_page(lang, t("error.not_found_title",lang), t("error.back_home",lang), "/"), 404)

        if request.method == "POST":
            if path == "/api/register":
                return await self.register(request)
            if path == "/api/login":
                return await self.login(request)
            if path == "/api/logout":
                return await self.logout(request)
            if path == "/api/groups":
                return await self.create_group(request)
            if path == "/api/events":
                return await self.create_event(request)
            if path == "/api/gifts":
                return await self.create_gift(request)
            if path.startswith("/api/gifts/") and path.endswith("/reserve"):
                return await self.reserve_gift(request, path, True)
            if path.startswith("/api/gifts/") and path.endswith("/unreserve"):
                return await self.reserve_gift(request, path, False)

        return Response("Not found", status=404)

    def html(self, body, status=200, headers=None):
        h = {"content-type": "text/html; charset=UTF-8"}
        if headers:
            h.update(headers)
        return Response(body, status=status, headers=h)

    def redirect(self, request, path):
        base = urlparse(request.url)
        return Response.redirect(f"{base.scheme}://{base.netloc}{path}", status=303)

    async def json_body(self, request):
        try:
            return await request.json()
        except Exception:
            return None

    async def register(self, request):
        data = await self.json_body(request)
        if not data:
            return Response.json({"ok": False, "error": "required"}, status=400)
        name = str(data.get("name","")).strip()
        email = str(data.get("email","")).strip().lower()
        password = str(data.get("password",""))
        if not name or not email or not password:
            return Response.json({"ok": False, "error": "required"}, status=400)
        if len(password) < 8:
            return Response.json({"ok": False, "error": "password_short"}, status=400)
        existing = await self.env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(email).first()
        if existing:
            return Response.json({"ok": False, "error": "email_exists"}, status=409)
        password_hash = await hash_password(password)
        try:
            user = await self.env.DB.prepare(
                "INSERT INTO users (name,email,password_hash,email_verified_at) VALUES (?,?,?,?) RETURNING id,name,email"
            ).bind(name, email, password_hash, now()).first()
        except Exception:
            return Response.json({"ok": False, "error": "register_failed"}, status=500)
        session = new_token()
        try:
            await self.env.DB.prepare(
                "INSERT INTO sessions (token_hash,user_id,expires_at) VALUES (?,?,?)"
            ).bind(token_hash(session), user["id"], (datetime.now(timezone.utc)+timedelta(days=SESSION_DAYS)).isoformat().replace("+00:00","Z")).run()
        except Exception:
            return Response.json({"ok": False, "error": "register_failed"}, status=500)
        response = Response.json({"ok": True, "user": {"id":user["id"],"name":user["name"],"email":user["email"]}}, status=201)
        response.headers.set("Set-Cookie", cookie("darkomat_session", session, SESSION_DAYS*86400))
        return response

    async def login(self, request):
        data = await self.json_body(request)
        if not data:
            return Response.json({"ok": False, "error": "required"}, status=400)
        email = str(data.get("email","")).strip().lower()
        password = str(data.get("password",""))
        user = await self.env.DB.prepare(
            "SELECT id,name,email,password_hash FROM users WHERE email=?"
        ).bind(email).first()
        if not user or not await verify_password(password, user["password_hash"]):
            return Response.json({"ok": False, "error": "login_failed"}, status=401)
        session = new_token()
        expires = (datetime.now(timezone.utc)+timedelta(days=SESSION_DAYS)).isoformat().replace("+00:00","Z")
        await self.env.DB.prepare(
            "INSERT INTO sessions (token_hash,user_id,expires_at) VALUES (?,?,?)"
        ).bind(token_hash(session), user["id"], expires).run()
        response = Response.json({"ok": True})
        response.headers.set("Set-Cookie", cookie("darkomat_session", session, SESSION_DAYS*86400))
        return response

    async def logout(self, request):
        token = self.cookie_value(request.headers.get("Cookie",""), "darkomat_session")
        if token:
            await self.env.DB.prepare("DELETE FROM sessions WHERE token_hash=?").bind(token_hash(token)).run()
        response = self.redirect(request, "/")
        response.headers.set("Set-Cookie", clear_cookie("darkomat_session"))
        return response

    async def current_user(self, request):
        token = self.cookie_value(request.headers.get("Cookie",""), "darkomat_session")
        if not token:
            return None
        return await self.env.DB.prepare(
            "SELECT u.id,u.name,u.email FROM sessions s JOIN users u ON u.id=s.user_id "
            "WHERE s.token_hash=? AND s.expires_at>?"
        ).bind(token_hash(token), now()).first()

    @staticmethod
    def cookie_value(header, name):
        for part in header.split(";"):
            k, sep, v = part.strip().partition("=")
            if sep and k == name:
                return v
        return None

    async def is_member(self, user_id, group_id):
        return await self.env.DB.prepare(
            "SELECT 1 FROM group_members WHERE group_id=? AND user_id=?"
        ).bind(group_id, user_id).first()

    async def user_groups(self, user_id):
        result = await self.env.DB.prepare(
            "SELECT g.id,g.name,COUNT(gm2.user_id) AS member_count "
            "FROM groups g JOIN group_members gm ON gm.group_id=g.id "
            "LEFT JOIN group_members gm2 ON gm2.group_id=g.id "
            "WHERE gm.user_id=? GROUP BY g.id,g.name ORDER BY g.created_at DESC"
        ).bind(user_id).all()
        return result.results

    async def group_data(self, group_id, user_id):
        if not await self.is_member(user_id, group_id):
            return None
        group = await self.env.DB.prepare("SELECT id,name FROM groups WHERE id=?").bind(group_id).first()
        members = (await self.env.DB.prepare(
            "SELECT u.id,u.name,u.email FROM group_members gm JOIN users u ON u.id=gm.user_id "
            "WHERE gm.group_id=? ORDER BY u.name"
        ).bind(group_id).all()).results
        events = (await self.env.DB.prepare(
            "SELECT id,name,event_date FROM events WHERE group_id=? ORDER BY event_date IS NULL,event_date"
        ).bind(group_id).all()).results
        gifts = (await self.env.DB.prepare(
            "SELECT g.id,g.owner_user_id,g.title,g.description,g.shop_url,g.event_id,"
            "CASE WHEN r.gift_id IS NULL THEN 0 ELSE 1 END reserved,"
            "r.reserved_by_user_id "
            "FROM gifts g LEFT JOIN reservations r ON r.gift_id=g.id "
            "WHERE g.group_id=? ORDER BY g.created_at DESC"
        ).bind(group_id).all()).results
        return group, members, events, gifts

    async def create_group(self, request):
        user = await self.current_user(request)
        if not user: return Response.json({"ok":False,"error":"login_required"}, status=401)
        data = await self.form_or_json(request)
        name = str(data.get("name","")).strip()
        if not name: return Response.json({"ok":False,"error":"required"}, status=400)
        group = await self.env.DB.prepare(
            "INSERT INTO groups (name,owner_user_id) VALUES (?,?) RETURNING id"
        ).bind(name,user["id"]).first()
        await self.env.DB.prepare(
            "INSERT INTO group_members (group_id,user_id,role) VALUES (?,?,?)"
        ).bind(group["id"],user["id"],"owner").run()
        return self.redirect(request, f"/groups/{group['id']}")

    async def create_event(self, request):
        user = await self.current_user(request)
        if not user: return Response.json({"ok":False,"error":"login_required"}, status=401)
        data = await self.form_or_json(request)
        group_id = int(data.get("group_id",0))
        if not await self.is_member(user["id"],group_id): return Response.json({"ok":False}, status=403)
        name = str(data.get("name","")).strip()
        if not name: return Response.json({"ok":False,"error":"required"}, status=400)
        await self.env.DB.prepare(
            "INSERT INTO events (group_id,name,event_date) VALUES (?,?,?)"
        ).bind(group_id,name,data.get("event_date") or None).run()
        return self.redirect(request, f"/groups/{group_id}")

    async def create_gift(self, request):
        user = await self.current_user(request)
        if not user: return Response.json({"ok":False,"error":"login_required"}, status=401)
        data = await self.form_or_json(request)
        group_id = int(data.get("group_id",0))
        if not await self.is_member(user["id"],group_id): return Response.json({"ok":False}, status=403)
        title = str(data.get("title","")).strip()
        if not title: return Response.json({"ok":False,"error":"required"}, status=400)
        event_id = data.get("event_id") or None
        await self.env.DB.prepare(
            "INSERT INTO gifts (group_id,owner_user_id,title,description,shop_url,image_url,event_id) VALUES (?,?,?,?,?,?,?)"
        ).bind(group_id,user["id"],title,data.get("description") or None,data.get("shop_url") or None,None,event_id).run()
        return self.redirect(request, f"/groups/{group_id}")

    async def reserve_gift(self, request, path, reserve):
        user = await self.current_user(request)
        if not user: return Response.json({"ok":False,"error":"login_required"}, status=401)
        try: gift_id = int(path.split("/")[3])
        except (IndexError,ValueError): return Response.json({"ok":False},status=400)
        gift = await self.env.DB.prepare("SELECT id,group_id,owner_user_id FROM gifts WHERE id=?").bind(gift_id).first()
        if not gift or not await self.is_member(user["id"],gift["group_id"]): return Response.json({"ok":False},status=403)
        if gift["owner_user_id"] == user["id"]: return Response.json({"ok":False},status=400)
        if reserve:
            existing = await self.env.DB.prepare("SELECT gift_id FROM reservations WHERE gift_id=?").bind(gift_id).first()
            if existing: return Response.json({"ok":False,"error":"already_reserved"},status=409)
            await self.env.DB.prepare("INSERT INTO reservations (gift_id,reserved_by_user_id) VALUES (?,?)").bind(gift_id,user["id"]).run()
        else:
            await self.env.DB.prepare("DELETE FROM reservations WHERE gift_id=? AND reserved_by_user_id=?").bind(gift_id,user["id"]).run()
        return self.redirect(request, f"/groups/{gift['group_id']}")

    async def form_or_json(self, request):
        ctype = request.headers.get("content-type","")
        if "application/json" in ctype:
            return await self.json_body(request) or {}
        form = await request.form_data()
        return {k: form.get(k) for k in form.keys()}
