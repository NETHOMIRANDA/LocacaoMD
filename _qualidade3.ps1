# Ultimo passe: corrige piso, bancos e os 2 pneus com problema.
# Exclui licencas ND (não permite modificação) e termos errados.
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

Log "PASSE 3 - inicio (4 categorias)"

$fixes = @(
  @{ chave="interno_piso";       q="car carpet floor mat";        ok="car|mat|carpet|floor|interior";  no="bike|bicycle|seat|wheel|tire" },
  @{ chave="interno_bancos";     q="car interior seats front";     ok="car|seat|interior|cabin";         no="bike|bicycle|child|baby|chair|sofa|pub" },
  @{ chave="pneu_dianteiro_esq";  q="car wheel hubcap";             ok="car|wheel|hubcap|alloy";          no="bike|bicycle|mavic|motorcycle|moped|f1|racing|formula" },
  @{ chave="pneu_traseiro_esq";   q="car tire wheel";               ok="car|wheel|tire|hubcap";           no="bike|bicycle|mavic|motorcycle|moped|f1|racing|formula" }
)

foreach ($f in $fixes) {
  $ok = $false
  for ($t = 1; $t -le 8 -and -not $ok; $t++) {
    try {
      $u = "https://api.openverse.org/v1/images/?q=" + [uri]::EscapeDataString($f.q) + "&license_type=commercial&page_size=20"
      $r = Invoke-RestMethod -Uri $u -TimeoutSec 25
      $res = @($r.results | Where-Object {
        $_.width -ge 800 -and
        $_.title -match $f.ok -and
        $_.title -notmatch $f.no -and
        $_.license -notin @("by-nd", "cc-by-nd")
      })
      if (-not $res) { Log "$($f.chave): sem candidato filtrado (tentativa $t)"; Start-Sleep -Seconds 30; continue }
      $ordem = @($res | Where-Object { $_.url -match "wikimedia" })
      if (-not $ordem) { $ordem = @($res | Where-Object { $_.url -match "flickr" }) }
      if (-not $ordem) { $ordem = $res }
      $img = $ordem[0]
      $arq = Join-Path $dest ($f.chave + ".jpg")
      if (Salvar-Como-Jpg $img.url $arq 1200) {
        Log "$($f.chave): PASSE3 OK $($img.width)x$($img.height) licenca=$($img.license) | $($img.title) | $($img.foreign_landing_url)"
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
  if (-not $ok) { Log "$($f.chave): NAO CONSEGUIU - mantem atual" }
  Start-Sleep -Seconds 25
}
Log "PASSE 3 - concluido"
