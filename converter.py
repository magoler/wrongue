"""Convert text typed on the wrong keyboard layout.

Works by physical key position: every character is mapped to the character the
same key would produce on the other layout (e.g. on Hebrew, the key "a" gives "ש").

To add a language, add a 34-character string to LAYOUTS listing what each key
in EN_KEYS produces on that layout.
"""

# The keys, in order: ` row, q row, a row, z row (US English layout)
EN_KEYS = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"

LAYOUTS = {
    # Standard Hebrew (SI-1452 as shipped on Mac/Windows)
    "he": ";/'קראטוןםפ][שדגכעיחלךף,זסבהנמצתץ.",
    # Russian (ЙЦУКЕН)
    "ru": "ёйцукенгшщзхъфывапролджэячсмитьбю.",
}

for _code, _keys in LAYOUTS.items():
    assert len(_keys) == len(EN_KEYS), f"layout {_code} must have {len(EN_KEYS)} chars"


def _build_maps(code):
    to_other, to_en = {}, {}
    for en, other in zip(EN_KEYS, LAYOUTS[code]):
        to_other[en] = other
        to_en.setdefault(other, en)
        if en.isalpha():
            # Caps lock / shift on English: Hebrew has no case, Russian does.
            to_other[en.upper()] = other.upper()
            if other.upper() != other:
                to_en.setdefault(other.upper(), en.upper())
    return to_other, to_en


_MAPS = {code: _build_maps(code) for code in LAYOUTS}


def _letters_of(code):
    return {c for c in _MAPS[code][1] if c.isalpha() and not c.isascii()}


_SCRIPT_LETTERS = {code: _letters_of(code) for code in LAYOUTS}


def detect(text, other_language):
    """Return the language the text is *currently* written in: 'en' or a layout code."""
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    best_code, best_count = other_language, 0
    for code, letters in _SCRIPT_LETTERS.items():
        count = sum(1 for c in text if c in letters)
        if count > best_count:
            best_code, best_count = code, count
    return best_code if best_count > latin else "en"


def convert(text, other_language="he"):
    """Flip text between English and `other_language` (direction auto-detected)."""
    if other_language not in LAYOUTS:
        raise ValueError(f"unknown language {other_language!r}; known: {list(LAYOUTS)}")
    source = detect(text, other_language)
    if source == "en":
        table = _MAPS[other_language][0]
    else:
        table = _MAPS[source][1]
    return "".join(table.get(c, c) for c in text)
