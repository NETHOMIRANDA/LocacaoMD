# Passe de qualidade: refaz as categorias com foto errada, duplicada,
# vaga ou desenho antigo. Filtra titulo (so carro) e prefere wikimedia.
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
    $g.Dispose(); $img.Dispose(); $fs.Dispose()
    $bmp.Save($arqFinal, [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()
    return $true
  } finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
  }
}

Log "PASSE DE QUALIDADE - inicio (9 categorias)"

# chave, busca, padrao obrigatorio no titulo, padrao proibido no titulo
$fixes = @(
  @{ chave="externo_lado_dir";     q="car side profile";                ok="car|sedan|vehicle";                no="bike|bicycle|motorcycle|moped|truck|van|sign|pub" },
  @{ chave="pneu_dianteiro_esq";  q="car wheel tire";                  ok="car|wheel|tire|hubcap|alloy";      no="bike|bicycle|mavic|motorcycle|moped" },
  @{ chave="pneu_dianteiro_dir";  q="car tire closeup";                ok="car|wheel|tire|hubcap|alloy";      no="bike|bicycle|mavic|motorcycle|moped" },
  @{ chave="pneu_traseiro_esq";   q="car rear wheel";                  ok="car|wheel|tire|hubcap|alloy";      no="bike|bicycle|mavic|motorcycle|moped" },
  @{ chave="interno_bancos";      q="car seats";                       ok="car|seat|interior";                no="bike|bicycle|chair|sofa|pub" },
  @{ chave="interno_porta_malas"; q="car trunk";                       ok="car|trunk|boot";                   no="bike|bicycle|tree|pub" },
  @{ chave="interno_teto";        q="car interior";                    ok="car|interior|seat|dash|roof";      no="bike|bicycle|pub|inn|sign|bar" },
  @{ chave="interno_piso";        q="car floor mat carpet";            ok="car|mat|carpet|floor|interior";    no="bike|bicycle" },
  @{ chave="painel";              q="car dashboard";                   ok="car|dashboard|speedometer|interior"; no="bike|bicycle" }
)

foreach ($f in $fixes) {
  $ok = $false
  for ($t = 1; $t -le 6 -and -not $ok; $t++) {
    try {
      $u = "https://api.openverse.org/v1/images/?q=" + [uri]::EscapeDataString($f.q) + "&license_type=commercial&page_size=20"
      $r = Invoke-RestMethod -Uri $u -TimeoutSec 25
      $res = @($r.results | Where-Object {
        $_.width -ge 800 -and
        $_.title -match $f.ok -and
        $_.title -notmatch $f.no
      })
      if (-not $res) { Log "$($f.chave): sem candidato filtrado (tentativa $t)"; Start-Sleep -Seconds 30; continue }
      $ordem = @($res | Where-Object { $_.url -match "wikimedia" })
      if (-not $ordem) { $ordem = @($res | Where-Object { $_.url -match "flickr" }) }
      if (-not $ordem) { $ordem = $res }
      $img = $ordem[0]
      $arq = Join-Path $dest ($f.chave + ".jpg")
      if (Salvar-Como-Jpg $img.url $arq 1200) {
        Log "$($f.chave): QUALIDADE OK $($img.width)x$($img.height) licenca=$($img.license) | $($img.title) | $($img.foreign_landing_url)"
        $ok = $true
      } else {
        Log "$($f.chave): formato invalido (tentativa $t) | $($img.title)"
        Start-Sleep -Seconds 30
      }
    } catch {
      Log "$($f.chave): ERRO $($_.Exception.Message) (tentativa $t)"
      Start-Sleep -Seconds 40
    }
  }
  if (-not $ok) { Log "$($f.chave): NAO CONSEGUIU substituir - mantem atual" }
  Start-Sleep -Seconds 25
}
Log "PASSE DE QUALIDADE - concluido"
