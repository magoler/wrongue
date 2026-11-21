from converter import convert


def test_english_typed_on_hebrew_layout():
    # Meant "hello world" but the keyboard was on Hebrew
    assert convert("יקךךם 'םרךג", "he") == "hello world"


def test_hebrew_typed_on_english_layout():
    # Meant "שלום עולם" but the keyboard was on English
    assert convert("akuo guko", "he") == "שלום עולם"


def test_caps_lock_english_to_hebrew():
    assert convert("AKUO", "he") == "שלום"


def test_round_trip_hebrew():
    s = "this is a test, ok."
    assert convert(convert(s, "he"), "he") == s


def test_russian():
    assert convert("ghbdtn", "ru") == "привет"
    assert convert("руддщ", "ru") == "hello"
    assert convert("Ghbdtn", "ru") == "Привет"


def test_digits_and_spaces_untouched():
    assert convert("akuo 123", "he") == "שלום 123"
