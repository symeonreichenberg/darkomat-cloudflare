from html import escape

from i18n import t


def verification_email(language: str, name: str, verify_url: str) -> tuple[str, str]:
    subject = t("email.verify_subject", language)
    greeting = t("email.verify_greeting", language).format(name=escape(name))
    text = t("email.verify_text", language)
    button = t("email.verify_button", language)

    html = f"""<!doctype html>
<html lang="{escape(language)}">
<body style="font-family:Arial,sans-serif;line-height:1.6;color:#222">
  <h1>{escape(t("brand.name", language))}</h1>
  <p>{greeting}</p>
  <p>{escape(text)}</p>
  <p>
    <a href="{escape(verify_url)}"
       style="display:inline-block;padding:12px 18px;background:#f28b5b;color:white;text-decoration:none;border-radius:8px">
      {escape(button)}
    </a>
  </p>
  <p style="font-size:13px;color:#666">{escape(verify_url)}</p>
</body>
</html>"""
    return subject, html
