from html import escape

from i18n import t


def layout(language: str, title: str, body: str, description: str = "") -> str:
    return f"""<!doctype html>
<html lang="{escape(language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(description)}">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header class="site-header">
    <div class="container nav">
      <a class="brand" href="/">{escape(t("brand.name", language))}</a>
      <nav class="nav-links" aria-label="Main navigation">
        <a href="/#how-it-works">{escape(t("nav.how_it_works", language))}</a>
        <a href="/#why">{escape(t("nav.why", language))}</a>
        <a href="/login">{escape(t("nav.login", language))}</a>
        <a class="button button-small" href="/register">{escape(t("nav.register", language))}</a>
      </nav>
    </div>
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <div class="container footer-inner">
      <span>{escape(t("brand.name", language))} — {escape(t("footer.tagline", language))}</span>
    </div>
  </footer>
</body>
</html>"""


def home_page(language: str) -> str:
    return layout(
        language,
        t("home.meta_title", language),
        f"""
<section class="hero">
  <div class="container hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">{escape(t("home.eyebrow", language))}</p>
      <h1>{escape(t("home.title", language))}</h1>
      <p class="hero-text">{escape(t("home.subtitle", language))}</p>
      <div class="hero-actions">
        <a class="button" href="/register">{escape(t("home.cta", language))}</a>
        <a class="text-link" href="#how-it-works">{escape(t("home.secondary_cta", language))}</a>
      </div>
    </div>
    <div class="wishlist-preview">
      <div class="preview-header">
        <div>
          <span class="preview-kicker">{escape(t("home.preview_kicker", language))}</span>
          <h2>{escape(t("home.preview_title", language))}</h2>
        </div>
        <span class="badge">{escape(t("home.preview_badge", language))}</span>
      </div>
      {_gift_card("🎧", "home.preview_item_1", "home.preview_item_1_detail", "home.preview_available", language)}
      {_gift_card("📚", "home.preview_item_2", "home.preview_item_2_detail", "home.preview_reserved", language, True)}
      {_gift_card("☕", "home.preview_item_3", "home.preview_item_3_detail", "home.preview_available", language)}
    </div>
  </div>
</section>
<section class="section" id="how-it-works">
  <div class="container">
    <div class="section-heading">
      <p class="eyebrow">{escape(t("home.steps_eyebrow", language))}</p>
      <h2>{escape(t("home.steps_title", language))}</h2>
    </div>
    <div class="steps">
      {_step("01", "home.step_1_title", "home.step_1_text", language)}
      {_step("02", "home.step_2_title", "home.step_2_text", language)}
      {_step("03", "home.step_3_title", "home.step_3_text", language)}
    </div>
  </div>
</section>
<section class="section section-soft" id="why">
  <div class="container feature-grid">
    <div>
      <p class="eyebrow">{escape(t("home.why_eyebrow", language))}</p>
      <h2>{escape(t("home.why_title", language))}</h2>
    </div>
    <div class="features">
      {_feature("✓", "home.feature_1_title", "home.feature_1_text", language)}
      {_feature("↗", "home.feature_2_title", "home.feature_2_text", language)}
      {_feature("♡", "home.feature_3_title", "home.feature_3_text", language)}
    </div>
  </div>
</section>
<section class="cta-section">
  <div class="container cta-box">
    <div>
      <p class="eyebrow">{escape(t("home.cta_eyebrow", language))}</p>
      <h2>{escape(t("home.cta_title", language))}</h2>
      <p>{escape(t("home.cta_text", language))}</p>
    </div>
    <a class="button button-light" href="/register">{escape(t("home.cta_button", language))}</a>
  </div>
</section>
""",
        t("home.meta_description", language),
    )


def _gift_card(icon, title_key, detail_key, status_key, language, reserved=False):
    status_class = "status reserved" if reserved else "status"
    return f"""<div class="gift-card">
  <div class="gift-icon">{icon}</div>
  <div class="gift-info">
    <strong>{escape(t(title_key, language))}</strong>
    <span>{escape(t(detail_key, language))}</span>
  </div>
  <span class="{status_class}">{escape(t(status_key, language))}</span>
</div>"""


def _step(number, title_key, text_key, language):
    return f"""<article class="step">
  <span class="step-number">{number}</span>
  <h3>{escape(t(title_key, language))}</h3>
  <p>{escape(t(text_key, language))}</p>
</article>"""


def _feature(icon, title_key, text_key, language):
    return f"""<div class="feature">
  <span class="feature-icon">{icon}</span>
  <div>
    <h3>{escape(t(title_key, language))}</h3>
    <p>{escape(t(text_key, language))}</p>
  </div>
</div>"""


def auth_page(language: str, mode: str) -> str:
    is_login = mode == "login"
    title_key = "auth.login_title" if is_login else "auth.register_title"
    subtitle_key = "auth.login_subtitle" if is_login else "auth.register_subtitle"
    button_key = "auth.login_button" if is_login else "auth.register_button"

    name_field = "" if is_login else f"""
<label>
  <span>{escape(t("auth.name", language))}</span>
  <input name="name" type="text" autocomplete="name" required>
</label>"""

    footer = (
        f'<p>{escape(t("auth.no_account", language))} '
        f'<a href="/register">{escape(t("auth.create_account", language))}</a></p>'
        if is_login else
        f'<p>{escape(t("auth.have_account", language))} '
        f'<a href="/login">{escape(t("auth.login_link", language))}</a></p>'
    )

    return layout(
        language,
        t(title_key, language),
        f"""
<section class="auth-section">
  <div class="auth-card">
    <p class="eyebrow">{escape(t("brand.name", language))}</p>
    <h1>{escape(t(title_key, language))}</h1>
    <p class="auth-subtitle">{escape(t(subtitle_key, language))}</p>
    <form id="{mode}-form" class="auth-form" novalidate>
      {name_field}
      <label>
        <span>{escape(t("auth.email", language))}</span>
        <input name="email" type="email" autocomplete="email" required>
      </label>
      <label>
        <span>{escape(t("auth.password", language))}</span>
        <input name="password" type="password" autocomplete="{'current-password' if is_login else 'new-password'}" minlength="8" required>
        <small>{escape(t("auth.password_hint", language))}</small>
      </label>
      <p id="{mode}-error" class="form-error" hidden></p>
      <button class="button" type="submit">{escape(t(button_key, language))}</button>
    </form>
    {footer}
  </div>
</section>
<script src="/app.js" defer></script>
<script>window.DARKOMAT_PAGE = "{mode}";</script>
""",
    )


def not_found_page(language: str) -> str:
    return layout(
        language,
        t("error.not_found_title", language),
        f"""
<section class="auth-section">
  <div class="auth-card">
    <p class="eyebrow">{escape(t("brand.name", language))}</p>
    <h1>{escape(t("error.not_found_title", language))}</h1>
    <p class="auth-subtitle">{escape(t("error.not_found_text", language))}</p>
    <a class="button" href="/">{escape(t("error.back_home", language))}</a>
  </div>
</section>
""",
    )
