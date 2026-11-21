"""Build the Mac app:  python setup.py py2app  ->  dist/Wrongue.app"""
from setuptools import setup

setup(
    app=["app.py"],
    name="Wrongue",
    options={
        "py2app": {
            "plist": {
                "CFBundleName": "Wrongue",
                "CFBundleDisplayName": "Wrongue",
                "CFBundleIdentifier": "com.wrongue.app",
                "CFBundleShortVersionString": "1.0",
                "LSUIElement": True,  # menu bar only, no Dock icon
            },
            "packages": ["rumps", "pynput", "pyperclip"],
            "includes": ["converter", "switcher", "clipboard"],
        }
    },
)
