# Build script para gerar executável desktop (Windows)
# Requisitos: Python 3.11+, PowerShell, acesso à internet para instalar dependências

param(
    [string]$Name = "FTTH-KML-Viewer",
    [string]$Icon = "icon.ico"
)

Write-Host "==> Preparando ambiente (venv recomendado)" -ForegroundColor Cyan

# Instalar dependências do projeto
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Instalar bibliotecas de build e janela desktop
python -m pip install pywebview pyinstaller

Write-Host "==> Limpando builds anteriores" -ForegroundColor Cyan
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Remove-Item -Force "$Name.spec" -ErrorAction SilentlyContinue

Write-Host "==> Gerando executável (modo janela, sem console)" -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean --windowed `
  --name "$Name" `
  --icon "$Icon" `
  --add-data "static;static" `
  --add-data "templates;templates" `
  --add-data "Mapas;Mapas" `
  ftth_kml_app.py

Write-Host "==> Concluído. Executável disponível em: dist/$Name/$Name.exe" -ForegroundColor Green
Write-Host "Se ao abrir o executável nenhuma janela aparecer, instale o 'Microsoft Edge WebView2 Runtime' e tente novamente." -ForegroundColor Yellow