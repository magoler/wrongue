# Wrongue

*For when you typed in the wrong tongue.*

Typed a sentence in the wrong keyboard language? Select it and switch language.
Wrongue retypes it as if you'd typed it in the right language.

```
akuo guko      →  select  →  switch to Hebrew  →  שלום עולם
יקךךם 'םרךג    →  select  →  switch to English →  hello world
```

You can also press **Ctrl+Option+L** (Windows: **Ctrl+Alt+L**). It converts the selection without switching language.

Supports English ↔ Hebrew and English ↔ Russian. More languages are easy to add (see below).

---

## Install on Mac

Wrongue isn't signed by Apple yet, so there's no download. You build it yourself on your own Mac. That takes one command, and macOS won't show any "unidentified developer" warnings.

**1. You need Homebrew and Python.** If you don't have Homebrew, install it from [brew.sh](https://brew.sh). Then:
```bash
brew install python git
```

**2. Download and build Wrongue:**
```bash
git clone https://github.com/magoler/wrongue.git
```
```bash
cd wrongue && ./build_mac.sh
```
This builds `Wrongue.app`, copies it to your Applications folder and opens it.
Look for **A⇄א** in the menu bar.

**3. Give it permission.** Wrongue needs to see the selected text and press copy/paste for you.
1. Open **System Settings → Privacy & Security → Accessibility** and turn on **Wrongue**.
2. Open **System Settings → Privacy & Security → Input Monitoring** and turn on **Wrongue**. If it isn't listed, click **+** and pick it from Applications.
3. Quit Wrongue from the menu bar icon and open it again from Applications.

**4. Turn on Start at login** in the **A⇄א** menu.

**Try it:** in Notes, type `akuo guko` with your keyboard on English. Select it and switch to Hebrew.

### Menu options
- **Convert when I switch language:** turn it off if you only want the shortcut.
- **Second language:** Hebrew or Russian.
- **Start at login**
- **Quit Wrongue**

### Update
```bash
cd wrongue && git pull && ./build_mac.sh
```
macOS asks for the permissions again after every update (see Known issues).

### Uninstall
Quit Wrongue, delete `/Applications/Wrongue.app`, and remove it from both permission lists in System Settings. Then:
```bash
rm -f ~/Library/LaunchAgents/com.wrongue.app.plist
```
```bash
rm -rf ~/Library/Application\ Support/Wrongue
```

## Install on Windows (experimental)

There's no app yet. You run the script directly. **Not tested on Windows yet.** Bug reports are welcome.

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/). Tick "Add Python to PATH".
2. In PowerShell:
```powershell
git clone https://github.com/magoler/wrongue.git
cd wrongue
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python switcher.py
```
3. Keep the window open while you use it. To change the second language, edit `OTHER_LANGUAGE` at the top of `switcher.py`.

---

## Known issues

**General**
- **Any selected text converts when you switch language.** That includes text you selected for another reason. Press **Cmd+Z** (Windows: Ctrl+Z) to undo, or turn off *Convert when I switch language* and use the shortcut instead.
- **Whole selection, one direction.** The direction is chosen by which letters are in the majority. A selection mixing correct Hebrew and wrong-layout English converts all of it the same way.
- **Only English ↔ one other language at a time.** You pick the other language in the menu.
- **The shortcut is fixed** to Ctrl+Option+L unless you edit `HOTKEY` in `switcher.py`. It may clash with a shortcut in another app.

**Mac**
- **Not signed by Apple.** That's why you build it yourself for now.
- **Permissions reset on every rebuild or update.** Turn Wrongue on again in Accessibility and Input Monitoring. In the old entry, use **−** to remove it, then add it again.
- **The shortcut needs Input Monitoring and a restart** of Wrongue after you grant it. Converting on language switch works without that restart.
- **Some apps (often Electron apps) don't report the selected text.** In those, Wrongue briefly uses Cmd+C to read it.
- **The terminal panel inside VS Code isn't excluded.** It's part of the editor window, so Wrongue can't tell it apart. Real terminal apps are excluded.
- **Clipboard history apps** skip Wrongue's clipboard entries only if they follow the [nspasteboard.org](http://nspasteboard.org) markers. Most popular ones do (Raycast, Paste, Alfred, Maccy).

**Windows**
- **Untested.**
- **Every language switch sends Ctrl+C.** Most apps ignore it when nothing is selected. Editors that copy the whole line instead are detected and skipped.
- **Only text clipboard contents are restored.** If you had an image copied, it's lost after a conversion.
- **Apps running as administrator:** Wrongue must also run as admin to type into them.

---

## Privacy and security

- **No network code.** Nothing you type is saved or sent anywhere. The log only says how many characters were converted.
- **Private clipboard:**
  - **Mac:** converted text is marked so clipboard history apps and Universal Clipboard skip it.
  - **Windows:** converted text is kept out of Win+V history and cloud clipboard sync.
- **On Mac, the original text usually never touches the clipboard.** Wrongue reads it through Accessibility when the app allows.
- **Your clipboard is restored afterwards.**
- **Never active in terminals or password managers.** Covered apps: Terminal, iTerm, Warp, Ghostty, kitty, Windows Terminal, PowerShell, 1Password, Bitwarden, Keychain, Passwords and others. The full list is in `switcher.py`.
- **What the permissions are used for:** Accessibility and Input Monitoring are powerful. Wrongue only uses them to notice modifier keys and its shortcut, read the selected text, and press copy/paste. The code is short, so read it if you're unsure.

## How it works

1. Wrongue notices keyboard-language changes. On Mac it listens for the system's input-source notification. On Windows it checks the active window's layout every 80 ms.
2. If text is selected, Wrongue reads it.
3. It converts the text by physical key position (the key `a` ↔ `ש`).
4. It pastes the result over the selection and restores your clipboard.

## Adding a language

In `converter.py`, add a 34-character string to `LAYOUTS`. It lists what each key in
`` `qwertyuiop[]asdfghjkl;'zxcvbnm,./ `` produces on that layout. Add it to the menu names in `app.py`, then run the tests:
```bash
.venv-build/bin/python -m pytest
```

## License

MIT
