# Baixa fotos reais para os exemplos do LocacaoMD (static/exemplos/*.jpg).
# Prefere Wikimedia (permite download com UA descritivo). Converte tudo
# para JPG redimensionado (max 1200px). Falhas viram fallback (PNG antigo).
$ErrorActionPreference = "Stop"
$dest = "C:\Users\netho\Desktop\LocacaoMD\static\exemplos"
$logf = "C:\Users\netho\Desktop\LocacaoMD\_download_log.txt"
$ua = "LocacaoMD-ExamplePhotos/1.0 (https://github.com/NETHOMIRANDA/LocacaoMD; contato: usuario@exemplo.com)"
Add-Type -AssemblyName System.Drawing

function Log($m) { ("$(Get-Date -f 'HH:mm:ss')  " + $m) | Out-File $logf -Append -Encoding utf8 }

function Salvar-Como-Jpg($url, $arqFinal, $maxLado) {
  $tmp = [System.IO.Path]::GetTempFileName()
  try {
    Invoke-WebRequest -Uri $url -OutFile $tmp -TimeoutSec 60 -Headers @{ "User-Agent" = $ua }
    $b = [System.IO.File]::ReadAllBytes($tmp)
    $eJPEG = ($b.Length -gt 5000 -and $b[0] -eq 0xFF -and $b[1] -eq 0xD8)
    $ePNG  = ($b.Length -gt 5000 -and $b[0] -eq 0x89 -and $b[1] -eq 0x50)
    if (-not ($eJPEG -or $ePNG)) { return $false }
    $fs = [System.IO.File]::OpenRead($tmp)
    $img = [System.Drawing.Image]::FromStream($fs)
    $w = $img.Width; $h = $img.Height
    if ($w -gt $maxLado) { $nw = $maxLado; $nh = [int]($h * $maxLado / $w) }
    else { $nw = $w; $nh = $h }
    $bmp = New-Object System.Drawing.Bitmap($nw, $nh)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($img, 0, 0, $nw, $nh)
    $g.Dispose()
    $img.Dispose()
    $fs.Dispose()
    $bmp.Save($arqFinal, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()
    return $true
  } finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
  }
}

Log "INICIO - espera curta (2 min)"
Start-Sleep -Seconds 120

$buscas = @(
  @{ chave="externo_frente";   q="car front view" },
  @{ chave="externo_traseira"; q="car rear view" },
  @{ chave="externo_lado_dir";   q="car side view road" },
  @{ chave="pneu_dianteiro_esq"; q="car front tire wheel" },
  @{ chave="pneu_dianteiro_dir"; q="car wheel closeup" },
  @{ chave="pneu_traseiro_esq";  q="car rear tire" },
  @{ chave="pneu_traseiro_dir";  q="car tire sidewall" },
  @{ chave="interno_bancos";     q="car seats interior" },
  @{ chave="interno_porta_malas"; q="car trunk open empty" },
  @{ chave="interno_teto";       q="car interior ceiling roof" },
  @{ chave="interno_piso";       q="car floor mat interior" },
  @{ chave="painel";             q="car dashboard speedometer" }
)

foreach ($b in $buscas) {
  $ok = $false
  for ($t = 1; $t -le 4 -and -not $ok; $t++) {
    try {
      $u = "https://api.openverse.org/v1/images/?q=" + [uri]::EscapeDataString($b.q) + "&license_type=commercial&page_size=20"
      $r = Invoke-RestMethod -Uri $u -TimeoutSec 25
      $res = @($r.results | Where-Object { $_.width -ge 800 })
      if (-not $res) { Log "$($b.chave): sem candidato"; Start-Sleep -Seconds 40; continue }
      # prefere wikimedia (funciona com nosso UA), depois outros, flickr por ultimo
      $ordem = @($res | Where-Object { $_.url -match "wikimedia" })
      if (-not $ordem) { $ordem = @($res | Where-Object { $_.url -notmatch "flickr" }) }
      if (-not $ordem) { $ordem = $res }
      $img = $ordem[0]
      $arq = Join-Path $dest ($b.chave + ".jpg")
      if (Salvar-Como-Jpg $img.url $arq 1200) {
        Log "$($b.chave): OK origem=$($img.width)x$($img.height) licenca=$($img.license) | $($img.title) | $($img.foreign_landing_url)"
        $ok = $true
      } else {
        Remove-Item $arq -Force -ErrorAction SilentlyContinue
        Log "$($b.chave): tentativa $t formato invalido"
        Start-Sleep -Seconds 40
      }
    } catch {
      Log "$($b.chave): tentativa $t ERRO $($_.Exception.Message)"
      Start-Sleep -Seconds 50
    }
  }
  Start-Sleep -Seconds 30
}

# Fallback: categorias sem foto real viram o desenho antigo convertido pra JPG
$chaves = @("externo_frente","externo_traseira","externo_lado_dir","pneu_dianteiro_esq","pneu_dianteiro_dir","pneu_traseiro_esq","pneu_traseiro_dir","interno_bancos","interno_porta_malas","interno_teto","interno_piso","painel")
foreach ($c in $chaves) {
  $jpg = Join-Path $dest ($c + ".jpg")
  if (Test-Path $jpg) { continue }
  $png = Join-Path $dest ($c + ".png")
  if (Test-Path $png) {
    try {
      $fs = [System.IO.File]::OpenRead($png)
      $img = [System.Drawing.Image]::FromStream($fs)
      $bmp = New-Object System.Drawing.Bitmap($img)
      $img.Dispose(); $fs.Dispose()
      $bmp.Save($jpg, [System.Drawing.Imaging.ImageFormat]::Jpeg)
      $bmp.Dispose()
      Log "${c}: FALLBACK (desenho antigo convertido)"
    } catch { Log "${c}: fallback falhou: $($_.Exception.Message)" }
  } else {
    Log "${c}: SEM FOTO e sem PNG original!"
  }
}
Log "CONCLUIDO"
