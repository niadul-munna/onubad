"""Translation engine. Provider chain with fallback. No persistent state."""

import requests

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
GOOGLE_URL = "https://translate.googleapis.com/translate_a/single"

_BENGALI_START = "ঀ"
_BENGALI_END = "৿"


class TranslationError(Exception):
    """Raised when every provider fails."""


def detect_lang(text):
    """Return 'bn' if any Bengali-block char is present, else 'en'."""
    for ch in text or "":
        if _BENGALI_START <= ch <= _BENGALI_END:
            return "bn"
    return "en"


def _mymemory(text, src, dst, timeout):
    r = requests.get(
        MYMEMORY_URL,
        params={"q": text, "langpair": f"{src}|{dst}"},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    if str(data.get("responseStatus")) != "200":
        raise TranslationError(f"mymemory status {data.get('responseStatus')}")
    out = (data.get("responseData") or {}).get("translatedText") or ""
    if not out.strip():
        raise TranslationError("mymemory empty result")
    return out


def _google(text, src, dst, timeout):
    r = requests.get(
        GOOGLE_URL,
        params={"client": "gtx", "sl": src, "tl": dst, "dt": "t", "q": text},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    segments = data[0] or []
    out = "".join(seg[0] for seg in segments if seg and seg[0])
    if not out.strip():
        raise TranslationError("google empty result")
    return out


PROVIDERS = (_mymemory, _google)


def translate(text, src="en", dst="bn", timeout=8):
    """Translate `text` from `src` to `dst`. Tries each provider in order."""
    text = (text or "").strip()
    if not text:
        return ""
    errors = []
    for provider in PROVIDERS:
        try:
            return provider(text, src, dst, timeout)
        except Exception as exc:  # provider failed; try the next one
            errors.append(f"{provider.__name__}: {exc}")
    raise TranslationError("; ".join(errors))
