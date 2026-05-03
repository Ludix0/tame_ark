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

from constants import CONFIG_FILE, DEFAULT_HOTKEY, DEFAULT_REGION, CHECK_INTERVAL
from region_selector import RegionSelector
from overlay import Overlay
import ocr


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tame ARK — Auto Narcotique")
        self.root.geometry("430x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f1a")

        self.monitoring = False
        self.hotkey_name = DEFAULT_HOTKEY
        self.region = dict(DEFAULT_REGION)
        self.margin = tk.IntVar(value=3)
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

        self._load_config()
        if not self.label_region:
            self.label_region = self._compute_default_label_region()
        self._build_ui()
        self.root.geometry(f"+{self.win_x}+{self.win_y}")
        self.root.bind("<Configure>", self._on_win_move)
        self.margin.trace_add("write", self._on_margin_change)
        self._register_hotkey()

    # ------------------------------------------------------------------ config

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                cfg = json.load(open(CONFIG_FILE))
                self.hotkey_name = cfg.get("hotkey", DEFAULT_HOTKEY)
                self.margin.set(max(0, min(5, int(cfg.get("margin", 3)))))
                self.overlay_x = cfg.get("overlay_x", 50)
                self.overlay_y = cfg.get("overlay_y", 50)
                self.overlay_locked = cfg.get("overlay_locked", False)
                self.win_x = cfg.get("win_x", 100)
                self.win_y = cfg.get("win_y", 100)
                if "region" in cfg:
                    self.region = cfg["region"]
                if "label_region" in cfg:
                    self.label_region = cfg["label_region"]
            except Exception:
                pass

    def _save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        cfg = {
            "hotkey": self.hotkey_name,
            "margin": self.margin.get(),
            "region": self.region,
            "label_region": self.label_region,
            "overlay_x": self.overlay.win.winfo_x() if self.overlay else self.overlay_x,
            "overlay_y": self.overlay.win.winfo_y() if self.overlay else self.overlay_y,
            "overlay_locked": self.overlay_locked,
            "win_x": self.root.winfo_x(),
            "win_y": self.root.winfo_y(),
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

        tk.Label(self.root, text="TAME ARK — AUTO NARCOTIQUE",
                 bg=BG, fg=CYAN, font=("Segoe UI", 13, "bold")).pack(pady=(18, 4))
        tk.Frame(self.root, bg=CYAN, height=1).pack(fill="x", padx=20)

        f = tk.Frame(self.root, bg=BG)
        f.pack(fill="x", padx=25, pady=12)

        # Marge
        lbl(f, "Marge de déclenchement (torpeur max − N) :").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(6, 2))
        row0 = tk.Frame(f, bg=BG)
        row0.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Spinbox(
            row0, from_=0, to=5, textvariable=self.margin,
            width=4, justify="center", state="readonly",
            bg=PANEL, fg="#ff9f43",
            font=("Consolas", 12, "bold"), relief="flat", bd=6,
            buttonbackground=PANEL, command=self._save_config
        ).pack(side="left")
        lbl(row0, "  en dessous du max  →  appui à ", 9, GREY).pack(side="left")
        tk.Label(row0, textvariable=self.threshold_var,
                 bg=BG, fg=CYAN, font=("Consolas", 11, "bold")).pack(side="left")

        # Hotkey
        lbl(f, "Touche marche/arrêt :").grid(row=2, column=0, columnspan=2,
                                              sticky="w", pady=(0, 2))
        row2 = tk.Frame(f, bg=BG)
        row2.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.hotkey_lbl = tk.Label(row2, text=self.hotkey_name.upper(),
                                    bg=PANEL, fg=CYAN, width=8,
                                    font=("Consolas", 12, "bold"),
                                    relief="flat", padx=5, pady=4)
        self.hotkey_lbl.pack(side="left")
        self.hotkey_btn = btn(row2, "Changer", self._change_hotkey)
        self.hotkey_btn.pack(side="left", padx=(8, 0))

        # Ligne 1 : calibrations
        row2b = tk.Frame(f, bg=BG)
        row2b.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        btn(row2b, "Calibrer zone", self._calibrate_region, color="#e17055").pack(side="left")
        btn(row2b, "Calibrer label", self._calibrate_label_region,
            color="#636e72", size=9).pack(side="left", padx=(6, 0))

        # Ligne 2 : outils
        row2c = tk.Frame(f, bg=BG)
        row2c.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        btn(row2c, "Tester OCR", self._test_ocr, color="#533483").pack(side="left")
        self.overlay_btn = btn(row2c, "Overlay", self._toggle_overlay, color="#2d3436")
        self.overlay_btn.pack(side="left", padx=(6, 0))

        tk.Frame(f, bg="#2a2a3e", height=1).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10)

        # Statut
        row4 = tk.Frame(f, bg=BG)
        row4.grid(row=7, column=0, columnspan=2, sticky="ew")
        lbl(row4, "Statut : ").pack(side="left")
        self.status_lbl = tk.Label(row4, textvariable=self.status_var,
                                    bg=BG, fg="#ff6b6b",
                                    font=("Segoe UI", 11, "bold"))
        self.status_lbl.pack(side="left")
        tk.Label(row4, textvariable=self.countdown_var, bg=BG, fg="#ffd700",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(8, 0))

        row5 = tk.Frame(f, bg=BG)
        row5.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        lbl(row5, "Torpeur lue : ").pack(side="left")
        tk.Label(row5, textvariable=self.torpor_var,
                 bg=BG, fg=CYAN, font=("Consolas", 14, "bold")).pack(side="left")

        row6 = tk.Frame(f, bg=BG)
        row6.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        lbl(row6, "Prochain check : ", 9, GREY).pack(side="left")
        tk.Label(row6, textvariable=self.next_check_var, bg=BG, fg="#ffd700",
                 font=("Consolas", 9, "bold")).pack(side="left")

        row7 = tk.Frame(f, bg=BG)
        row7.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        lbl(row7, "Narcotiques à donner : ", 9, GREY).pack(side="left")
        tk.Label(row7, textvariable=self.narco_var, bg=BG, fg="#ff9f43",
                 font=("Consolas", 11, "bold")).pack(side="left")

        row8 = tk.Frame(f, bg=BG)
        row8.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        lbl(row8, "Cible torpeur : ", 9, GREY).pack(side="left")
        tk.Label(row8, textvariable=self.cible_var, bg=BG, fg="#a29bfe",
                 font=("Consolas", 11, "bold")).pack(side="left")

        row9 = tk.Frame(f, bg=BG)
        row9.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        lbl(row9, "Dernier appui E : ", 9, GREY).pack(side="left")
        tk.Label(row9, textvariable=self.last_press_var, bg=BG, fg="#00b894",
                 font=("Consolas", 10, "bold")).pack(side="left")

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=14)
        self.main_btn = tk.Button(
            bf, text=f"▶   DÉMARRER   ({self.hotkey_name.upper()})",
            command=self._toggle,
            bg="#00b894", fg="white", font=("Segoe UI", 13, "bold"),
            relief="flat", padx=24, pady=11, cursor="hand2",
            activebackground="#00a381"
        )
        self.main_btn.pack()

        tk.Label(self.root,
                 text="ARK doit être la fenêtre active pendant l'utilisation",
                 bg=BG, fg="#444", font=("Segoe UI", 8)).pack(pady=(0, 10))

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

    def _hide_overlay(self):
        if self.overlay and self.overlay.win.winfo_exists():
            self.overlay.win.destroy()
        self.overlay = None
        self.overlay_locked = False
        self._update_overlay_btn()

    def _update_overlay_btn(self):
        if not self.overlay or not self.overlay.win.winfo_exists():
            self.overlay_btn.config(text="Overlay", bg="#2d3436", fg="white")
        elif self.overlay.locked:
            self.overlay_btn.config(text="🔒 Déverrouiller", bg="#e17055", fg="white")
        else:
            self.overlay_btn.config(text="🔓 Overlay", bg="#00d4ff", fg="#0f0f1a")

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
        self.main_btn.config(text=f"▶   DÉMARRER   ({self.hotkey_name.upper()})")
        self.hotkey_btn.config(state="normal")
        self._register_hotkey()
        self._save_config()

    def _register_hotkey(self):
        try:
            keyboard.add_hotkey(self.hotkey_name, self._toggle)
        except Exception as e:
            print(f"Hotkey: {e}")

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
                    "Zone calibrée",
                    f"Zone enregistrée :\nx={region['left']}  y={region['top']}  "
                    f"{region['width']}×{region['height']}\n\n"
                    "Cliquez sur « Tester OCR » pour vérifier."
                )
            else:
                messagebox.showinfo("Calibration annulée", "La zone n'a pas été modifiée.")
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
            "Calibrer le label torpeur",
            "Sélectionnez uniquement le mot « Torpeur » (le label, pas les chiffres).\n\n"
            "Ouvrez l'inventaire d'une bête endormie dans ARK, puis cliquez OK."
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
                    "Label calibré",
                    f"Zone du label enregistrée :\n"
                    f"x={region['left']}  y={region['top']}  "
                    f"{region['width']}×{region['height']}\n\n"
                    "Cette zone est sauvegardée et sera rechargée au prochain démarrage."
                )
            else:
                messagebox.showinfo("Calibration annulée", "La zone n'a pas été modifiée.")
        RegionSelector(on_select)

    # ------------------------------------------------------------------ test OCR

    def _test_ocr(self):
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_debug")
        raw_text, result = ocr.read_torpor_debug(self.region)

        if result is not None:
            torpor, torpor_max = result
            max_txt = f"{torpor_max:.1f}" if torpor_max else "non lu"
            messagebox.showinfo(
                "Test OCR",
                f"Torpeur actuelle : {torpor:.1f}\nTorpeur max : {max_txt}\n\n"
                f"Texte brut OCR : «{raw_text.strip()}»\n\n"
                f"Images debug sauvegardées dans :\n{debug_dir}"
            )
        else:
            messagebox.showwarning(
                "Test OCR",
                f"Aucune valeur numérique détectée.\n\n"
                f"Texte brut OCR : «{raw_text.strip()}»\n\n"
                f"Zone capturée : x={self.region['left']} y={self.region['top']} "
                f"{self.region['width']}×{self.region['height']}\n\n"
                f"Images debug sauvegardées dans :\n{debug_dir}\n\n"
                "Ouvrez ocr_debug\\capture_raw.png pour vérifier que la zone est correcte."
            )

    # ------------------------------------------------------------------ monitoring

    def _toggle(self):
        if self.monitoring:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.monitoring = True
        self.main_btn.config(text="⏹   ARRÊTER", bg="#d63031",
                              activebackground="#c0392b")
        self.status_var.set("Démarrage…")
        self.status_lbl.config(fg="#ffd700")
        self.action_var.set("")
        threading.Thread(target=self._loop, daemon=True).start()

    def _stop(self):
        self.monitoring = False
        self.status_var.set("Arrêté")
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
            text=f"▶   DÉMARRER   ({self.hotkey_name.upper()})",
            bg="#00b894", activebackground="#00a381"
        )

    def _loop(self):
        for i in range(5, 0, -1):
            if not self.monitoring:
                return
            self.root.after(0, lambda v=i: self.countdown_var.set(f"({v}s)"))
            time.sleep(1)

        self.root.after(0, lambda: self.countdown_var.set(""))
        self.root.after(0, lambda: self.status_var.set("Actif ✓"))
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
                    if torpor <= threshold and descend and nb_narco > 0:
                        pyautogui.press("e")
                        ts = time.strftime("%H:%M:%S")
                        self.root.after(0, lambda t=ts: self.last_press_var.set(f"E  à {t}"))
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
