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
