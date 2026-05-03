# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Objectif du projet

Application Windows (Python + tkinter) qui automatise l'administration de narcotiques lors de l'apprivoisement d'un animal dans ARK: Survival Ascended. Elle surveille la valeur de torpeur via OCR sur une zone de l'écran et appuie automatiquement sur **E** quand la torpeur descend sous le seuil configuré.

## Lancer l'application

```bat
# Avec fenêtre console (débogage)
tame_ark.bat

# Sans console (usage normal)
Lancer Tame ARK.vbs
```

Ou directement :
```bash
py tame_ark.py
```

## Installation des dépendances

```bat
install.bat
```

Ce script (`_setup.ps1`) installe les modules pip (`mss`, `Pillow`, `pytesseract`, `pyautogui`, `keyboard`) et Tesseract OCR via winget si absent.

## Architecture — fichiers

| Fichier | Rôle |
|---|---|
| `tame_ark.py` | Point d'entrée : vérification des dépendances, localisation de Tesseract, lancement de l'app |
| `app.py` | Classe `App` : UI tkinter, config, hotkey, calibration, boucle de monitoring |
| `ocr.py` | Fonctions OCR pures : `read_torpor`, `is_taming_active`, `read_torpor_debug` |
| `overlay.py` | Classe `Overlay` (fenêtre in-game) + constantes et helpers Win32 |
| `region_selector.py` | Classe `RegionSelector` : overlay plein écran pour sélectionner une zone par cliquer-glisser |
| `constants.py` | Constantes globales : `CONFIG_FILE`, `TESSERACT_PATHS`, `DEFAULT_HOTKEY`, `CHECK_INTERVAL`, `DEFAULT_REGION` |

## Classe App (`app.py`)

Responsabilités :
- `_load_config` / `_save_config` : persistance dans `config.json`
- `_build_ui` : construction de l'interface tkinter
- `_loop` (thread daemon) : boucle de monitoring — capture écran → OCR → décision → action
- `_toggle` / `_start` / `_stop` : gestion démarrage/arrêt
- `_register_hotkey` / `_change_hotkey` : gestion de la touche clavier globale
- `_calibrate_region` / `_calibrate_label_region` : sélection des zones OCR à l'écran
- `_on_win_move` : sauvegarde automatique de la position de la fenêtre (debounce 500 ms)

## Pipeline OCR (`ocr.py`)

Trois fonctions exposées :

**`read_torpor(region)`** — lecture normale (utilisée dans la boucle) :
1. Capture la région avec **mss**
2. Redimensionne ×3, augmente contraste et netteté via **Pillow**
3. Passe en niveaux de gris
4. Extrait le texte avec **pytesseract** (PSM 7, chiffres/points/slash uniquement)
5. Parse le format `"current / max"` (regex), fallback sur premier nombre trouvé

**`is_taming_active(label_region)`** — détecte si l'UI de tam est visible :
- Capture la zone du label « Torpeur » (calibrée séparément)
- OCR sans whitelist, cherche le mot « torpeur » ou « torpor »
- Utilisé pour éviter que l'overlay réapparaisse sur de fausses lectures hors inventaire

**`read_torpor_debug(region)`** — comme `read_torpor` mais sauvegarde les images dans `ocr_debug/`

## Logique de déclenchement (`App._loop`)

L'appui sur E n'est déclenché que si **toutes** ces conditions sont vraies :
- `torpeur_actuelle ≤ seuil`
- La torpeur **descend** (comparé à la lecture précédente)
- `nb_narco > 0` (il manque effectivement de la torpeur)
- La lecture est validée (sanity checks : `torpeur ≤ max`, variation ≤ 60 entre deux lectures)

Après un appui, `prev_torpor` est remis à `None` pour forcer deux lectures consécutives avant un nouvel appui.

### Auto-masquage de l'overlay

- Après `_HIDE_AFTER` cycles sans torpeur valide → `overlay.win.withdraw()`
- Réapparition uniquement si `torpor > 0` **ET** `is_taming_active()` retourne `True`
- Empêche les faux réaffichages quand l'OCR lit accidentellement un nombre hors inventaire

### Seuil de déclenchement

`torpor_max − 40 − margin` où `margin` est un entier configurable (Spinbox, 0–5). Sauvegardé dans la config.

### Threading

La boucle tourne dans un **thread daemon** pour ne pas bloquer l'UI tkinter. Toutes les mises à jour de l'interface se font via `root.after(0, lambda: ...)` pour rester thread-safe.

## Configuration persistée

Chemin : `%APPDATA%\TameARK\config.json` (créé automatiquement).

```json
{
  "hotkey": "f6",
  "margin": 3,
  "region": {"left": 975, "top": 664, "width": 120, "height": 23},
  "label_region": {"left": 830, "top": 662, "width": 140, "height": 27},
  "overlay_x": 50,
  "overlay_y": 50,
  "overlay_locked": false,
  "win_x": 100,
  "win_y": 100
}
```

- `region` : zone de capture des chiffres de torpeur (calibrable via « Calibrer zone »)
- `label_region` : zone du label « Torpeur » (calibrable via « Calibrer label »), calculée automatiquement si absente
- `win_x` / `win_y` : position de la fenêtre principale, sauvegardée automatiquement au déplacement

## Dépendances externes

| Outil | Rôle |
|---|---|
| `mss` | Capture d'écran rapide |
| `Pillow` | Traitement d'image |
| `pytesseract` | OCR (nécessite Tesseract installé séparément) |
| `pyautogui` | Simulation de touche clavier (`press("e")`) |
| `keyboard` | Hotkey global (fonctionne même si ARK est en avant-plan) |
| Tesseract OCR | Binaire externe, cherché dans les chemins standards Program Files |
