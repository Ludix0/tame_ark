$Host.UI.RawUI.WindowTitle = "Installation — Tame ARK"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Installation — Tame ARK Auto Narcotique  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Python ---
Write-Host "[1/2] Verification de Python..." -ForegroundColor Yellow
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERREUR : Python n'est pas installe." -ForegroundColor Red
    Write-Host "Telechargez-le sur https://python.org puis relancez install.bat" -ForegroundColor Red
    Read-Host "`nAppuyez sur Entree pour quitter"
    exit 1
}
$ver = & py --version 2>&1
Write-Host "      OK : $ver" -ForegroundColor Green

Write-Host ""
Write-Host "[2/2] Installation des modules Python..." -ForegroundColor Yellow
Write-Host "      (patience, chaque module peut prendre 1-2 minutes)" -ForegroundColor Gray
$modules = @("mss", "Pillow", "pytesseract", "pyautogui", "keyboard")
$ok = $true
foreach ($mod in $modules) {
    Write-Host "      -> $mod ..." -NoNewline -ForegroundColor White
    $out = & py -m pip install --timeout 120 --retries 3 --upgrade $mod 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " ERREUR" -ForegroundColor Red
        Write-Host $out -ForegroundColor Red
        $ok = $false
    }
}
if (-not $ok) {
    Read-Host "`nAppuyez sur Entree pour quitter"
    exit 1
}
Write-Host "      Tous les modules sont installes" -ForegroundColor Green

Write-Host ""
Write-Host "[3/3] Verification de Tesseract OCR..." -ForegroundColor Yellow
$tessPaths = @(
    "C:\Program Files\Tesseract-OCR\tesseract.exe",
    "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe"
)
$tess = $tessPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($tess) {
    $tessver = & $tess --version 2>&1 | Select-Object -First 1
    Write-Host "      OK : $tessver" -ForegroundColor Green
    Write-Host "      Chemin : $tess" -ForegroundColor Gray
} else {
    Write-Host "      Tesseract absent, installation via winget..." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Host "ERREUR : winget non disponible." -ForegroundColor Red
        Write-Host "Installez Tesseract manuellement depuis :" -ForegroundColor Red
        Write-Host "https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
        Read-Host "`nAppuyez sur Entree pour quitter"
        exit 1
    }
    Write-Host "      Lancement de winget (une fenetre peut s'ouvrir)..." -ForegroundColor Yellow
    winget install --id UB-Mannheim.TesseractOCR -e --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERREUR : echec installation Tesseract." -ForegroundColor Red
        Read-Host "`nAppuyez sur Entree pour quitter"
        exit 1
    }
    $tess = $tessPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($tess) {
        Write-Host "      OK : Tesseract installe avec succes" -ForegroundColor Green
    } else {
        Write-Host "ATTENTION : chemin de Tesseract introuvable apres installation." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Installation terminee avec succes !      " -ForegroundColor Green
Write-Host "   Lancez tame_ark.bat pour demarrer.       " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Appuyez sur Entree pour fermer"