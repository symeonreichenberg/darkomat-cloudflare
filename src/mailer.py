import json


async def send_email(env, to, subject, html, text, tag=None):
    """
    Send an email through Resend.

    RESEND_API_KEY is a Cloudflare secret.
    MAIL_FROM and APP_URL are Worker configuration values.
    """

    api_key = getattr(env, "RESEND_API_KEY", None)
    mail_from = getattr(env, "MAIL_FROM", None)

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    if not mail_from:
        raise RuntimeError("MAIL_FROM is not configured")

    payload = {
        "from": mail_from,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }

    if tag:
        payload["tags"] = [
            {
                "name": "category",
                "value": tag,
            }
        ]

    from js import Object, fetch
    from pyodide.ffi import to_js

    options = to_js(
        {
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "darkomat/1.0",
            },
            "body": json.dumps(payload),
        },
        dict_converter=Object.fromEntries,
    )

    response = await fetch(
        "https://api.resend.com/emails",
        options,
    )

    if not response.ok:
        try:
            details = await response.text()
        except Exception:
            details = "unknown email provider error"

        raise RuntimeError(
            f"Resend returned HTTP {response.status}: {details}"
        )

    return await response.json()
