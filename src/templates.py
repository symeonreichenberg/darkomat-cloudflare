from html import escape
from i18n import t


def layout(language, title, body, logged_in=False):
    nav = (
        f'<a href="/app">{escape(t("nav.dashboard", language))}</a>'
        f'<form class="inline-form" method="post" action="/api/logout">'
        f'<button class="nav-button" type="submit">{escape(t("nav.logout", language))}</button></form>'
        if logged_in else
        f'<a href="/login">{escape(t("nav.login", language))}</a>'
        f'<a class="button button-small" href="/register">{escape(t("nav.register", language))}</a>'
    )
    return f"""<!doctype html>
<html lang="{language}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{escape(t("home.meta_description", language))}">
<title>{escape(title)}</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header class="site-header"><div class="container nav">
<a class="brand" href="/">{escape(t("brand.name", language))}</a>
<nav class="nav-links">{nav}</nav>
</div></header>
<main>{body}</main>
<footer class="site-footer"><div class="container">{escape(t("brand.name", language))}</div></footer>
</body></html>"""


def home_page(language):
    return layout(language, t("home.meta_title", language), f"""
<section class="hero"><div class="container hero-grid">
<div class="hero-copy">
<p class="eyebrow">{escape(t("home.eyebrow", language))}</p>
<h1>{escape(t("home.title", language))}</h1>
<p class="hero-text">{escape(t("home.subtitle", language))}</p>
<div class="hero-actions">
<a class="button" href="/register">{escape(t("home.cta", language))}</a>
<a class="text-link" href="/login">{escape(t("home.login", language))}</a>
</div></div>
<div class="wishlist-preview">
<div class="preview-header"><span>{escape(t("home.how", language))}</span></div>
{_preview("01","home.step1","home.step1_text",language)}
{_preview("02","home.step2","home.step2_text",language)}
{_preview("03","home.step3","home.step3_text",language)}
</div></div></section>""")


def _preview(number, title, text, language):
    return f'<div class="gift-card"><div class="gift-icon">{number}</div><div class="gift-info"><strong>{escape(t(title, language))}</strong><span>{escape(t(text, language))}</span></div></div>'


def auth_page(language, mode):
    login = mode == "login"
    title = t("auth.login_title" if login else "auth.register_title", language)
    subtitle = t("auth.login_subtitle" if login else "auth.register_subtitle", language)
    button = t("auth.login_button" if login else "auth.register_button", language)
    name = "" if login else f'<label><span>{escape(t("auth.name", language))}</span><input name="name" autocomplete="name" required></label>'
    switch = (
        f'{escape(t("auth.no_account",language))} <a href="/register">{escape(t("auth.create_account",language))}</a>'
        if login else
        f'{escape(t("auth.have_account",language))} <a href="/login">{escape(t("auth.login_link",language))}</a>'
    )
    return layout(language, title, f"""
<section class="auth-section"><div class="auth-card">
<p class="eyebrow">{escape(t("brand.name",language))}</p><h1>{escape(title)}</h1>
<p class="auth-subtitle">{escape(subtitle)}</p>
<form id="{mode}-form" class="auth-form">
{name}
<label><span>{escape(t("auth.email",language))}</span><input name="email" type="email" autocomplete="email" required></label>
<label><span>{escape(t("auth.password",language))}</span><input name="password" type="password" autocomplete="{'current-password' if login else 'new-password'}" minlength="8" required><small>{escape(t("auth.password_hint",language))}</small></label>
<p id="{mode}-error" class="form-error" hidden></p>
<button class="button" type="submit">{escape(button)}</button>
</form><p>{switch}</p></div></section>
<script>
window.DARKOMAT_PAGE="{mode}";
window.DARKOMAT_MESSAGES={{{{"required":{t("auth.required",language)!r},"password_short":{t("auth.password_short",language)!r},"register_failed":{t("auth.register_failed",language)!r},"email_exists":{t("auth.email_exists",language)!r},"login_failed":{t("auth.login_failed",language)!r},"unexpected":{t("auth.unexpected",language)!r}}}}};
</script><script src="/app.js" defer></script>""")


def dashboard_page(language, user, groups):
    cards = "".join(
        f'<a class="group-card" href="/groups/{g["id"]}"><strong>{escape(g["name"])}</strong><span>{g["member_count"]} {escape(t("group.member_count",language))}</span></a>'
        for g in groups
    ) or f'<div class="empty-state"><h2>{escape(t("dashboard.empty_title",language))}</h2><p>{escape(t("dashboard.empty_text",language))}</p></div>'
    return layout(language, t("dashboard.title",language), f"""
<section class="section"><div class="container">
<div class="page-heading"><div><p class="eyebrow">{escape(t("brand.name",language))}</p><h1>{escape(t("dashboard.title",language))}</h1><p>{escape(t("dashboard.subtitle",language))}</p></div>
<a class="button" href="/groups/new">{escape(t("dashboard.new_group",language))}</a></div>
<div class="group-grid">{cards}</div></div></section>""", True)


def create_group_page(language):
    return layout(language, t("group.create_title",language), f"""
<section class="auth-section"><div class="auth-card">
<a class="text-link" href="/app">← {escape(t("group.back",language))}</a>
<h1>{escape(t("group.create_title",language))}</h1>
<form method="post" action="/api/groups" class="auth-form">
<label><span>{escape(t("group.name",language))}</span><input name="name" required></label>
<button class="button" type="submit">{escape(t("group.create",language))}</button>
</form></div></section>""", True)


def group_page(language, user, group, members, events, gifts):
    event_options = "".join(
        f'<option value="{e["id"]}">{escape(e["name"])}{" — "+escape(e["event_date"]) if e["event_date"] else ""}</option>'
        for e in events
    )
    events_html = "".join(
        f'<div class="list-row"><strong>{escape(e["name"])}</strong><span>{escape(e["event_date"] or "")}</span></div>'
        for e in events
    ) or f'<p class="muted">{escape(t("group.events",language))}</p>'
    gifts_html = "".join(_gift(g, user, language) for g in gifts) or f'<p class="muted">{escape(t("gift.no_gifts",language))}</p>'
    members_html = "".join(f'<div class="list-row"><strong>{escape(m["name"])}</strong><span>{escape(m["email"])}</span></div>' for m in members)
    return layout(language, group["name"], f"""
<section class="section"><div class="container">
<a class="text-link" href="/app">← {escape(t("group.back",language))}</a>
<div class="page-heading"><div><p class="eyebrow">{escape(t("brand.name",language))}</p><h1>{escape(group["name"])}</h1></div></div>
<div class="content-grid">
<section class="panel"><div class="panel-heading"><h2>{escape(t("group.gifts",language))}</h2></div>{gifts_html}
<form method="post" action="/api/gifts" class="stack-form">
<input type="hidden" name="group_id" value="{group["id"]}">
<h3>{escape(t("group.new_gift",language))}</h3>
<label><span>{escape(t("gift.title",language))}</span><input name="title" required></label>
<label><span>{escape(t("gift.description",language))}</span><textarea name="description" rows="3"></textarea></label>
<label><span>{escape(t("gift.shop_url",language))}</span><input name="shop_url" type="url"></label>
<label><span>{escape(t("gift.event",language))}</span><select name="event_id"><option value="">{escape(t("gift.no_event",language))}</option>{event_options}</select></label>
<button class="button" type="submit">{escape(t("gift.add",language))}</button>
</form></section>
<aside class="sidebar">
<section class="panel"><div class="panel-heading"><h2>{escape(t("group.members",language))}</h2></div>{members_html}</section>
<section class="panel"><div class="panel-heading"><h2>{escape(t("group.events",language))}</h2></div>{events_html}
<form method="post" action="/api/events" class="stack-form">
<input type="hidden" name="group_id" value="{group["id"]}">
<input name="name" placeholder="{escape(t("group.event_name",language))}" required>
<input name="event_date" type="date">
<button class="button button-small" type="submit">{escape(t("group.add_event",language))}</button>
</form></section>
</aside></div></div></section>""", True)


def _gift(g, user, language):
    reserved = bool(g["reserved"])
    own = g["owner_user_id"] == user["id"]
    action = ""
    if not own:
        action = (
            f'<form method="post" action="/api/gifts/{g["id"]}/unreserve"><button class="button button-small" type="submit">{escape(t("gift.unreserve",language))}</button></form>'
            if reserved and g["reserved_by_user_id"] == user["id"] else
            f'<form method="post" action="/api/gifts/{g["id"]}/reserve"><button class="button button-small" type="submit">{escape(t("gift.reserve",language))}</button></form>'
            if not reserved else ""
        )
    status = t("gift.reserved",language) if reserved else t("gift.available",language)
    return f"""<article class="gift-item"><div class="gift-main"><h3>{escape(g["title"])}</h3>
<p>{escape(g["description"] or "")}</p>
{f'<a href="{escape(g["shop_url"])}" target="_blank" rel="noopener">{escape(t("gift.open",language))} ↗</a>' if g["shop_url"] else ""}
</div><div class="gift-side"><span class="status {'reserved' if reserved else ''}">{escape(status)}</span>{action}</div></article>"""


def account_page(language, user):
    return layout(language, t("account.title",language), f"""
<section class="auth-section"><div class="auth-card"><p class="eyebrow">{escape(t("brand.name",language))}</p>
<h1>{escape(t("account.title",language))}</h1><p>{escape(t("account.logged_in_as",language).format(name=user["name"]))}</p><p>{escape(user["email"])}</p>
<a class="button" href="/app">{escape(t("nav.dashboard",language))}</a></div></section>""", True)


def message_page(language, title, link_text, link_url, logged_in=False):
    return layout(language, title, f'<section class="auth-section"><div class="auth-card"><h1>{escape(title)}</h1><a class="button" href="{escape(link_url)}">{escape(link_text)}</a></div></section>', logged_in)
