# Einmaliges Einrichten unter Windows.
# Doppelklick auf Einrichten.cmd, oder in PowerShell im Repo-Ordner:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ""
Write-Host "=== humbee-manual-demo einrichten ===" -ForegroundColor Cyan
Write-Host ""

# --- 1: geschuetzte Ordner befuellen ---------------------------------------
# .vscode, .claude und .github koennen von aussen nicht beschrieben werden.
# Die Dateien liegen deshalb unter setup\ und werden hier einsortiert.
Write-Host "1/4  Konfiguration einsortieren..." -ForegroundColor Cyan
$paare = @(
    @{ Von = "setup\vscode";           Nach = ".vscode" },
    @{ Von = "setup\claude\commands";  Nach = ".claude\commands" },
    @{ Von = "setup\github\workflows"; Nach = ".github\workflows" }
)
foreach ($p in $paare) {
    if (Test-Path $p.Von) {
        New-Item -ItemType Directory -Force -Path $p.Nach | Out-Null
        Copy-Item "$($p.Von)\*" $p.Nach -Recurse -Force
        Write-Host "     $($p.Von)  ->  $($p.Nach)" -ForegroundColor Green
    }
}
if (Test-Path "setup") {
    Remove-Item "setup" -Recurse -Force
    Write-Host "     setup\ entfernt" -ForegroundColor Green
}

# --- 2: Python -------------------------------------------------------------
Write-Host ""
Write-Host "2/4  Python-Abhaengigkeiten..." -ForegroundColor Cyan
python -m pip install --quiet -r requirements.txt
Write-Host "     PyYAML und requests installiert" -ForegroundColor Green

# --- 3: Git ----------------------------------------------------------------
Write-Host ""
Write-Host "3/4  Git-Repository..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) {
    git init -b main | Out-Null
    Write-Host "     Repository angelegt" -ForegroundColor Green
}
git add -A
if (git status --porcelain) {
    git commit -q -m "Demo-Aufbau: eine Quelle, zwei Auslieferungen"
    Write-Host "     Erster Commit erstellt" -ForegroundColor Green
} else {
    Write-Host "     Nichts zu committen" -ForegroundColor Yellow
}

# --- 4: Werkzeuge ----------------------------------------------------------
Write-Host ""
Write-Host "4/4  Werkzeuge pruefen..." -ForegroundColor Cyan
$fehlt = @()
foreach ($t in @("python", "git", "pandoc", "quarto")) {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Write-Host "     $t gefunden" -ForegroundColor Green
    } else {
        Write-Host "     $t fehlt" -ForegroundColor Yellow
        $fehlt += $t
    }
}

Write-Host ""
if ($fehlt -contains "quarto" -and $fehlt -contains "pandoc") {
    Write-Host "Fuer das PDF fehlt noch ein Werkzeug:" -ForegroundColor Yellow
    Write-Host "  winget install Posit.Quarto      (empfohlen, bringt LaTeX mit)"
    Write-Host "  winget install JohnMacFarlane.Pandoc   (Alternative)"
    Write-Host ""
}
Write-Host "Fertig. Naechste Schritte:" -ForegroundColor Cyan
Write-Host "  python scripts\validate.py"
Write-Host "  python scripts\build_wiki.py"
Write-Host "  python scripts\build_print.py"
Write-Host ""
