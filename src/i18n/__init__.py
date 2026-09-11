from . import cs, en

LANGUAGES = {
    "en": en.TEXTS,
    "cs": cs.TEXTS,
}


def get_language(request) -> str:
    cookie = request.headers.get("Cookie", "")
    for part in cookie.split(";"):
        name, _, value = part.strip().partition("=")
        if name == "lang" and value in LANGUAGES:
            return value

    accept_language = request.headers.get("Accept-Language", "").lower()
    if accept_language.startswith("cs") or ",cs" in accept_language or ";cs" in accept_language:
        return "cs"

    return "en"


def t(key: str, language: str) -> str:
    return LANGUAGES.get(language, LANGUAGES["en"]).get(key, key)
