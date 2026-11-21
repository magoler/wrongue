"""Wrongue as a macOS menu bar app (no Dock icon).

Build with:  python setup.py py2app   ->   dist/Wrongue.app
"""

import json
import os
import subprocess

import rumps
from ApplicationServices import AXIsProcessTrustedWithOptions
from Foundation import NSBundle, NSDistributedNotificationCenter, NSObject

import switcher
from converter import LAYOUTS

APP_NAME = "Wrongue"
SETTINGS_FILE = os.path.expanduser(
    "~/Library/Application Support/Wrongue/settings.json")
LAUNCH_AGENT = os.path.expanduser(
    "~/Library/LaunchAgents/com.wrongue.app.plist")
LANG_NAMES = {"he": "Hebrew", "ru": "Russian"}
LANG_LETTER = {"he": "א", "ru": "Я"}
DEFAULTS = {"language": "he", "on_switch": True}


def load_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return {**DEFAULTS, **json.load(f)}
    except Exception:
        return dict(DEFAULTS)


def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


def is_trusted(prompt=False):
    return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": prompt}))


class LayoutObserver(NSObject):
    def initWithApp_(self, app):
        self = self.init()
        self.app = app
        return self

    def layoutChanged_(self, _note):
        if self.app.settings["on_switch"]:
            switcher._spawn("layout")


class WrongueApp(rumps.App):
    def __init__(self):
        super().__init__(APP_NAME, quit_button=None)
        self.settings = load_settings()
        switcher.OTHER_LANGUAGE = self.settings["language"]

        self.perm_item = rumps.MenuItem("", callback=self.open_permissions)
        self.switch_item = rumps.MenuItem("Convert when I switch language",
                                          callback=self.toggle_on_switch)
        self.lang_menu = rumps.MenuItem("Second language")
        for code in LAYOUTS:
            self.lang_menu.add(rumps.MenuItem(LANG_NAMES.get(code, code),
                                              callback=self.make_lang_setter(code)))
        self.login_item = rumps.MenuItem("Start at login", callback=self.toggle_login)

        self.menu = [
            self.perm_item,
            None,
            self.switch_item,
            rumps.MenuItem("Shortcut: Ctrl+Option+L"),
            self.lang_menu,
            self.login_item,
            None,
            rumps.MenuItem("Quit Wrongue", callback=rumps.quit_application),
        ]
        self.refresh()

        # Ask macOS for Accessibility once (adds us to the list in System Settings).
        is_trusted(prompt=True)
        switcher.start_keyboard_listener()
        self.observer = LayoutObserver.alloc().initWithApp_(self)
        NSDistributedNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self.observer, "layoutChanged:",
            "AppleSelectedInputSourcesChangedNotification", None)

    # ---- menu state ----
    def refresh(self):
        code = self.settings["language"]
        self.title = f"A⇄{LANG_LETTER.get(code, code)}"
        self.switch_item.state = self.settings["on_switch"]
        for code_, item in zip(LAYOUTS, self.lang_menu.values()):
            item.state = code_ == code
        self.login_item.state = os.path.exists(LAUNCH_AGENT)
        self.perm_item.title = ("✓ Permissions OK" if is_trusted()
                                else "⚠ Needs permissions — click to open Settings")

    @rumps.timer(3)
    def poll_permissions(self, _):
        self.refresh()

    # ---- actions ----
    def toggle_on_switch(self, _):
        self.settings["on_switch"] = not self.settings["on_switch"]
        save_settings(self.settings)
        self.refresh()

    def make_lang_setter(self, code):
        def set_lang(_):
            self.settings["language"] = code
            switcher.OTHER_LANGUAGE = code
            save_settings(self.settings)
            self.refresh()
        return set_lang

    def toggle_login(self, _):
        if os.path.exists(LAUNCH_AGENT):
            os.remove(LAUNCH_AGENT)
        else:
            app_path = NSBundle.mainBundle().bundlePath()
            os.makedirs(os.path.dirname(LAUNCH_AGENT), exist_ok=True)
            with open(LAUNCH_AGENT, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.wrongue.app</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/open</string><string>-a</string><string>{app_path}</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
""")
        self.refresh()

    def open_permissions(self, _):
        subprocess.Popen(["open", "x-apple.systempreferences:"
                          "com.apple.preference.security?Privacy_Accessibility"])


if __name__ == "__main__":
    WrongueApp().run()
