[README.md](https://github.com/user-attachments/files/27362757/README.md)
# Tame ARK — Auto Narcotic

Windows tool that automates narcotic administration when taming animals in **ARK: Survival Ascended**.

---

## What is it for?

When taming an animal by knocking it out in ARK, you must regularly give it narcotics to keep its torpor high enough and prevent it from waking up. This process can last several tens of minutes and requires constant monitoring.

**Tame ARK** watches the torpor bar for you and automatically presses `E` (force-feed) at the right moment, without you needing to leave the animal's inventory.

---

## How it works

### Torpor reading

The application continuously captures a small screen region (the torpor row in the animal's inventory) and reads the values via OCR (optical character recognition). The displayed value follows the format `current / maximum`, for example `423.5 / 499.0`.

### Trigger logic

The `E` press is triggered only if **all** of these conditions are met:

| Condition | Detail |
|---|---|
| Torpor ≤ threshold | `torpor_max − 40 − margin` |
| Torpor is decreasing | two consecutive readings confirm the drop |
| Narcotics needed | the calculation indicates at least 1 narcotic is missing |
| Valid reading | value within bounds, realistic variation between readings |

After each press, the tool waits for a new confirmed drop before pressing again, preventing any burst-pressing.

### Threshold and safety margin

- **Press threshold** = `torpor_max − 40 − margin`
- **Torpor target** (level aimed at after the narcotic) = `torpor_max − margin`
- The **margin** is adjustable from 0 to 5 directly in the interface

*Example with torpor_max = 200 and margin = 3:*
- Press triggered at **157** (200 − 40 − 3)
- Target: **197** (200 − 3)

### Automatic context detection

When you close an animal's inventory or switch to another one, the tool detects it automatically (no valid reading) and resets its internal state. It is ready to act as soon as you open the next animal's inventory.

---

## Interface

| Element | Role |
|---|---|
| **Trigger margin** | Adjusts the distance from the max (0 to 5) |
| **Press at** | Exact torpor value that will trigger the press (updated in real time) |
| **Start/stop key** | Configurable global hotkey (works even when ARK is in the foreground) |
| **Calibrate zone** | Select the screen region where torpor numbers are read |
| **Calibrate label** | Select the region where the word "Torpor" appears (used for overlay auto-hiding) |
| **Test OCR** | Verifies that the reading zone captures values correctly, saves debug images |
| **Overlay** | Displays a transparent mini-panel above the game |
| **Start / Stop** | Starts or stops monitoring (also accessible via the configured hotkey) |

### Overlay

The mini-overlay stays above ARK and displays torpor, the press threshold, and the time of the last `E` press in real time.

- 🔓 **Unlocked**: draggable with the mouse
- 🔒 **Locked**: clicks pass through to ARK (click-through), keyboard focus stays on the game
- **Auto-hides** when you are not in a knocked-out animal's inventory
- **Reappears** as soon as you open a sleeping creature's inventory — only if the "Torpor" label is detected, to avoid false re-displays

To unlock the overlay from the game: click the **🔒 Unlock** button in the main window.

---

## Installation

### Requirements

- Windows 10 / 11
- Python 3.x — [python.org](https://www.python.org/)

### Steps

1. Download or clone this repository
2. Double-click **`install.bat`**
   - Installs the required Python modules (`mss`, `Pillow`, `pytesseract`, `pyautogui`, `keyboard`)
   - Installs Tesseract OCR automatically via winget if missing

### Launch

| File | Usage |
|---|---|
| `Lancer Tame ARK.vbs` | Normal launch (no console) |
| `tame_ark.bat` | Launch with console (useful for seeing errors) |

---

## Calibration (first use or new PC)

The reading zone must be calibrated once to match your screen resolution.

1. Launch ARK and open the inventory of a knocked-out creature
2. In the application, click **Calibrate zone** and draw around the torpor numbers (e.g. `423.5 / 499.0`)
3. Click **Calibrate label** and draw around only the word "Torpor" to the left of the numbers
4. Click **Test OCR** to verify that reading works correctly

Both zones are saved in the configuration and automatically reloaded on next startup.

---

## Configuration

The configuration is automatically saved in:
```
%APPDATA%\TameARK\config.json
```

It contains the hotkey, the margin, the calibrated zones, and the window positions. The main window position is also saved automatically when you move it.

---

## Dependencies

| Tool | Role |
|---|---|
| [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) | Text recognition engine |
| [mss](https://python-mss.readthedocs.io/) | Fast screen capture |
| [Pillow](https://python-pillow.org/) | Image processing (contrast, sharpness) |
| [pytesseract](https://github.com/madmaze/pytesseract) | Python interface for Tesseract |
| [pyautogui](https://pyautogui.readthedocs.io/) | Keyboard key simulation |
| [keyboard](https://github.com/boppreh/keyboard) | Global hotkey (driver-level) |

---

## Notes

- ARK must be in **windowed** or **borderless windowed** mode for the capture zone to match the configured screen position.
- The tool does not inject anything into the game: it reads the screen and simulates a key press, exactly as a player would.

---

---

# Tame ARK — Auto Narcotique

Outil Windows qui automatise l'administration de narcotiques lors de l'apprivoisement d'animaux dans **ARK: Survival Ascended**.

---

## À quoi ça sert ?

Quand tu apprivoises un animal en le massommant dans ARK, tu dois régulièrement lui donner des narcotiques pour maintenir sa torpeur assez haute et éviter qu'il se réveille. Ce processus peut durer plusieurs dizaines de minutes et nécessite une surveillance constante.

**Tame ARK** surveille la barre de torpeur à ta place et appuie automatiquement sur `E` (forcer-nourrir) au bon moment, sans que tu aies besoin de quitter l'inventaire de l'animal.

---

## Fonctionnement

### Lecture de la torpeur

L'application capture en permanence une petite zone de l'écran (la ligne torpeur dans l'inventaire de l'animal) et y lit les valeurs via OCR (reconnaissance optique de caractères). La valeur affichée suit le format `actuelle / maximum`, par exemple `423.5 / 499.0`.

### Logique de déclenchement

L'appui sur `E` se déclenche uniquement si **toutes** ces conditions sont réunies :

| Condition | Détail |
|---|---|
| Torpeur ≤ seuil | `torpeur_max − 40 − marge` |
| Torpeur en baisse | deux lectures consécutives confirment la descente |
| Narcotiques nécessaires | le calcul indique qu'au moins 1 narcotique manque |
| Lecture cohérente | valeur dans les bornes, variation réaliste entre lectures |

Après chaque appui, l'outil attend une nouvelle descente confirmée avant de ré-appuyer, évitant tout appui en rafale.

### Seuil et marge de sécurité

- **Seuil d'appui** = `torpeur_max − 40 − marge`
- **Cible torpeur** (niveau visé après le narcotique) = `torpeur_max − marge`
- La **marge** est réglable de 0 à 5 directement dans l'interface

*Exemple avec torpeur_max = 200 et marge = 3 :*
- Appui déclenché à **157** (200 − 40 − 3)
- Cible visée : **197** (200 − 3)

### Détection automatique du contexte

Quand tu fermes l'inventaire d'un animal ou que tu passes à un autre, l'outil le détecte automatiquement (plus de lecture valide) et réinitialise son état interne. Il est prêt à agir dès que tu ouvres l'inventaire du prochain animal.

---

## Interface

| Élément | Rôle |
|---|---|
| **Marge de déclenchement** | Réglage de la distance par rapport au max (0 à 5) |
| **Appui à** | Valeur de torpeur exacte qui déclenchera l'appui (mis à jour en temps réel) |
| **Touche marche/arrêt** | Hotkey global configurable (fonctionne même si ARK est en avant-plan) |
| **Calibrer zone** | Sélectionne la zone de l'écran où lire les chiffres de torpeur |
| **Calibrer label** | Sélectionne la zone où apparaît le mot « Torpeur » (utilisé pour l'auto-masquage de l'overlay) |
| **Tester OCR** | Vérifie que la zone de lecture capte bien les valeurs, sauvegarde des images de débogage |
| **Overlay** | Affiche un mini-panneau transparent au-dessus du jeu |
| **Démarrer / Arrêter** | Lance ou stoppe la surveillance (aussi accessible via le hotkey configuré) |

### Overlay

Le mini-overlay reste au-dessus d'ARK et affiche en temps réel la torpeur, le seuil d'appui et l'heure du dernier appui `E`.

- 🔓 **Déverrouillé** : déplaçable à la souris
- 🔒 **Verrouillé** : les clics passent au travers vers ARK (click-through), le focus clavier reste sur le jeu
- **Se cache automatiquement** quand tu n'es pas dans l'inventaire d'un animal endormi
- **Réapparaît** dès que tu ouvres l'inventaire d'une bête endormie — uniquement si le label « Torpeur » est détecté, pour éviter les faux réaffichages

Pour déverrouiller l'overlay depuis le jeu : cliquer sur le bouton **🔒 Déverrouiller** dans la fenêtre principale.

---

## Installation

### Prérequis

- Windows 10 / 11
- Python 3.x — [python.org](https://www.python.org/)

### Étapes

1. Télécharger ou cloner ce dépôt
2. Double-cliquer sur **`install.bat`**
   - Installe les modules Python nécessaires (`mss`, `Pillow`, `pytesseract`, `pyautogui`, `keyboard`)
   - Installe Tesseract OCR automatiquement via winget si absent

### Lancement

| Fichier | Usage |
|---|---|
| `Lancer Tame ARK.vbs` | Lancement normal (pas de console) |
| `tame_ark.bat` | Lancement avec console (utile pour voir les erreurs) |

---

## Calibration (première utilisation ou nouveau PC)

La zone de lecture doit être calibrée une fois pour correspondre à ta résolution d'écran.

1. Lance ARK et ouvre l'inventaire d'une bête endormie
2. Dans l'application, clique sur **Calibrer zone** et entoure les chiffres de torpeur (ex: `423.5 / 499.0`)
3. Clique sur **Calibrer label** et entoure uniquement le mot « Torpeur » à gauche des chiffres
4. Clique sur **Tester OCR** pour vérifier que la lecture fonctionne

Les deux zones sont sauvegardées dans la configuration et rechargées automatiquement au prochain démarrage.

---

## Configuration

La configuration est sauvegardée automatiquement dans :
```
%APPDATA%\TameARK\config.json
```

Elle contient la touche hotkey, la marge, les zones calibrées, et les positions des fenêtres. La position de la fenêtre principale est également mémorisée automatiquement quand tu la déplaces.

---

## Dépendances

| Outil | Rôle |
|---|---|
| [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) | Moteur de reconnaissance de texte |
| [mss](https://python-mss.readthedocs.io/) | Capture d'écran rapide |
| [Pillow](https://python-pillow.org/) | Traitement d'image (contraste, netteté) |
| [pytesseract](https://github.com/madmaze/pytesseract) | Interface Python pour Tesseract |
| [pyautogui](https://pyautogui.readthedocs.io/) | Simulation de touche clavier |
| [keyboard](https://github.com/boppreh/keyboard) | Hotkey global (driver-level) |

---

## Notes

- ARK doit être en **fenêtre** ou **fenêtre sans bordure** pour que la zone de capture corresponde à l'écran configuré.
- L'outil n'injecte rien dans le jeu : il lit l'écran et simule une pression de touche, exactement comme le ferait un joueur.

---

*Fait par IA.*
