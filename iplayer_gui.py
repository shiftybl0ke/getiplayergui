#!/usr/bin/env python3
"""
iPlayer Downloader GUI
A friendly front-end for get_iplayer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import re
import json
import os
import sys
from pathlib import Path

# ── Config persistence ────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".iplayer_gui_config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(data: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Could not save config: {e}")

# ── URL helpers ───────────────────────────────────────────────────────────────
EPISODE_RE = re.compile(r"bbc\.co\.uk/iplayer/episode/([a-z0-9]+)", re.I)
SERIES_RE  = re.compile(r"bbc\.co\.uk/iplayer/episodes/([a-z0-9]+)", re.I)

def classify_url(url: str):
    m = SERIES_RE.search(url)
    if m:
        return "series", m.group(1)
    m = EPISODE_RE.search(url)
    if m:
        return "episode", m.group(1)
    return "unknown", None

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "BG":      "#0f1117",
        "SURFACE": "#1a1d27",
        "ACCENT":  "#00b8ff",
        "ACCENT2": "#ff5c8a",
        "TEXT":    "#e8eaf0",
        "MUTED":   "#6b7280",
        "SUCCESS": "#22d3a0",
        "ERROR":   "#ff5c5c",
        "BORDER":  "#2a2d3a",
        "LOG_BG":  "#0f1117",
        "BTN_FG":  "#000000",
    },
    "light": {
        "BG":      "#f0f4f8",
        "SURFACE": "#ffffff",
        "ACCENT":  "#0070cc",
        "ACCENT2": "#d63060",
        "TEXT":    "#1a1a2e",
        "MUTED":   "#555e6e",
        "SUCCESS": "#1a9e70",
        "ERROR":   "#cc2222",
        "BORDER":  "#c8d0dc",
        "LOG_BG":  "#f8fafc",
        "BTN_FG":  "#ffffff",
    },
}

BASE_FONT  = "Segoe UI"      if sys.platform == "win32"  else "SF Pro Text"    if sys.platform == "darwin" else "Ubuntu"
BASE_TITLE = "Segoe UI"      if sys.platform == "win32"  else "SF Pro Display" if sys.platform == "darwin" else "Ubuntu"

def fonts(mode):
    return {
        "UI":    (BASE_FONT,  10),
        "BOLD":  (BASE_FONT,  10, "bold"),
        "MONO":  ("Courier New", 10),
        "TITLE": (BASE_TITLE, 18, "bold"),
        "SMALL": (BASE_FONT,  9),
    }

# ── Main App ──────────────────────────────────────────────────────────────────
class IPlayerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.process = None
        self._mode = self.config_data.get("theme", "dark")
        self._c = THEMES[self._mode]
        self._f = fonts(self._mode)
        self._themed_widgets = []   # list of (widget, role)

        self.title("iPlayer Downloader")
        self.geometry("860x720")
        self.minsize(700, 560)
        self._build_ui()
        self._apply_theme(self._mode)

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _reg(self, widget, role):
        self._themed_widgets.append((widget, role))
        return widget

    def _apply_theme(self, mode: str):
        self._mode = mode
        self._c = THEMES[mode]
        self._f = fonts(mode)
        c, f = self._c, self._f

        self.configure(bg=c["BG"])

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=c["BG"], foreground=c["TEXT"],
            fieldbackground=c["SURFACE"], bordercolor=c["BORDER"],
            troughcolor=c["SURFACE"], font=f["UI"])
        style.configure("TProgressbar",
            troughcolor=c["SURFACE"], background=c["ACCENT"],
            bordercolor=c["BORDER"], thickness=5)

        for widget, role in self._themed_widgets:
            try:
                self._theme_widget(widget, role)
            except tk.TclError:
                pass

        if hasattr(self, "log"):
            self.log.configure(bg=c["LOG_BG"], fg=c["TEXT"], font=f["MONO"])
            self.log.tag_configure("info",    foreground=c["TEXT"])
            self.log.tag_configure("success", foreground=c["SUCCESS"])
            self.log.tag_configure("error",   foreground=c["ERROR"])
            self.log.tag_configure("accent",  foreground=c["ACCENT"])
            self.log.tag_configure("muted",   foreground=c["MUTED"])

        if hasattr(self, "theme_btn"):
            label = "☀  Light mode" if mode == "dark" else "🌙  Dark mode"
            self.theme_btn.configure(text=label,
                bg=c["SURFACE"], fg=c["MUTED"],
                activebackground=c["BORDER"], activeforeground=c["TEXT"])

    def _theme_widget(self, w, role):
        c, f = self._c, self._f
        cfg = {
            "bg":            dict(bg=c["BG"]),
            "surface":       dict(bg=c["SURFACE"]),
            "label":         dict(bg=c["BG"],      fg=c["TEXT"],  font=f["UI"]),
            "label_surface": dict(bg=c["SURFACE"], fg=c["TEXT"],  font=f["UI"]),
            "label_bold":    dict(bg=c["SURFACE"], fg=c["TEXT"],  font=f["BOLD"]),
            "label_muted":   dict(bg=c["SURFACE"], fg=c["MUTED"], font=f["SMALL"]),
            "label_title":   dict(bg=c["BG"],      fg=c["ACCENT"],font=f["TITLE"]),
            "label_status":  dict(bg=c["BG"],                     font=f["UI"]),
            "label_dot":     dict(bg=c["BG"]),
            "badge":         dict(bg=c["SURFACE"],                font=f["BOLD"]),
            "entry":         dict(bg=c["SURFACE"], fg=c["TEXT"],
                                  insertbackground=c["ACCENT"],
                                  highlightbackground=c["BORDER"],
                                  highlightcolor=c["ACCENT"], font=f["UI"]),
            "btn_browse":    dict(bg=c["BORDER"],  fg=c["TEXT"],
                                  activebackground=c["ACCENT"], activeforeground=c["BTN_FG"],
                                  font=f["UI"]),
            "btn_download":  dict(bg=c["ACCENT"],  fg=c["BTN_FG"],
                                  activebackground=c["ACCENT"], activeforeground=c["BTN_FG"],
                                  font=f["BOLD"]),
            "btn_stop":      dict(bg=c["ACCENT2"], fg="#fff",
                                  activebackground=c["ACCENT2"], activeforeground="#fff",
                                  font=f["UI"]),
            "btn_open":      dict(bg=c["SURFACE"], fg=c["TEXT"],
                                  activebackground=c["BORDER"], activeforeground=c["TEXT"],
                                  font=f["UI"]),
            "btn_clear":     dict(bg=c["SURFACE"], fg=c["MUTED"],
                                  activebackground=c["SURFACE"], activeforeground=c["ERROR"],
                                  font=f["UI"]),
            "radio":         dict(bg=c["SURFACE"], fg=c["TEXT"],
                                  selectcolor=c["BG"],
                                  activebackground=c["SURFACE"], activeforeground=c["ACCENT"],
                                  font=f["UI"]),
        }
        if role in cfg:
            w.configure(**cfg[role])

    # ── UI Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = self._reg(tk.Frame(self, pady=20), "bg")
        header.pack(fill="x", padx=30)

        self._reg(tk.Label(header, text="📺  iPlayer Downloader"), "label_title").pack(side="left")

        self.theme_btn = tk.Button(header, command=self._toggle_theme,
                                   relief="flat", cursor="hand2", bd=0, padx=12, pady=6)
        self.theme_btn.pack(side="right", padx=(8, 0))

        self.status_dot = self._reg(tk.Label(header, text="●", font=("", 14)), "label_dot")
        self.status_dot.pack(side="right", padx=(0, 4))
        self.status_label = self._reg(tk.Label(header, text="Ready"), "label_status")
        self.status_label.pack(side="right")

        # ── URL Card ──
        url_card = self._reg(tk.Frame(self, padx=20, pady=16), "surface")
        url_card.pack(fill="x", padx=30, pady=(0, 12))

        self._reg(tk.Label(url_card, text="BBC iPlayer URL"), "label_bold").pack(anchor="w")
        self._reg(tk.Label(url_card, text="Paste an episode or series URL below"),
                  "label_muted").pack(anchor="w", pady=(2, 8))

        url_row = self._reg(tk.Frame(url_card), "surface")
        url_row.pack(fill="x")

        self.url_var = tk.StringVar()
        self.url_var.trace_add("write", self._on_url_change)
        self.url_entry = self._reg(
            tk.Entry(url_row, textvariable=self.url_var, relief="flat", highlightthickness=1),
            "entry")
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self._add_context_menu(self.url_entry)

        self.clear_btn = self._reg(
            tk.Button(url_row, text="✕", command=self._clear_url,
                      relief="flat", cursor="hand2", bd=0, padx=10),
            "btn_clear")
        self.clear_btn.pack(side="left")

        self.badge_var = tk.StringVar(value="")
        self.badge = self._reg(
            tk.Label(url_card, textvariable=self.badge_var, pady=4), "badge")
        self.badge.pack(anchor="w", pady=(6, 0))

        # ── Download folder card ──
        folder_card = self._reg(tk.Frame(self, padx=20, pady=14), "surface")
        folder_card.pack(fill="x", padx=30, pady=(0, 12))

        self._reg(tk.Label(folder_card, text="Download Folder"), "label_bold").pack(anchor="w", pady=(0, 8))

        folder_row = self._reg(tk.Frame(folder_card), "surface")
        folder_row.pack(fill="x")

        self.folder_var = tk.StringVar(
            value=self.config_data.get("download_folder", str(Path.home() / "Downloads")))
        self.folder_entry = self._reg(
            tk.Entry(folder_row, textvariable=self.folder_var, relief="flat", highlightthickness=1),
            "entry")
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=8)

        self._reg(
            tk.Button(folder_row, text="Browse…", command=self._browse_folder,
                      relief="flat", cursor="hand2", bd=0, padx=14, pady=8),
            "btn_browse").pack(side="left", padx=(8, 0))

        # ── Quality selector ──
        quality_card = self._reg(tk.Frame(self, padx=20, pady=14), "surface")
        quality_card.pack(fill="x", padx=30, pady=(0, 12))

        self._reg(tk.Label(quality_card, text="Download Quality"), "label_bold").pack(anchor="w", pady=(0, 8))

        quality_row = self._reg(tk.Frame(quality_card), "surface")
        quality_row.pack(anchor="w")

        self.quality_var = tk.StringVar(value=self.config_data.get("quality", "1080p"))
        for label, value in [("Full HD (1080p)", "1080p"), ("HD (720p)", "720p"),
                              ("SD (540p)", "540p"), ("Low (396p)", "396p"),
                              ("Mobile (288p)", "288p")]:
            self._reg(
                tk.Radiobutton(quality_row, text=label, variable=self.quality_var,
                               value=value, command=self._save_quality,
                               highlightthickness=0, cursor="hand2"),
                "radio").pack(side="left", padx=(0, 16))

        # ── Action buttons ──
        btn_row = self._reg(tk.Frame(self), "bg")
        btn_row.pack(fill="x", padx=30, pady=(4, 16))

        self.download_btn = self._reg(
            tk.Button(btn_row, text="⬇  Download", command=self._start_download,
                      relief="flat", cursor="hand2", bd=0, padx=20, pady=10),
            "btn_download")
        self.download_btn.pack(side="left")

        self.stop_btn = self._reg(
            tk.Button(btn_row, text="■  Stop", command=self._stop_download,
                      relief="flat", cursor="hand2", bd=0, padx=16, pady=10,
                      state="disabled"),
            "btn_stop")
        self.stop_btn.pack(side="left", padx=(10, 0))

        self._reg(
            tk.Button(btn_row, text="📁  Open Folder", command=self._open_folder,
                      relief="flat", cursor="hand2", bd=0, padx=16, pady=10),
            "btn_open").pack(side="right")

        # ── Progress bar ──
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=(0, 10))

        # ── Output log ──
        self._reg(tk.Label(self, text="Output"), "label").pack(anchor="w", padx=30)

        log_outer = tk.Frame(self, padx=1, pady=1)
        log_outer.pack(fill="both", expand=True, padx=30, pady=(4, 20))

        self.log = tk.Text(log_outer, relief="flat", wrap="word",
                           state="disabled", padx=12, pady=10)
        scrollbar = ttk.Scrollbar(log_outer, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    # ── Theme toggle ──────────────────────────────────────────────────────────
    def _toggle_theme(self):
        new_mode = "light" if self._mode == "dark" else "dark"
        self._apply_theme(new_mode)
        self.config_data["theme"] = new_mode
        save_config(self.config_data)

    # ── URL detection ─────────────────────────────────────────────────────────
    def _on_url_change(self, *_):
        url = self.url_var.get().strip()
        kind, _ = classify_url(url)
        if kind == "series":
            self.badge_var.set("📚  Series URL detected — will download all episodes")
            self.badge.configure(fg=self._c["ACCENT"])
        elif kind == "episode":
            self.badge_var.set("🎬  Episode URL detected — will download single episode")
            self.badge.configure(fg=self._c["SUCCESS"])
        else:
            self.badge_var.set("")

    def _clear_url(self):
        self.url_var.set("")
        self.url_entry.focus_set()

    # ── Quality ───────────────────────────────────────────────────────────────
    def _save_quality(self):
        self.config_data["quality"] = self.quality_var.get()
        save_config(self.config_data)

    # ── Context menu ──────────────────────────────────────────────────────────
    def _add_context_menu(self, widget):
        c = self._c
        menu = tk.Menu(self, tearoff=0, bg=c["SURFACE"], fg=c["TEXT"],
                       activebackground=c["ACCENT"], activeforeground=c["BTN_FG"],
                       relief="flat", borderwidth=1)
        menu.add_command(label="Cut",        command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy",       command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste",      command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: widget.select_range(0, "end"))

        def show_menu(event):
            widget.focus_set()
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", show_menu)

    # ── Folder ────────────────────────────────────────────────────────────────
    def _browse_folder(self):
        current = self.folder_var.get() or str(Path.home())
        folder = filedialog.askdirectory(initialdir=current, title="Choose download folder")
        if folder:
            self.folder_var.set(folder)
            self.config_data["download_folder"] = folder
            save_config(self.config_data)

    def _open_folder(self):
        folder = self.folder_var.get()
        if not folder or not Path(folder).exists():
            messagebox.showinfo("iPlayer Downloader", "Folder does not exist yet.")
            return
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    # ── Logging ───────────────────────────────────────────────────────────────
    def _log(self, text: str, tag="info"):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log_clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _set_status(self, text: str, colour: str = None):
        colour = colour or self._c["MUTED"]
        self.status_label.configure(text=text, fg=colour)
        self.status_dot.configure(fg=colour)

    # ── Download ──────────────────────────────────────────────────────────────
    def _start_download(self):
        url    = self.url_var.get().strip()
        folder = self.folder_var.get().strip()

        if not url:
            messagebox.showwarning("No URL", "Please paste a BBC iPlayer URL.")
            return

        kind, pid = classify_url(url)
        if kind == "unknown":
            messagebox.showerror(
                "Unrecognised URL",
                "That doesn't look like a BBC iPlayer episode or series URL.\n\n"
                "Episode URLs contain  /iplayer/episode/…\n"
                "Series URLs contain   /iplayer/episodes/…")
            return

        if not folder:
            messagebox.showwarning("No Folder", "Please choose a download folder.")
            return

        self.download_btn.configure(state="disabled")
        self.progress.start(12)
        self._set_status("Loading…", self._c["ACCENT"])
        self._log_clear()

        exe = r"C:\Program Files\get_iplayer\get_iplayer.cmd" if sys.platform == "win32" else "get_iplayer"
        threading.Thread(
            target=self._query_and_pick,
            args=(pid, kind, folder, exe),
            daemon=True
        ).start()

    def _query_and_pick(self, pid, kind, folder, exe):
        """Show the picker immediately — no slow network query needed."""
        self.after(0, self._show_picker, pid, kind, folder, exe, [])

    def _query_done_error(self):
        self.progress.stop()
        self.download_btn.configure(state="normal")
        self._set_status("Error", self._c["ERROR"])

    def _show_picker(self, pid, kind, folder, exe, series_nums):
        self.progress.stop()

        result = self._ask_download_choice(kind)
        if result is None:
            self.download_btn.configure(state="normal")
            self._set_status("Ready", self._c["MUTED"])
            return

        download_kind, series_filter = result

        Path(folder).mkdir(parents=True, exist_ok=True)
        self.config_data["download_folder"] = folder
        save_config(self.config_data)

        quality = self.quality_var.get()
        self._log_clear()

        if download_kind == "episode":
            cmd = [exe, "--pid", pid, "--force", "--tvquality", quality, "--output", folder]
            self._log(f"PID: {pid}", "accent")
            self._log(f"Mode: Single episode | Quality: {quality}\n", "muted")
        elif series_filter is not None:
            # First list all episodes, then download only PIDs matching the chosen series
            self._log(f"PID: {pid}", "accent")
            self._log(f"Mode: Series {series_filter} only | Quality: {quality}\n", "muted")
            self._log("Fetching episode list to filter by series…\n", "muted")
            threading.Thread(
                target=self._run_series_filtered,
                args=(exe, pid, series_filter, quality, folder),
                daemon=True
            ).start()
            return  # _run_series_filtered handles the rest
        else:
            cmd = [exe, "--pid", pid, "--pid-recursive", "--force",
                   "--tvquality", quality, "--output", folder]
            self._log(f"PID: {pid}", "accent")
            self._log(f"Mode: All series | Quality: {quality}\n", "muted")

        self._log(f"Command: {' '.join(cmd)}\n", "muted")

        self.stop_btn.configure(state="normal")
        self.progress.start(12)
        self._set_status("Downloading…", self._c["ACCENT"])

        threading.Thread(target=self._run_command, args=(cmd,), daemon=True).start()

    def _run_series_filtered(self, exe, pid, series_filter, quality, folder):
        """List all episodes via --pid-recursive-list, filter to chosen series, then download."""
        try:
            result = subprocess.run(
                [exe, "--pid", pid, "--pid-recursive-list"],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr

            # Format: "Show Name: Series N - Episode. Title, Channel, pid"
            matching_pids = []
            series_pattern = re.compile(
                rf":\s+Series\s+{re.escape(str(series_filter))}\s+-\s+.*,\s*([a-z0-9]+)\s*$",
                re.IGNORECASE
            )
            for line in output.splitlines():
                m = series_pattern.search(line)
                if m:
                    matching_pids.append(m.group(1))
                    self.after(0, self._log, f"  Found: {line.strip()}", "muted")

            if not matching_pids:
                self.after(0, self._log,
                    f"\nNo episodes found for Series {series_filter}.\n"
                    "The series name may not contain 'Series N' — try 'Download everything' instead.",
                    "error")
                self.after(0, self._on_done, 1)
                return

            self.after(0, self._log,
                f"\nFound {len(matching_pids)} episode(s) for Series {series_filter}. Starting download…\n",
                "success")

            cmd = [exe, "--pid", ",".join(matching_pids), "--force",
                   "--tvquality", quality, "--output", folder]
            self.after(0, self._log, f"Command: {' '.join(cmd)}\n", "muted")
            self._run_command(cmd)

        except subprocess.TimeoutExpired:
            self.after(0, self._log, "Timed out fetching episode list.", "error")
            self.after(0, self._on_done, 1)
        except Exception as e:
            self.after(0, self._log, f"Error fetching episode list: {e}", "error")
            self.after(0, self._on_done, 1)

    def _run_command(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
            for line in self.process.stdout:
                line = line.rstrip()
                if not line:
                    continue
                low = line.lower()
                if any(w in low for w in ("error", "failed", "not found")):
                    tag = "error"
                elif any(w in low for w in ("complete", "download", "success", "saved")):
                    tag = "success"
                elif line.startswith("INFO:") or line.startswith("--"):
                    tag = "muted"
                else:
                    tag = "info"
                self.after(0, self._log, line, tag)

            self.process.wait()
            self.after(0, self._on_done, self.process.returncode)

        except FileNotFoundError:
            self.after(0, self._log,
                "ERROR: get_iplayer not found.\n\n"
                "Expected: C:\\Program Files\\get_iplayer\\get_iplayer.cmd\n"
                "Please check get_iplayer is installed correctly.", "error")
            self.after(0, self._on_done, 1)

        except Exception as e:
            self.after(0, self._log, f"Unexpected error: {e}", "error")
            self.after(0, self._on_done, 1)

    def _on_done(self, returncode: int):
        self.progress.stop()
        self.download_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.process = None

        if returncode == 0:
            self._log("\n✓ All done!", "success")
            self._set_status("Complete", self._c["SUCCESS"])
        elif returncode == -1:
            self._log("\n■ Stopped by user.", "muted")
            self._set_status("Stopped", self._c["MUTED"])
        else:
            self._log(f"\n✗ Finished with errors (exit code {returncode}).", "error")
            self._set_status("Error", self._c["ERROR"])

    def _ask_download_choice(self, kind):
        """
        Show a picker dialog. Returns (download_kind, series_filter) or None if cancelled.
          download_kind: 'episode' | 'series'
          series_filter: None (all) or int (specific series number)
        """
        c, f = self._c, self._f
        result = tk.StringVar(value="")

        dlg = tk.Toplevel(self)
        dlg.title("What would you like to download?")
        dlg.configure(bg=c["BG"])
        dlg.resizable(False, False)
        dlg.grab_set()

        self.update_idletasks()

        tk.Label(dlg, text="What would you like to download?",
                 font=f["BOLD"], bg=c["BG"], fg=c["TEXT"]).pack(pady=(24, 4), padx=30)
        tk.Label(dlg, text="Download this episode, a specific series number, or everything.",
                 font=f["UI"], bg=c["BG"], fg=c["MUTED"]).pack(pady=(0, 16), padx=30)

        btn_frame = tk.Frame(dlg, bg=c["BG"])
        btn_frame.pack(padx=30, pady=(0, 24), fill="x")

        def choose(val):
            result.set(val)
            dlg.destroy()

        # ── Episode-only button (only for episode URLs) ──
        if kind == "episode":
            tk.Button(btn_frame, text="🎬  This episode only",
                      command=lambda: choose("episode:"),
                      bg=c["SURFACE"], fg=c["TEXT"], relief="flat",
                      font=f["UI"], cursor="hand2",
                      activebackground=c["BORDER"], activeforeground=c["TEXT"],
                      bd=0, padx=16, pady=9).pack(fill="x", pady=(0, 8))

        # ── Specific series number input ──
        series_row = tk.Frame(btn_frame, bg=c["BG"])
        series_row.pack(fill="x", pady=(0, 8))

        tk.Label(series_row, text="Specific series number:",
                 font=f["UI"], bg=c["BG"], fg=c["TEXT"]).pack(side="left")

        series_num_var = tk.StringVar()
        series_entry = tk.Entry(series_row, textvariable=series_num_var, width=4,
                                bg=c["SURFACE"], fg=c["TEXT"],
                                insertbackground=c["ACCENT"],
                                relief="flat", highlightthickness=1,
                                highlightbackground=c["BORDER"],
                                highlightcolor=c["ACCENT"],
                                font=f["UI"])
        series_entry.pack(side="left", padx=(8, 8), ipady=5)

        def choose_series_num():
            val = series_num_var.get().strip()
            if val.isdigit():
                choose(f"series:{val}")
            else:
                series_entry.configure(highlightbackground=c["ERROR"])

        tk.Button(series_row, text="Download this series",
                  command=choose_series_num,
                  bg=c["SURFACE"], fg=c["TEXT"], relief="flat",
                  font=f["UI"], cursor="hand2",
                  activebackground=c["BORDER"], activeforeground=c["TEXT"],
                  bd=0, padx=12, pady=7).pack(side="left")

        # ── All series button ──
        tk.Button(btn_frame, text="📚  Download everything",
                  command=lambda: choose("series:"),
                  bg=c["ACCENT"], fg=c["BTN_FG"], relief="flat",
                  font=f["BOLD"], cursor="hand2",
                  activebackground=c["ACCENT"], activeforeground=c["BTN_FG"],
                  bd=0, padx=16, pady=9).pack(fill="x")

        # Size and centre
        dlg.update_idletasks()
        w = max(420, dlg.winfo_reqwidth() + 20)
        h = dlg.winfo_reqheight() + 10
        x = self.winfo_x() + (self.winfo_width()  // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
        self.wait_window(dlg)

        val = result.get()
        if not val:
            return None
        parts = val.split(":", 1)
        kind_out = parts[0]
        series_out = int(parts[1]) if len(parts) > 1 and parts[1] else None
        return kind_out, series_out

    def _stop_download(self):
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = IPlayerGUI()
    app.mainloop()
