# 📺 iPlayer Downloader GUI

A clean, dark/light themed Python GUI for downloading BBC iPlayer programmes using [get_iplayer](https://github.com/get-iplayer/get_iplayer).

Designed to make get_iplayer easy to use without touching the command line.

![Python](https://img.shields.io/badge/python-3.x-blue) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- Paste any BBC iPlayer **episode or series URL** — it auto-detects which type
- Choose to download **this episode only**, **a specific series number**, or **everything**
- Specific series filtering works reliably by querying available episodes first, then downloading only the matching ones
- **Quality selector** — Full HD (1080p), HD (720p), SD (540p), Low (396p), Mobile (288p)
- **Download folder** remembered between sessions
- **Quality preference** remembered between sessions
- **Dark and light mode** toggle, remembered between sessions
- Right-click **paste menu** in the URL box
- Live **output log** with colour-coded messages
- **Stop button** to cancel a download mid-way
- **Open Folder** button to jump straight to your downloads

---

## Requirements

- **Python 3** — [python.org](https://www.python.org/downloads/)
- **get_iplayer** — [Windows installer](https://github.com/get-iplayer/get_iplayer_win32/releases)

No additional Python packages needed — only standard library modules are used (tkinter, subprocess, threading, re, json, os, sys, pathlib).

---

## Installation

**1. Install get_iplayer**

Download and run the Windows installer from the [get_iplayer releases page](https://github.com/get-iplayer/get_iplayer_win32/releases). The default install path is:

```
C:\Program Files\get_iplayer\get_iplayer.cmd
```

The GUI expects this path by default on Windows.

**2. Clone this repo**

```bash
git clone https://github.com/shiftybl0ke/iplayer-gui.git
cd iplayer-gui
```

**3. Run the app**

```bash
python iplayer_gui.py
```

---

## Usage

1. Find a programme on [BBC iPlayer](https://www.bbc.co.uk/iplayer)
2. Copy the URL — works with both episode and series URLs:
   - Episode: `https://www.bbc.co.uk/iplayer/episode/b03wc5fl/...`
   - Series: `https://www.bbc.co.uk/iplayer/episodes/b03wh7vl/...`
3. Paste it into the URL box
4. Choose your download folder and quality
5. Click **Download** and choose what to grab from the picker

---

## Platform Notes

| Platform | Status |
|----------|--------|
| Windows | ✅ Fully tested |
| macOS | ✅ Should work — install get_iplayer via `brew install get-iplayer` |
| Linux | ✅ Should work — install via `sudo apt install get-iplayer` |

On macOS and Linux, get_iplayer is expected to be on your system PATH. The explicit path is only used on Windows.

---

## Settings

User preferences are saved automatically to `~/.iplayer_gui_config.json`:

- Download folder
- Quality preference
- Dark/light theme

---

## Acknowledgements

- [get_iplayer](https://github.com/get-iplayer/get_iplayer) — the command line tool that does all the heavy lifting
- Built with Python's built-in tkinter UI library
