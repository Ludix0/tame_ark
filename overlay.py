# -*- coding: utf-8 -*-
import tkinter as tk
import ctypes

# Constantes Win32 pour la fenêtre transparente non-focusable
_GWL_EXSTYLE       = -20
_WS_EX_LAYERED     = 0x00080000
_WS_EX_TRANSPARENT = 0x00000020
_WS_EX_NOACTIVATE  = 0x08000000
_GA_ROOT           = 2


def _get_hwnd(tk_widget):
    return ctypes.windll.user32.GetAncestor(tk_widget.winfo_id(), _GA_ROOT)


class Overlay:
    """
    Overlay transparent, toujours au-dessus, sans voler le focus à ARK.
    🔓 = déplaçable   🔒 = click-through complet (souris passe au travers)
    """

    def __init__(self, parent, app):
        self.app = app
        self.locked = app.overlay_locked
        self._hwnd = None
        self._drag_ox = self._drag_oy = 0

        self.win = tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.82)
        self.win.configure(bg="#0a0a14")
        self.win.geometry(f"+{app.overlay_x}+{app.overlay_y}")

        self._build()
        self._bind_drag(self.win)
        self.win.after(80, self._init_win32)

    # ── Construction ─────────────────────────────────────────────────────────

    def _build(self):
        BG     = "#07131a"   # fond quasi noir teinté teal (comme le jeu)
        HDR    = "#0c2030"   # barre de titre teal sombre
        CYAN   = "#00cfe0"   # cyan-teal vif (couleur des bordures ARK)
        GREY   = "#5a9aaa"   # texte secondaire teal atténué
        BORDER = "#00b8c8"   # couleur de bordure extérieure

        # Bordure fine autour de toute la fenêtre
        self.win.configure(bg=BORDER)
        outer = tk.Frame(self.win, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        hdr = tk.Frame(outer, bg=HDR, pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="≡  TAME ARK", bg=HDR, fg=CYAN,
                 font=("Consolas", 7, "bold"), padx=8).pack(side="left")

        close_lbl = tk.Label(hdr, text="×", bg=HDR, fg="#4a8898",
                              font=("Segoe UI", 11, "bold"), cursor="hand2", padx=8)
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda e: self.app._hide_overlay())

        self.lock_lbl = tk.Label(
            hdr, text=("🔒" if self.locked else "🔓"),
            bg=HDR, fg="#4a8898", font=("Segoe UI", 8), cursor="hand2", padx=6
        )
        self.lock_lbl.pack(side="right")
        self.lock_lbl.bind("<Button-1>", self._toggle_lock)

        # Séparateur teal sous le header
        tk.Frame(outer, bg=CYAN, height=1).pack(fill="x")

        body = tk.Frame(outer, bg=BG, padx=12, pady=8)
        body.pack(fill="both")

        self.status_lbl = tk.Label(body, textvariable=self.app.status_var,
                                    bg=BG, fg=GREY, font=("Consolas", 8, "bold"))
        self.status_lbl.pack(anchor="w", pady=(0, 4))

        self._prefix_labels = []

        def stat_row(key, var, color):
            f = tk.Frame(body, bg=BG)
            f.pack(anchor="w", pady=2)
            prefix = tk.Label(f, text=self.app._t(key), bg=BG, fg=GREY,
                               font=("Consolas", 9))
            prefix.pack(side="left")
            tk.Label(f, textvariable=var, bg=BG, fg=color,
                     font=("Consolas", 13, "bold")).pack(side="left")
            self._prefix_labels.append((prefix, key))

        stat_row("ov_torpor",   self.app.torpor_var,    CYAN)
        stat_row("ov_press_at", self.app.threshold_var, "#e09030")
        stat_row("ov_last",     self.app.last_press_var, "#30c890")

        self.app.status_var.trace_add("write", self._update_status_color)
        self._update_status_color()

    def _update_status_color(self, *_):
        state = getattr(self.app, "_status_state", "stopped")
        color = "#30c890" if state == "active" else "#e0b030" if state == "starting" else "#5a9aaa"
        self.status_lbl.config(fg=color)

    def update_lang(self):
        for lbl, key in self._prefix_labels:
            lbl.config(text=self.app._t(key))

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _bind_drag(self, widget):
        widget.bind("<ButtonPress-1>",  self._drag_start,  add="+")
        widget.bind("<B1-Motion>",       self._drag_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._drag_end,    add="+")
        for child in widget.winfo_children():
            self._bind_drag(child)

    def _drag_start(self, event):
        if not self.locked:
            self._drag_ox = event.x_root - self.win.winfo_x()
            self._drag_oy = event.y_root - self.win.winfo_y()

    def _drag_motion(self, event):
        if not self.locked:
            self.win.geometry(f"+{event.x_root - self._drag_ox}+{event.y_root - self._drag_oy}")

    def _drag_end(self, event):
        if not self.locked:
            self.app.overlay_x = self.win.winfo_x()
            self.app.overlay_y = self.win.winfo_y()
            self.app._save_config()

    # ── Lock / click-through ─────────────────────────────────────────────────

    def _toggle_lock(self, event):
        self.locked = not self.locked
        self.app.overlay_locked = self.locked
        self.lock_lbl.config(text="🔒" if self.locked else "🔓")
        self._apply_click_through(self.locked)
        self.app._save_config()
        self.app._update_overlay_btn()

    def _init_win32(self):
        try:
            self._hwnd = _get_hwnd(self.win)
            style = ctypes.windll.user32.GetWindowLongW(self._hwnd, _GWL_EXSTYLE)
            base = style | _WS_EX_LAYERED | _WS_EX_NOACTIVATE
            if self.locked:
                base |= _WS_EX_TRANSPARENT
            ctypes.windll.user32.SetWindowLongW(self._hwnd, _GWL_EXSTYLE, base)
        except Exception as e:
            print(f"overlay win32: {e}")

    def _apply_click_through(self, enable):
        if not self._hwnd:
            return
        try:
            style = ctypes.windll.user32.GetWindowLongW(self._hwnd, _GWL_EXSTYLE)
            new_style = (style | _WS_EX_TRANSPARENT) if enable else (style & ~_WS_EX_TRANSPARENT)
            ctypes.windll.user32.SetWindowLongW(self._hwnd, _GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"click-through: {e}")
