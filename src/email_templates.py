from html import escape

from i18n import t


def verification_email(name: str, verification_url: str, language: str):
    subject = t("email.verify_subject", language)
    title = t("email.verify_title", language)
    greeting = t("email.verify_greeting", language).format(
        name=escape(name)
    )
    text = t("email.verify_text", language)
    button = t("email.verify_button", language)
    expiry = t("email.verify_expiry", language)
    ignore = t("email.verify_ignore", language)

    html = f"""<!doctype html>
<html lang="{escape(language)}">
<body style="font-family:Arial,sans-serif;line-height:1.6;color:#332a24;">
  <h1>{escape(title)}</h1>
  <p>{greeting}</p>
  <p>{escape(text)}</p>
  <p>
    <a href="{escape(verification_url)}"
       style="display:inline-block;padding:12px 18px;background:#f28b5b;color:#fff;text-decoration:none;border-radius:8px;">
      {escape(button)}
    </a>
  </p>
  <p>{escape(expiry)}</p>
  <p style="color:#6f655e;font-size:14px;">{escape(ignore)}</p>
</body>
</html>"""

    plain_text = (
        f"{title}\n\n"
        f"{greeting}\n\n"
        f"{text}\n\n"
        f"{button}: {verification_url}\n\n"
        f"{expiry}\n\n"
        f"{ignore}"
    )

    return {
        "subject": subject,
        "html": html,
        "text": plain_text,
    }
