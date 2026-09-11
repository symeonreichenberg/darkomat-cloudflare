import json

from js import Object, fetch
from pyodide.ffi import to_js


def _js_options(options):
    return to_js(options, dict_converter=Object.fromEntries)


async def send_email(env, to: str, subject: str, html: str):
    api_key = getattr(env, "RESEND_API_KEY", None)
    from_address = getattr(env, "MAIL_FROM", None)

    if not api_key or not from_address:
        raise RuntimeError("Email service is not configured")

    response = await fetch(
        "https://api.resend.com/emails",
        _js_options({
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "darkomat-cloudflare",
            },
            "body": json.dumps({
                "from": from_address,
                "to": [to],
                "subject": subject,
                "html": html,
            }),
        }),
    )

    if not response.ok:
        body = await response.text()
        raise RuntimeError(
            f"Resend API error: {response.status}: {body}"
        )

    return await response.json()
