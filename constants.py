# -*- coding: utf-8 -*-
import os

_appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
CONFIG_FILE = os.path.join(_appdata, "TameARK", "config.json")

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]

DEFAULT_HOTKEY       = "f6"
DEFAULT_NARCO_HOTKEY = "f7"
CHECK_INTERVAL  = 0.075
DEFAULT_REGION  = {"left": 975, "top": 664, "width": 120, "height": 23}
