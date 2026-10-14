# MD Locacoes - Inicio automatico (roda oculto ao ligar o PC)
$locacaoDir = "C:\Users\netho\OneDrive\Desktop\LocacaoMD"
$logFile = "$locacaoDir\tunnel_auto.log"

# Mata processos antigos
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Inicia Flask oculto
Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory $locacaoDir -WindowStyle Hidden
Start-Sleep -Seconds 4

# Inicia tunnel oculto
Start-Process -FilePath "$locacaoDir\cloudflared.exe" -ArgumentList "tunnel","--url","http://localhost:5000" -RedirectStandardError $logFile -WindowStyle Hidden

# Espera e captura URL
$tunnelUrl = $null
for ($i = 0; $i -lt 25; $i++) {
    Start-Sleep -Seconds 2
    $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
    if ($content -match "(https://[a-z0-9-]+\.trycloudflare\.com)") {
        $tunnelUrl = $Matches[1]
        break
    }
}

if ($tunnelUrl) {
    # Atualiza url.json no GitHub
    $json = @{
        tunnel_url = $tunnelUrl
        updated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json
    Set-Content -Path "C:\Users\netho\OneDrive\Desktop\md-locacoes-pages\url.json" -Value $json
    Set-Location "C:\Users\netho\OneDrive\Desktop\md-locacoes-pages"
    git add url.json 2>$null
    git commit -m "Auto-update: $tunnelUrl" --allow-empty 2>$null
    git push origin main 2>$null
}
