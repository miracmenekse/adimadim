# adımadım Windows kurulumu — tek komut: powershell -ExecutionPolicy Bypass -File kur.ps1
# Defalarca çalıştırmak güvenlidir: kurulu olanı atlar, eksiği tamamlar, ayar.json'daki
# mevcut değerlere dokunmaz. -Kuru yalnızca yapılacak adımları yazar, hiçbir şey kurmaz.
[CmdletBinding()]
param([switch]$Kuru)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$Venv = Join-Path $env:LOCALAPPDATA 'adimadim\venv'
$Py = Join-Path $Venv 'Scripts\python.exe'
$Ayar = Join-Path $env:APPDATA 'adimadim\ayar.json'
$TorchIndex = 'https://download.pytorch.org/whl/cpu'

function Adim([string]$Metin) { Write-Host "==> $Metin" }
function Uyari([string]$Metin) { Write-Host "UYARI: $Metin" -ForegroundColor Yellow }
function Kos {
    param([string]$Dosya, [string[]]$Argumanlar)
    & $Dosya @Argumanlar
    if ($LASTEXITCODE -ne 0) { throw "$Dosya başarısız oldu (çıkış kodu $LASTEXITCODE)" }
}

# ------------------------------------------------------------------ 1. uv
Adim 'uv denetleniyor'
$Uv = $null
if (-not $Kuru) {
    $Uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $Uv) {
        Write-Host 'uv kuruluyor (astral.sh)…'
        Invoke-RestMethod 'https://astral.sh/uv/install.ps1' | Invoke-Expression
        $env:Path = (Join-Path $env:USERPROFILE '.local\bin') + ';' + $env:Path
        $Uv = Get-Command uv -ErrorAction SilentlyContinue
    }
    if (-not $Uv) { throw 'uv kurulamadı; https://astral.sh/uv adresinden elle kurup tekrar dene.' }
}

# ------------------------------------------------------------------ 2. python 3.10
Adim 'uv ile Python 3.10'
if (-not $Kuru) { Kos $Uv.Source @('python', 'install', '3.10') }

# ------------------------------------------------------------------ 3. venv
Adim "venv: $Venv"
if (-not $Kuru -and -not (Test-Path $Py)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Venv) | Out-Null
    Kos $Uv.Source @('venv', '--python', '3.10', $Venv)
}

# ------------------------------------------------------------------ 4. torch (CPU)
Adim 'torch (CPU) kuruluyor'
if (-not $Kuru) {
    Kos $Uv.Source @('pip', 'install', '--python', $Py, 'torch', 'torchvision', '--index-url', $TorchIndex)
}

# ------------------------------------------------------------------ 5. ortak bağımlılıklar
Adim 'requirements-win.txt kuruluyor'
if (-not $Kuru) {
    Kos $Uv.Source @('pip', 'install', '--python', $Py, '-r', (Join-Path $Repo 'requirements-win.txt'))
}

# ------------------------------------------------------------------ 6. ayarlar
Adim "Ayarlar: $Ayar"
if (-not $Kuru) {
    $ayarKur = Join-Path $Repo 'araclar\ayar_kur.py'
    Kos $Py @($ayarKur, (Join-Path $Repo 'ayar.ornek.json'), $Ayar)
}

# ------------------------------------------------------------------ 7. konuşma modeli
Adim 'OpenVINO modeli (optimum-cli)'
if (-not $Kuru) {
    $ayar = Get-Content $Ayar -Raw -Encoding UTF8 | ConvertFrom-Json
    $kaynak = [string]$ayar.ov_kaynak
    $model = [string]$ayar.ov_model
    if ($model.StartsWith('~')) { $model = Join-Path $env:USERPROFILE ($model.Substring(1).TrimStart('\', '/')) }
    $optimum = Join-Path $Venv 'Scripts\optimum-cli.exe'
    if (-not $kaynak -or -not $model) {
        Uyari "ayar.json'da ov_kaynak / ov_model boş; model adımı atlandı."
    } elseif (Test-Path (Join-Path $model 'openvino_encoder_model.xml')) {
        Write-Host "Hazır: $model"
    } elseif (-not (Test-Path $optimum)) {
        Uyari "optimum-cli kurulu değil; model dönüştürülemedi (requirements-win.txt'i kontrol et)."
    } else {
        Write-Host "$kaynak -> $model dönüştürülüyor (bir kez yapılır, birkaç dakika sürer)…"
        New-Item -ItemType Directory -Force -Path (Split-Path $model) | Out-Null
        try {
            Kos $optimum @('export', 'openvino', '--model', $kaynak, '--weight-format', 'fp16', $model)
        } catch {
            Uyari "Model indirilemedi ya da dönüştürülemedi: $($_.Exception.Message)"
            Uyari "İnternet bağlantısını kontrol edip kur.ps1'yi tekrar çalıştır. Kurulum devam ediyor."
        }
    }
}

# ------------------------------------------------------------------ 8. masaüstü kısayolu
Adim 'Masaüstü kısayolu adımadım.lnk'
if (-not $Kuru) {
    $pythonw = Join-Path $Venv 'Scripts\pythonw.exe'
    $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'adımadım.lnk'
    $kabuk = New-Object -ComObject WScript.Shell
    $kisayol = $kabuk.CreateShortcut($lnk)
    $kisayol.TargetPath = $pythonw
    $kisayol.Arguments = '"' + (Join-Path $Repo 'adimadim.py') + '" arayuz'
    $kisayol.WorkingDirectory = $Repo
    $kisayol.IconLocation = "$pythonw,0"
    $kisayol.Save()
    Write-Host "Tamam: $lnk"
}

# ------------------------------------------------------------------ 9. komut sarmalayıcı
Adim 'Komut sarmalayıcı adimadim.cmd'
if (-not $Kuru) {
    $bin = Join-Path $env:USERPROFILE '.local\bin'
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    $cmd = Join-Path $bin 'adimadim.cmd'
    $icerik = @"
@echo off
rem adimadim-sarmalayici - kur.ps1 olusturdu. Elle duzenleme; gerekirse kur.ps1'yi yeniden calistir.
"$Py" "$(Join-Path $Repo 'adimadim.py')" %*
"@
    Set-Content -Path $cmd -Value $icerik -Encoding Default
    $kullaniciYolu = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($kullaniciYolu -notlike "*$bin*") {
        Uyari "$bin PATH'te değil; oturumu kapatıp açınca eklenir."
    }
    Write-Host "Tamam: $cmd"
}

# ------------------------------------------------------------------ 10. klavye kısayolları
Adim 'Klavye kısayolları (adimadim.py kisayol)'
if (-not $Kuru) {
    & $Py (Join-Path $Repo 'adimadim.py') kisayol
    if ($LASTEXITCODE -ne 0) { Uyari "Kısayollar tanımlanamadı; sonra 'adimadim kisayol' ile dene." }
}

Adim 'Kurulum bitti. Sıradaki adım: test.ps1'
