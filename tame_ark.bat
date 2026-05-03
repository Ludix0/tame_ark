@echo off
cd /d "%~dp0"
echo Demarrage de Tame ARK...
py tame_ark.py
if errorlevel 1 (
    echo.
    echo L application s est fermee avec une erreur.
    if exist error.log (
        echo.
        echo === Contenu de error.log ===
        type error.log
    )
    echo.
    pause
)