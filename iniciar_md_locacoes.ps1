# ============================================================
# MD Locacoes - Iniciar Servidor
# Execute este arquivo para iniciar o sistema completo.
# Ele inicia o app + tunnel e atualiza o link automaticamente.
# ============================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   MD LOCACOES - Iniciando servidor..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Mata processos antigos
Write-Host "[1/5] Parando processos antigos..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Inicia o Flask
Write-Host "[2/5] Iniciando aplicativo Flask..." -ForegroundColor Yellow
$locacaoDir = "C:\Users\netho\OneDrive\Desktop\LocacaoMD"
Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $locacaoDir -WindowStyle Minimized
Start-Sleep -Seconds 3

# Verifica se Flask subiu
try {
    $r = Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing -TimeoutSec 5
    Write-Host "  Flask OK! (http://localhost:5000)" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Flask nao subiu!" -ForegroundColor Red
    exit 1
}

# 3. Inicia o tunnel Cloudflare
Write-Host "[3/5] Iniciando tunnel Cloudflare..." -ForegroundColor Yellow
$logFile = "$locacaoDir\tunnel_restart.log"
Start-Process -FilePath "$locacaoDir\cloudflared.exe" -ArgumentList "tunnel","--url","http://localhost:5000" -RedirectStandardError $logFile -WindowStyle Minimized

# 4. Espera e captura a URL do tunnel
Write-Host "[4/5] Aguardando tunnel ficar online..." -ForegroundColor Yellow
$tunnelUrl = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
    if ($content -match "(https://[a-z0-9-]+\.trycloudflare\.com)") {
        $tunnelUrl = $Matches[1]
        break
    }
}

if ($tunnelUrl) {
    Write-Host "  Tunnel OK! $tunnelUrl" -ForegroundColor Green
} else {
    Write-Host "  ERRO: Tunnel nao subiu! Verifique $logFile" -ForegroundColor Red
    exit 1
}

# 5. Atualiza o url.json e envia pro GitHub
Write-Host "[5/5] Atualizando link permanente no GitHub..." -ForegroundColor Yellow
$json = @{
    tunnel_url = $tunnelUrl
    updated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Set-Content -Path "C:\Users\netho\OneDrive\Desktop\md-locacoes-pages\url.json" -Value $json

Set-Location "C:\Users\netho\OneDrive\Desktop\md-locacoes-pages"
git add url.json
git commit -m "Update tunnel URL: $tunnelUrl" --allow-empty 2>$null
git push origin main 2>$null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   SISTEMA ONLINE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "LINK PERMANENTE (fixo):" -ForegroundColor Cyan
Write-Host "  https://nethomiranda.github.io/md-locacoes/" -ForegroundColor White
Write-Host ""
Write-Host "LINKS DIRETOS:" -ForegroundColor Cyan
Write-Host "  Antonio:   https://nethomiranda.github.io/md-locacoes/m1.html" -ForegroundColor White
Write-Host "  Eslaine:   https://nethomiranda.github.io/md-locacoes/m2.html" -ForegroundColor White
Write-Host "  Matheus:   https://nethomiranda.github.io/md-locacoes/m3.html" -ForegroundColor White
Write-Host "  Admin:     https://nethomiranda.github.io/md-locacoes/admin.html" -ForegroundColor White
Write-Host ""
Write-Host "LINK TEMPORARIO (direto):" -ForegroundColor Yellow
Write-Host "  $tunnelUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "IMPORTANTE: Nao feche esta janela enquanto quiser manter o sistema online!" -ForegroundColor Red
Write-Host "Pressione Ctrl+C ou feche a janela para parar." -ForegroundColor Gray

# Mantem o script vivo
Write-Host ""
Write-Host "Pressione qualquer tecla para PARAR o servidor..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Servidor parado." -ForegroundColor Red
