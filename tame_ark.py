# -*- coding: utf-8 -*-
"""Point d'entrée : vérification des dépendances puis lancement de l'application."""
import tkinter as tk
from tkinter import messagebox
import sys
import os
import ctypes

# Vérification des dépendances avant tout import interne
MISSING = []
try:
    import mss
    from PIL import Image, ImageEnhance
except ImportError:
    MISSING.append("mss Pillow")
try:
    import pytesseract
except ImportError:
    MISSING.append("pytesseract")
try:
    import pyautogui
except ImportError:
    MISSING.append("pyautogui")
try:
    import keyboard
except ImportError:
    MISSING.append("keyboard")

if MISSING:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Modules manquants",
        f"Lancez install.bat pour installer les dépendances manquantes :\n{', '.join(MISSING)}"
    )
    root.destroy()
    sys.exit(1)

from constants import TESSERACT_PATHS
from app import App


def main():
    import traceback

    # Localisation de Tesseract
    found = False
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            found = True
            print(f"Tesseract : {path}")
            break

    if not found:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Tesseract introuvable",
            "Tesseract OCR est introuvable.\nRelancez install.bat pour l'installer."
        )
        root.destroy()
        sys.exit(1)

    pyautogui.FAILSAFE = False

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TameARK.Narcotic.1")

        root = tk.Tk()
        ico = os.path.join(os.path.dirname(__file__), "64x64px-Narcotic.ico")
        if os.path.exists(ico):
            root.iconbitmap(ico)
        app = App(root)

        def on_close():
            app._save_config()
            app._hide_overlay(save=False)
            app.monitoring = False
            try:
                keyboard.unhook_all()
            except Exception:
                pass
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()

    except Exception:
        err = traceback.format_exc()
        print("\n=== ERREUR ===")
        print(err)
        log_path = os.path.join(os.path.dirname(__file__), "error.log")
        with open(log_path, "w") as f:
            f.write(err)
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("Erreur", f"L'application a planté :\n\n{err}\n\nDétails dans error.log")
            r.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
