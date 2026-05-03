# -*- coding: utf-8 -*-
"""Pipeline OCR : lecture de la torpeur et détection du label à l'écran."""
import re
import os

import mss
from PIL import Image, ImageEnhance
import pytesseract


def _preprocess(img, sharpness=False):
    """Redimensionne ×3, augmente le contraste, optionnellement la netteté, passe en niveaux de gris."""
    img = img.resize((img.width * 3, img.height * 3), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(3.0)
    if sharpness:
        img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img.convert("L")


def _capture(region):
    with mss.mss() as sct:
        raw = sct.grab(region)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def _parse_torpor(text):
    """Extrait (actuelle, max) ou (actuelle, None) depuis le texte OCR."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if nums:
        return float(nums[0]), None
    return None


def read_torpor(region):
    """Retourne (torpeur_actuelle, torpeur_max) ou None si lecture impossible."""
    try:
        img = _preprocess(_capture(region), sharpness=True)
        text = pytesseract.image_to_string(
            img, config="--psm 7 -c tessedit_char_whitelist=0123456789./ "
        )
        return _parse_torpor(text)
    except Exception as e:
        print(f"OCR error: {e}")
        return None


def is_taming_active(label_region):
    """Retourne True si le label 'Torpeur' est visible dans la zone calibrée."""
    try:
        img = _preprocess(_capture(label_region))
        text = pytesseract.image_to_string(img, config="--psm 7")
        return "torpeur" in text.lower() or "torpor" in text.lower()
    except Exception:
        return False


def read_torpor_debug(region):
    """Comme read_torpor mais sauvegarde les images dans ocr_debug/ et retourne le texte brut."""
    try:
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_debug")
        os.makedirs(debug_dir, exist_ok=True)

        raw_img = _capture(region)
        raw_img.save(os.path.join(debug_dir, "capture_raw.png"))

        proc_img = _preprocess(raw_img, sharpness=True)
        proc_img.save(os.path.join(debug_dir, "capture_processed.png"))

        text = pytesseract.image_to_string(
            proc_img, config="--psm 7 -c tessedit_char_whitelist=0123456789./"
        )
        result = _parse_torpor(text)
        return text, result
    except Exception as e:
        return f"[erreur: {e}]", None
