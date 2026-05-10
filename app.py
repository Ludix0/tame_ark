# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import threading
import time
import math
import json
import os

import pyautogui
import keyboard
from PIL import Image

from constants import CONFIG_FILE, DEFAULT_HOTKEY, DEFAULT_NARCO_HOTKEY, DEFAULT_REGION, CHECK_INTERVAL
from region_selector import RegionSelector
from overlay import Overlay
from i18n import TRANSLATIONS
import ocr


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("540x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f1a")

        self.monitoring = False
        self.hotkey_name = DEFAULT_HOTKEY
        self.region = dict(DEFAULT_REGION)
        self.margin = tk.IntVar(value=3)
        self.lang = "fr"
        self._status_state = "stopped"
        self.status_var = tk.StringVar(value="Arrêté")
        self.torpor_var = tk.StringVar(value="—")
        self.countdown_var = tk.StringVar(value="")
        self.action_var = tk.StringVar(value="")
        self.last_press_var = tk.StringVar(value="—")
        self.next_check_var = tk.StringVar(value="")
        self.narco_var = tk.StringVar(value="")
        self.cible_var = tk.StringVar(value="")
        self.threshold_var = tk.StringVar(value="—")
        self._torpor_max_live = None
        self.overlay = None
        self.overlay_x = 50
        self.overlay_y = 50
        self.overlay_locked = False
        self.label_region = None
        self.win_x = 100
        self.win_y = 100
        self._save_pos_job = None
        self.narco_icon_region = None
        self.narco_hotkey_name = DEFAULT_NARCO_HOTKEY
        self.overlay_open = False

        self._load_config()
        if not self.label_region:
            self.label_region = self._compute_default_label_region()
        self._build_ui()
        self.root.title(self._t("title_window"))
        self.status_var.set(self._t("status_stopped"))
        self.root.geometry(f"+{self.win_x}+{self.win_y}")
        self.root.bind("<Configure>", self._on_win_move)
        self.margin.trace_add("write", self._on_margin_change)
        self._register_hotkey()
        if self.overlay_open:
            self.root.after(200, self._show_overlay)

    # ------------------------------------------------------------------ i18n

    def _t(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["fr"]).get(key, key)

    def _on_lang_change(self, value):
        self.lang = "fr" if value == "Français" else "en"
        self._apply_lang()
        self._save_config()

    def _apply_lang(self):
        t = self._t
        self.root.title(t("title_window"))
        self._title_lbl.config(text=t("title"))
        self._lbl_margin.config(text=t("margin_label"))
        self._lbl_margin_below.config(text=t("margin_below"))
        self._lbl_hotkey.config(text=t("hotkey_label"))
        self.hotkey_btn.config(text=t("btn_change"))
        self._lbl_narco_hotkey.config(text=t("narco_hotkey_label"))
        self.calib_zone_btn.config(text=t("btn_calib_zone"))
        self.calib_label_btn.config(text=t("btn_calib_label"))
        self._update_calib_narco_btn()
        self.narco_hotkey_btn.config(text=t("btn_change"))
        self.test_ocr_btn.config(text=t("btn_test_ocr"))
        self._lbl_status.config(text=t("status_label"))
        self._lbl_torpor.config(text=t("torpor_label"))
        self._lbl_next_check.config(text=t("next_check_label"))
        self._lbl_narco.config(text=t("narco_label"))
        self._lbl_target.config(text=t("target_label"))
        self._lbl_last_press.config(text=t("last_press_label"))
        self._lbl_footer.config(text=t("footer"))
        self._update_overlay_btn()

        state = self._status_state
        if state == "stopped":
            self.status_var.set(t("status_stopped"))
        elif state == "starting":
            self.status_var.set(t("status_starting"))
        elif state == "active":
            self.status_var.set(t("status_active"))

        if self.monitoring:
            self.main_btn.config(text=t("btn_stop"))
        else:
            self.main_btn.config(text=f"{t('btn_start')}   ({self.hotkey_name.upper()})")

        if self.overlay and self.overlay.win.winfo_exists():
            self.overlay.update_lang()

    # ------------------------------------------------------------------ config

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                cfg = json.load(open(CONFIG_FILE))
                self.hotkey_name = cfg.get("hotkey", DEFAULT_HOTKEY)
                self.narco_hotkey_name = cfg.get("narco_hotkey", DEFAULT_NARCO_HOTKEY)
                self.margin.set(max(0, min(5, int(cfg.get("margin", 3)))))
                self.overlay_x = cfg.get("overlay_x", 50)
                self.overlay_y = cfg.get("overlay_y", 50)
                self.overlay_locked = cfg.get("overlay_locked", False)
                self.overlay_open = cfg.get("overlay_open", False)
                self.win_x = cfg.get("win_x", 100)
                self.win_y = cfg.get("win_y", 100)
                self.lang = cfg.get("lang", "fr")
                if "region" in cfg:
                    self.region = cfg["region"]
                if "label_region" in cfg:
                    self.label_region = cfg["label_region"]
                if "narco_icon_region" in cfg:
                    self.narco_icon_region = cfg["narco_icon_region"]
            except Exception:
                pass

    def _save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        cfg = {
            "hotkey": self.hotkey_name,
            "narco_hotkey": self.narco_hotkey_name,
            "margin": self.margin.get(),
            "region": self.region,
            "label_region": self.label_region,
            "narco_icon_region": self.narco_icon_region,
            "overlay_x": self.overlay.win.winfo_x() if self.overlay else self.overlay_x,
            "overlay_y": self.overlay.win.winfo_y() if self.overlay else self.overlay_y,
            "overlay_locked": (self.overlay.locked if (self.overlay and self.overlay.win.winfo_exists()) else self.overlay_locked),
            "overlay_open": self.overlay is not None and self.overlay.win.winfo_exists(),
            "win_x": self.root.winfo_x(),
            "win_y": self.root.winfo_y(),
            "lang": self.lang,
        }
        json.dump(cfg, open(CONFIG_FILE, "w"))

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        BG    = "#0f0f1a"
        PANEL = "#16213e"
        CYAN  = "#00d4ff"
        WHITE = "#e0e0e0"
        GREY  = "#666"

        def lbl(parent, text, size=10, color=WHITE, bold=False):
            return tk.Label(parent, text=text, bg=BG, fg=color,
                            font=("Segoe UI", size, "bold" if bold else "normal"))

        def btn(parent, text, cmd, color="#0f3460", fg="white", size=10):
            return tk.Button(parent, text=text, command=cmd,
                             bg=color, fg=fg, relief="flat",
                             font=("Segoe UI", size, "bold"),
                             padx=12, pady=5, cursor="hand2",
                             activebackground=color)

        # En-tête : titre centré + sélecteur de langue en haut à droite
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x")

        self.lang_var = tk.StringVar(value="Français" if self.lang == "fr" else "English")
        lang_menu = tk.OptionMenu(hdr, self.lang_var, "Français", "English",
                                  command=self._on_lang_change)
        lang_menu.config(
            bg=PANEL, fg="#888", relief="flat",
            font=("Segoe UI", 8), bd=0,
            highlightthickness=0, padx=6, pady=3,
            activebackground=PANEL, activeforeground=WHITE,
        )
        lang_menu["menu"].config(
            bg=PANEL, fg=WHITE,
            activebackground=CYAN, activeforeground="#0f0f1a",
            font=("Segoe UI", 9),
        )
        lang_menu.pack(side="right", padx=8, pady=10)

        self._title_lbl = tk.Label(hdr, text=self._t("title"),
                                   bg=BG, fg=CYAN, font=("Segoe UI", 13, "bold"))
        self._title_lbl.pack(expand=True, pady=(18, 4))

        tk.Frame(self.root, bg=CYAN, height=1).pack(fill="x", padx=25)

        f = tk.Frame(self.root, bg=BG)
        f.pack(fill="x", padx=25, pady=12)
        f.columnconfigure(0, weight=1)

        # Marge
        self._lbl_margin = lbl(f, self._t("margin_label"))
        self._lbl_margin.grid(row=0, column=0, columnspan=2, sticky="w", pady=(6, 2))
        row0 = tk.Frame(f, bg=BG)
        row0.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Spinbox(
            row0, from_=0, to=5, textvariable=self.margin,
            width=4, justify="center", state="readonly",
            bg=PANEL, fg="#ff9f43",
            font=("Consolas", 12, "bold"), relief="flat", bd=6,
            buttonbackground=PANEL, command=self._save_config
        ).pack(side="left")
        self._lbl_margin_below = lbl(row0, self._t("margin_below"), 9, GREY)
        self._lbl_margin_below.pack(side="left")
        tk.Label(row0, textvariable=self.threshold_var,
                 bg=BG, fg=CYAN, font=("Consolas", 11, "bold")).pack(side="left")

        # Hotkey
        self._lbl_hotkey = lbl(f, self._t("hotkey_label"))
        self._lbl_hotkey.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 2))
        row2 = tk.Frame(f, bg=BG)
        row2.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.hotkey_lbl = tk.Label(row2, text=self.hotkey_name.upper(),
                                    bg=PANEL, fg=CYAN, width=8,
                                    font=("Consolas", 12, "bold"),
                                    relief="flat", padx=5, pady=4)
        self.hotkey_lbl.pack(side="left")
        self.hotkey_btn = btn(row2, self._t("btn_change"), self._change_hotkey)
        self.hotkey_btn.pack(side="left", padx=(8, 0))

        # Hotkey narco - label
        self._lbl_narco_hotkey = lbl(f, self._t("narco_hotkey_label"))
        self._lbl_narco_hotkey.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 2))
        # Hotkey narco - widgets
        row_narco_hotkey = tk.Frame(f, bg=BG)
        row_narco_hotkey.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.narco_hotkey_lbl = tk.Label(
            row_narco_hotkey, text=self.narco_hotkey_name.upper(),
            bg=PANEL, fg=CYAN, width=6,
            font=("Consolas", 11, "bold"), relief="flat", padx=5, pady=4)
        self.narco_hotkey_lbl.pack(side="left")
        self.narco_hotkey_btn = btn(row_narco_hotkey, self._t("btn_change"),
                                    self._change_narco_hotkey)
        self.narco_hotkey_btn.pack(side="left", padx=(8, 0))

        tk.Frame(f, bg="#2a2a3e", height=1).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10)

        # Ligne 1 : calibrations
        row2b = tk.Frame(f, bg=BG)
        row2b.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.calib_zone_btn = btn(row2b, self._t("btn_calib_zone"),
                                   self._calibrate_region, color="#e17055")
        self.calib_zone_btn.pack(side="left")
        self.calib_label_btn = btn(row2b, self._t("btn_calib_label"),
                                    self._calibrate_label_region,
                                    color="#636e72", size=9)
        self.calib_label_btn.pack(side="left", padx=(6, 0))

        # Ligne 1b : calibration icône narcotique + outils
        row2b2 = tk.Frame(f, bg=BG)
        row2b2.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.calib_narco_btn = btn(row2b2, "",
                                    self._calibrate_narco_icon_region,
                                    color="#6c3483", size=9)
        self.calib_narco_btn.pack(side="left")
        self._update_calib_narco_btn()
        self.test_ocr_btn = btn(row2b2, self._t("btn_test_ocr"),
                                 self._test_ocr, color="#533483", size=9)
        self.test_ocr_btn.pack(side="left", padx=(6, 0))
        self.overlay_btn = btn(row2b2, self._t("btn_overlay"),
                                self._toggle_overlay, color="#2d3436", size=9)
        self.overlay_btn.pack(side="left", padx=(6, 0))

        tk.Frame(f, bg="#2a2a3e", height=1).grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=10)

        # Statut
        row4 = tk.Frame(f, bg=BG)
        row4.grid(row=10, column=0, columnspan=2, sticky="ew")
        self._lbl_status = lbl(row4, self._t("status_label"))
        self._lbl_status.pack(side="left")
        self.status_lbl = tk.Label(row4, textvariable=self.status_var,
                                    bg=BG, fg="#ff6b6b",
                                    font=("Segoe UI", 11, "bold"))
        self.status_lbl.pack(side="left")
        tk.Label(row4, textvariable=self.countdown_var, bg=BG, fg="#ffd700",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(8, 0))

        row5 = tk.Frame(f, bg=BG)
        row5.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self._lbl_torpor = lbl(row5, self._t("torpor_label"))
        self._lbl_torpor.pack(side="left")
        tk.Label(row5, textvariable=self.torpor_var,
                 bg=BG, fg=CYAN, font=("Consolas", 14, "bold")).pack(side="left")

        row6 = tk.Frame(f, bg=BG)
        row6.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self._lbl_next_check = lbl(row6, self._t("next_check_label"), 9, GREY)
        self._lbl_next_check.pack(side="left")
        tk.Label(row6, textvariable=self.next_check_var, bg=BG, fg="#ffd700",
                 font=("Consolas", 9, "bold")).pack(side="left")

        row7 = tk.Frame(f, bg=BG)
        row7.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self._lbl_narco = lbl(row7, self._t("narco_label"), 9, GREY)
        self._lbl_narco.pack(side="left")
        tk.Label(row7, textvariable=self.narco_var, bg=BG, fg="#ff9f43",
                 font=("Consolas", 11, "bold")).pack(side="left")

        row8 = tk.Frame(f, bg=BG)
        row8.grid(row=14, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self._lbl_target = lbl(row8, self._t("target_label"), 9, GREY)
        self._lbl_target.pack(side="left")
        tk.Label(row8, textvariable=self.cible_var, bg=BG, fg="#a29bfe",
                 font=("Consolas", 11, "bold")).pack(side="left")

        row9 = tk.Frame(f, bg=BG)
        row9.grid(row=15, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._lbl_last_press = lbl(row9, self._t("last_press_label"), 9, GREY)
        self._lbl_last_press.pack(side="left")
        tk.Label(row9, textvariable=self.last_press_var, bg=BG, fg="#00b894",
                 font=("Consolas", 10, "bold")).pack(side="left")

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=14)
        self.main_btn = tk.Button(
            bf, text=f"{self._t('btn_start')}   ({self.hotkey_name.upper()})",
            command=self._toggle,
            bg="#00b894", fg="white", font=("Segoe UI", 13, "bold"),
            relief="flat", padx=24, pady=12, cursor="hand2",
            activebackground="#00a381"
        )
        self.main_btn.pack()

        self._lbl_footer = tk.Label(self.root,
                 text=self._t("footer"),
                 bg=BG, fg="#444", font=("Segoe UI", 8))
        self._lbl_footer.pack(pady=(0, 10))

    # ------------------------------------------------------------------ marge / position

    def _on_margin_change(self, *_):
        self._save_config()
        if self._torpor_max_live is not None:
            t = self._torpor_max_live - 40 - self.margin.get()
            self.threshold_var.set(f"{t:.0f}")

    def _on_win_move(self, event):
        if event.widget is self.root:
            if self._save_pos_job:
                self.root.after_cancel(self._save_pos_job)
            self._save_pos_job = self.root.after(500, self._save_config)

    # ------------------------------------------------------------------ overlay

    def _toggle_overlay(self):
        if self.overlay and self.overlay.win.winfo_exists():
            if self.overlay.locked:
                self.overlay.locked = False
                self.overlay_locked = False
                self.overlay.lock_lbl.config(text="🔓")
                self.overlay._apply_click_through(False)
                self._save_config()
                self._update_overlay_btn()
            else:
                self._hide_overlay()
        else:
            self._show_overlay()

    def _show_overlay(self):
        self.overlay = Overlay(self.root, self)
        self._update_overlay_btn()

    def _hide_overlay(self, save=True):
        if self.overlay and self.overlay.win.winfo_exists():
            self.overlay_locked = self.overlay.locked
            self.overlay_x = self.overlay.win.winfo_x()
            self.overlay_y = self.overlay.win.winfo_y()
            self.overlay.win.destroy()
        self.overlay = None
        self._update_overlay_btn()
        if save:
            self._save_config()

    def _update_overlay_btn(self):
        if not self.overlay or not self.overlay.win.winfo_exists():
            self.overlay_btn.config(text=self._t("btn_overlay"), bg="#2d3436", fg="white")
        elif self.overlay.locked:
            self.overlay_btn.config(text=self._t("btn_overlay_unlock"), bg="#e17055", fg="white")
        else:
            self.overlay_btn.config(text=self._t("btn_overlay_open"), bg="#00d4ff", fg="#0f0f1a")

    # ------------------------------------------------------------------ hotkey

    def _change_hotkey(self):
        self.hotkey_btn.config(state="disabled")
        self.hotkey_lbl.config(text="...", fg="#ffd700")
        try:
            keyboard.remove_hotkey(self.hotkey_name)
        except Exception:
            pass

        def wait():
            ev = keyboard.read_event(suppress=True)
            if ev.event_type == "down" and ev.name not in ("shift", "ctrl", "alt", "altgr"):
                self.hotkey_name = ev.name
                self.root.after(0, self._hotkey_updated)

        threading.Thread(target=wait, daemon=True).start()

    def _hotkey_updated(self):
        self.hotkey_lbl.config(text=self.hotkey_name.upper(), fg="#00d4ff")
        if not self.monitoring:
            self.main_btn.config(
                text=f"{self._t('btn_start')}   ({self.hotkey_name.upper()})")
        self.hotkey_btn.config(state="normal")
        self._register_hotkey()
        self._save_config()

    def _register_hotkey(self):
        try:
            keyboard.add_hotkey(self.hotkey_name, self._toggle)
        except Exception as e:
            print(f"Hotkey: {e}")
        try:
            keyboard.add_hotkey(self.narco_hotkey_name, self._trigger_narco_select)
        except Exception as e:
            print(f"Narco hotkey: {e}")

    def _change_narco_hotkey(self):
        self.narco_hotkey_btn.config(state="disabled")
        self.narco_hotkey_lbl.config(text="...", fg="#ffd700")
        try:
            keyboard.remove_hotkey(self.narco_hotkey_name)
        except Exception:
            pass

        def wait():
            ev = keyboard.read_event(suppress=True)
            if ev.event_type == "down" and ev.name not in ("shift", "ctrl", "alt", "altgr"):
                self.narco_hotkey_name = ev.name
                self.root.after(0, self._narco_hotkey_updated)

        threading.Thread(target=wait, daemon=True).start()

    def _narco_hotkey_updated(self):
        self.narco_hotkey_lbl.config(text=self.narco_hotkey_name.upper(), fg="#00d4ff")
        self.narco_hotkey_btn.config(state="normal")
        try:
            keyboard.add_hotkey(self.narco_hotkey_name, self._trigger_narco_select)
        except Exception as e:
            print(f"Narco hotkey: {e}")
        self._save_config()

    def _trigger_narco_select(self):
        self.root.after(0, self._calibrate_narco_icon_region)

    # ------------------------------------------------------------------ calibration

    def _calibrate_region(self):
        self.root.withdraw()
        self.root.after(150, self._open_selector)

    def _open_selector(self):
        def on_select(region):
            self.root.deiconify()
            if region:
                self.region = region
                self._save_config()
                messagebox.showinfo(
                    self._t("calib_zone_title"),
                    self._t("calib_zone_msg").format(
                        left=region["left"], top=region["top"],
                        width=region["width"], height=region["height"])
                )
            else:
                messagebox.showinfo(
                    self._t("calib_cancel_title"),
                    self._t("calib_cancel_msg"))
        RegionSelector(on_select)

    def _compute_default_label_region(self):
        return {
            "left": max(0, self.region["left"] - 145),
            "top": max(0, self.region["top"] - 2),
            "width": 140,
            "height": self.region["height"] + 4,
        }

    def _calibrate_label_region(self):
        messagebox.showinfo(
            self._t("calib_label_title"),
            self._t("calib_label_msg")
        )
        self.root.withdraw()
        self.root.after(150, self._open_label_selector)

    def _open_label_selector(self):
        def on_select(region):
            self.root.deiconify()
            if region:
                self.label_region = region
                self._save_config()
                messagebox.showinfo(
                    self._t("calib_label_done_title"),
                    self._t("calib_label_done_msg").format(
                        left=region["left"], top=region["top"],
                        width=region["width"], height=region["height"])
                )
            else:
                messagebox.showinfo(
                    self._t("calib_cancel_title"),
                    self._t("calib_cancel_msg"))
        RegionSelector(on_select)

    # ------------------------------------------------------------------ calibration icône narcotique

    def _update_calib_narco_btn(self):
        if self.narco_icon_region:
            nr = self.narco_icon_region
            self.calib_narco_btn.config(
                text=f"{self._t('btn_calib_narco')}  ✓  [{nr['width']}×{nr['height']}]",
                bg="#1e8449"
            )
        else:
            self.calib_narco_btn.config(
                text=self._t("btn_calib_narco"),
                bg="#6c3483"
            )

    def _calibrate_narco_icon_region(self):
        if self.narco_icon_region:
            if messagebox.askyesno(
                self._t("calib_narco_title"),
                ("Supprimer cette sélection ?" if self.lang == "fr"
                 else "Remove this selection?")
            ):
                self.narco_icon_region = None
                self._save_config()
                self._update_calib_narco_btn()
                messagebox.showinfo(
                    self._t("calib_narco_clear_title"),
                    self._t("calib_narco_clear_msg")
                )
            return

        messagebox.showinfo(
            self._t("calib_narco_title"),
            self._t("calib_narco_msg")
        )
        self.root.withdraw()
        self.root.after(150, self._open_narco_icon_selector)

    def _open_narco_icon_selector(self):
        def on_select(region):
            self.root.deiconify()
            if region:
                self.narco_icon_region = region
                self._save_config()
                self._update_calib_narco_btn()
                messagebox.showinfo(
                    self._t("calib_narco_done_title"),
                    self._t("calib_narco_done_msg").format(
                        left=region["left"], top=region["top"],
                        width=region["width"], height=region["height"])
                )
            else:
                messagebox.showinfo(
                    self._t("calib_cancel_title"),
                    self._t("calib_cancel_msg"))
        RegionSelector(on_select)

    # ------------------------------------------------------------------ test OCR

    def _test_ocr(self):
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_debug")
        raw_text, result = ocr.read_torpor_debug(self.region)

        if result is not None:
            torpor, torpor_max = result
            max_txt = f"{torpor_max:.1f}" if torpor_max else ("non lu" if self.lang == "fr" else "not read")
            messagebox.showinfo(
                self._t("ocr_title"),
                self._t("ocr_success").format(
                    torpor=torpor, max=max_txt, raw=raw_text.strip(), dir=debug_dir)
            )
        else:
            messagebox.showwarning(
                self._t("ocr_title"),
                self._t("ocr_fail").format(
                    raw=raw_text.strip(),
                    left=self.region["left"], top=self.region["top"],
                    width=self.region["width"], height=self.region["height"],
                    dir=debug_dir)
            )

    # ------------------------------------------------------------------ monitoring

    def _toggle(self):
        if self.monitoring:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.monitoring = True
        self.main_btn.config(text=self._t("btn_stop"), bg="#d63031",
                              activebackground="#c0392b")
        self._status_state = "starting"
        self.status_var.set(self._t("status_starting"))
        self.status_lbl.config(fg="#ffd700")
        self.action_var.set("")
        threading.Thread(target=self._loop, daemon=True).start()

    def _stop(self):
        self.monitoring = False
        self._status_state = "stopped"
        self.status_var.set(self._t("status_stopped"))
        self.countdown_var.set("")
        self.next_check_var.set("")
        self.narco_var.set("")
        self.cible_var.set("")
        self.last_press_var.set("—")
        self.threshold_var.set("—")
        self._torpor_max_live = None
        if self.overlay and self.overlay.win.winfo_exists():
            self.overlay.win.deiconify()
        self.status_lbl.config(fg="#ff6b6b")
        self.main_btn.config(
            text=f"{self._t('btn_start')}   ({self.hotkey_name.upper()})",
            bg="#00b894", activebackground="#00a381"
        )

    def _loop(self):
        for i in range(5, 0, -1):
            if not self.monitoring:
                return
            self.root.after(0, lambda v=i: self.countdown_var.set(f"({v}s)"))
            time.sleep(1)

        self.root.after(0, lambda: self.countdown_var.set(""))
        self._status_state = "active"
        self.root.after(0, lambda: self.status_var.set(self._t("status_active")))
        self.root.after(0, lambda: self.status_lbl.config(fg="#00b894"))

        prev_torpor = None
        no_read_streak = 0
        overlay_visible = True
        _HIDE_AFTER = 6

        while self.monitoring:
            result = ocr.read_torpor(self.region)

            if result is not None:
                torpor, torpor_max = result

                if torpor_max is not None:
                    self._torpor_max_live = torpor_max

                if torpor > 0:
                    no_read_streak = 0
                    if not overlay_visible and self.overlay and self.overlay.win.winfo_exists():
                        if ocr.is_taming_active(self.label_region):
                            self.root.after(0, self.overlay.win.deiconify)
                            overlay_visible = True
                else:
                    no_read_streak += 1

                self.root.after(0, lambda v=torpor: self.torpor_var.set(f"{v:.1f}"))

                threshold = (self._torpor_max_live - 40 - self.margin.get()
                             if self._torpor_max_live is not None else None)
                self.root.after(0, lambda v=threshold: self.threshold_var.set(
                    f"{v:.0f}" if v is not None else "—"))

                lecture_valide = (
                    torpor_max is not None
                    and torpor <= torpor_max
                    and torpor >= 0
                    and (prev_torpor is None or abs(torpor - prev_torpor) <= 60)
                )

                if lecture_valide and threshold is not None:
                    cible = torpor_max - self.margin.get()
                    nb_narco = max(0, math.ceil((cible - torpor) / 40))
                    self.root.after(0, lambda n=nb_narco: self.narco_var.set(str(n)))
                    self.root.after(0, lambda c=cible: self.cible_var.set(f"{c:.0f}"))

                    descend = prev_torpor is not None and torpor < prev_torpor
                    should_press = torpor <= threshold and descend and nb_narco > 0
                    if should_press and self.narco_icon_region is not None:
                        mx, my = pyautogui.position()
                        nr = self.narco_icon_region
                        should_press = (
                            nr["left"] <= mx <= nr["left"] + nr["width"]
                            and nr["top"] <= my <= nr["top"] + nr["height"]
                        )
                    if should_press:
                        pyautogui.press("e")
                        ts = time.strftime("%H:%M:%S")
                        self.root.after(0, lambda t=ts: self.last_press_var.set(
                            self._t("press_at_time").format(ts=t)))
                        prev_torpor = None
                    else:
                        self.root.after(0, lambda: self.action_var.set(""))
                        prev_torpor = torpor
                else:
                    prev_torpor = None
                    self.root.after(0, lambda: self.narco_var.set("—"))
                    self.root.after(0, lambda: self.cible_var.set("—"))
                    self.root.after(0, lambda: self.action_var.set(""))
            else:
                prev_torpor = None
                no_read_streak += 1
                self.root.after(0, lambda: self.torpor_var.set("?"))
                self.root.after(0, lambda: self.narco_var.set("—"))
                self.root.after(0, lambda: self.cible_var.set("—"))
                self.root.after(0, lambda: self.action_var.set(""))

            if no_read_streak >= _HIDE_AFTER:
                if overlay_visible and self.overlay and self.overlay.win.winfo_exists():
                    self.root.after(0, self.overlay.win.withdraw)
                    overlay_visible = False

            steps = 5
            step_duration = CHECK_INTERVAL / steps
            for i in range(steps, 0, -1):
                if not self.monitoring:
                    break
                remaining = i * step_duration
                self.root.after(0, lambda v=remaining: self.next_check_var.set(f"{v:.2f}s"))
                time.sleep(step_duration)
            self.root.after(0, lambda: self.next_check_var.set(""))

        self.root.after(0, self._stop)
