from .cs import TEXTS as CS
from .en import TEXTS as EN

def get_language(request):
    cookie = request.headers.get("Cookie", "")
    if "darkomat_lang=cs" in cookie:
        return "cs"
    if "darkomat_lang=en" in cookie:
        return "en"
    return "cs"

def t(key, language="cs"):
    return (CS if language == "cs" else EN).get(key, key)
