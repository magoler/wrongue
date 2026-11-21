"""Wrongue: fix text typed in the wrong keyboard language.

Flow:  select the text  ->  switch keyboard language  ->  the text is retyped
       as if you had typed it in the right language.

A backup hotkey (default Ctrl+Alt+L / Ctrl+Option+L) does the same thing
without switching language.

Runs on macOS and Windows. See README.md for setup.
"""

import sys
import threading
import time

import clipboard
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from converter import convert

# ---------------- settings ----------------
OTHER_LANGUAGE = "he"            # your second language: "he", "ru" (add more in converter.py)
HOTKEY = "<ctrl>+<alt>+l"        # manual convert hotkey (pynput syntax)
CONVERT_ON_LAYOUT_SWITCH = True  # convert the selection when you switch keyboard language
# ------------------------------------------

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")

kb = keyboard.Controller()
CMD = Key.cmd if IS_MAC else Key.ctrl
# Physical key codes for C and V, so copy/paste works whatever layout is active.
KEY_C = KeyCode.from_vk(8 if IS_MAC else 0x43)
KEY_V = KeyCode.from_vk(9 if IS_MAC else 0x56)

MODIFIERS = {Key.cmd, Key.cmd_r, Key.ctrl, Key.ctrl_r, Key.alt, Key.alt_r,
             Key.shift, Key.shift_r}
_held = set()
_busy = threading.Lock()


def log(msg):
    # Never pass the user's text in here.
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ---------------- apps we never touch ----------------
# Terminals (a paste there lands on the command line) and password managers.
EXCLUDED_MAC_APPS = {
    "com.apple.Terminal", "com.googlecode.iterm2", "dev.warp.Warp-Stable",
    "net.kovidgoyal.kitty", "io.alacritty", "org.alacritty", "com.github.wez.wezterm",
    "com.mitchellh.ghostty", "co.zeit.hyper", "com.apple.keychainaccess",
    "com.apple.Passwords", "com.1password.1password", "com.agilebits.onepassword7",
    "com.bitwarden.desktop", "com.lastpass.LastPass", "in.sinew.Enpass-Desktop",
    "org.keepassxc.keepassxc", "com.dashlane.dashlanephonefinal",
}
EXCLUDED_WIN_EXES = {
    "windowsterminal.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe",
    "wsl.exe", "mintty.exe", "putty.exe", "alacritty.exe", "wezterm-gui.exe",
    "1password.exe", "bitwarden.exe", "keepass.exe", "keepassxc.exe", "lastpass.exe",
    "dashlane.exe", "enpass.exe",
}


def _frontmost_app():
    try:
        if IS_MAC:
            from AppKit import NSWorkspace
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return app.bundleIdentifier() if app else None
        if IS_WIN:
            import ctypes
            import os
            from ctypes import wintypes
            u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(u32.GetForegroundWindow(), ctypes.byref(pid))
            h = k32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
            if not h:
                return None
            try:
                buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                    return os.path.basename(buf.value).lower()
            finally:
                k32.CloseHandle(h)
    except Exception:
        pass
    return None


def _is_excluded_app():
    app = _frontmost_app()
    return app in (EXCLUDED_MAC_APPS if IS_MAC else EXCLUDED_WIN_EXES)


# ---------------- clipboard helpers ----------------

def _tap(key):
    with kb.pressed(CMD):
        kb.press(key)
        kb.release(key)


def _wait_for_modifiers_released(timeout=1.5):
    """Don't send Cmd+C while the user still holds Alt+Shift / Cmd+Space etc."""
    end = time.time() + timeout
    while _held & MODIFIERS and time.time() < end:
        time.sleep(0.02)
    time.sleep(0.05)


def _copy_selection():
    """Press copy; return the selected text, or '' if the app copied nothing."""
    before = clipboard.change_count()
    _tap(KEY_C)
    for _ in range(20):
        time.sleep(0.025)
        if clipboard.change_count() != before:
            return clipboard.get_text()
    return ""


def _paste_text(new_text):
    clipboard.set_private_text(new_text)
    time.sleep(0.05)
    _tap(KEY_V)
    time.sleep(0.3)  # let the app finish pasting before restoring


# ---------------- macOS: ask the app directly if something is selected ----------------

def _mac_selected_text():
    """Selected text via the Accessibility API, '' if nothing selected, None if unknown."""
    try:
        from ApplicationServices import (AXUIElementCopyAttributeValue,
                                         AXUIElementCreateSystemWide)
        system = AXUIElementCreateSystemWide()
        err, focused = AXUIElementCopyAttributeValue(system, "AXFocusedUIElement", None)
        if err or focused is None:
            return None
        err, selected = AXUIElementCopyAttributeValue(focused, "AXSelectedText", None)
        if err or selected is None:
            return None
        return str(selected)
    except Exception:
        return None


# ---------------- the conversion ----------------

def convert_selection(trigger):
    if not _busy.acquire(blocking=False):
        return
    try:
        _wait_for_modifiers_released()
        if _is_excluded_app():
            return  # terminal or password manager: never touch
        known = _mac_selected_text() if IS_MAC else None
        if trigger == "layout" and known == "":
            return  # just a normal language switch, nothing selected

        previous = clipboard.save()
        count_before = clipboard.change_count()
        try:
            # If the app told us the selection, the original never touches the clipboard.
            text = known if known else _copy_selection()
            if not text.strip():
                return
            # Editors like VS Code copy the whole line when nothing is selected.
            # On a plain language switch we don't want to touch that line.
            if (trigger == "layout" and known is None
                    and text.endswith("\n") and text.count("\n") == 1):
                return
            new_text = convert(text, OTHER_LANGUAGE)
            if new_text == text:
                return
            _paste_text(new_text)
            log(f"converted {len(text)} characters ({trigger})")
        finally:
            if clipboard.change_count() != count_before:  # only if we touched it
                clipboard.restore(previous)
    except Exception as e:  # keep running whatever happens
        log(f"error: {e}")
    finally:
        _busy.release()


def _spawn(trigger):
    threading.Thread(target=convert_selection, args=(trigger,), daemon=True).start()


# ---------------- keyboard listener (hotkey + held modifiers) ----------------

def start_keyboard_listener():
    hotkey = keyboard.HotKey(keyboard.HotKey.parse(HOTKEY), lambda: _spawn("hotkey"))

    def on_press(key):
        if key in MODIFIERS:
            _held.add(key)
        hotkey.press(listener.canonical(key))

    def on_release(key):
        _held.discard(key)
        hotkey.release(listener.canonical(key))

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener


# ---------------- watching for keyboard-language switches ----------------

def run_mac():
    from Foundation import NSDistributedNotificationCenter, NSObject
    from PyObjCTools import AppHelper

    class Observer(NSObject):
        def layoutChanged_(self, _note):
            _spawn("layout")

    observer = Observer.new()
    if CONVERT_ON_LAYOUT_SWITCH:
        NSDistributedNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            observer, "layoutChanged:", "AppleSelectedInputSourcesChangedNotification", None)
    AppHelper.runConsoleEventLoop(installInterrupt=True)


def run_windows():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p

    def state():
        hwnd = user32.GetForegroundWindow()
        return hwnd, user32.GetKeyboardLayout(user32.GetWindowThreadProcessId(hwnd, None))

    last = state()
    while True:
        time.sleep(0.08)
        current = state()
        # Same window, different layout = the user switched language.
        if CONVERT_ON_LAYOUT_SWITCH and current[0] == last[0] and current[1] != last[1]:
            _spawn("layout")
        last = current


def main():
    start_keyboard_listener()
    log(f"Wrongue running (English <-> {OTHER_LANGUAGE}). "
        f"Select text and switch language, or press {HOTKEY}. Ctrl+C to quit.")
    if IS_MAC:
        run_mac()
    elif IS_WIN:
        run_windows()
    else:
        log("Only the hotkey is supported on this OS.")
        threading.Event().wait()


if __name__ == "__main__":
    main()
