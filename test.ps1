# adımadım Windows testleri: 1) sözdizimi 2) durum komutu 3) gerçek konuşma tanıma
[CmdletBinding()]
param()

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = '1'          # Python çıktısı Türkçe karakterde cp1252'ye takılmasın
$env:PYTHONIOENCODING = 'utf-8'
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$Venv = Join-Path $env:LOCALAPPDATA 'adimadim\venv'
$Py = Join-Path $Venv 'Scripts\python.exe'
$Hata = 0

function Baslik([string]$Metin) { Write-Host "== $Metin" }
function HataYaz([string]$Metin) { Write-Host "HATA: $Metin" -ForegroundColor Red; $script:Hata++ }

if (-not (Test-Path $Py)) { Write-Host 'Önce kur.ps1 çalıştır.'; exit 1 }

Baslik '1/3 Sözdizimi'
$env:PYTHONPYCACHEPREFIX = Join-Path $env:TEMP 'adimadim-pycache'
$dosyalar = @(Get-ChildItem -Path $Repo -Recurse -Filter *.py -File | ForEach-Object { $_.FullName })
& $Py -m py_compile $dosyalar
if ($LASTEXITCODE -ne 0) { HataYaz 'sözdizimi hatası' } else { Write-Host 'tamam' }

Baslik '2/3 Durum'
& $Py (Join-Path $Repo 'adimadim.py') durum
if ($LASTEXITCODE -ne 0) { HataYaz 'durum komutu başarısız' } else { Write-Host 'tamam' }

Baslik '3/3 Konuşma tanıma (gerçek model)'
$kod = @'
import sys
sys.path.insert(0, sys.argv[1] + '/testler')
import stt_olc
a = stt_olc.adimadim.ayarlari_oku()
if str(a.get('stt', 'openvino')).lower() != 'openvino':
    print('Atlandı: stt openvino değil.')
    sys.exit(0)
c = stt_olc.adimadim.openvino_cevirici(a, str(a.get('cihaz') or 'CPU').upper())
print('OpenVINO modeli yüklendi:', a.get('ov_model'), a.get('cihaz'))
import numpy as n, tempfile, wave
f = tempfile.mktemp(suffix='.wav')
w = wave.open(f, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
w.writeframes((n.random.default_rng(0).normal(0, .03, 80000) * 32767).astype('<i2').tobytes()); w.close()
m = ' '.join(t for _, _, t in c(stt_olc.adimadim.wav_oku(stt_olc.adimadim.Path(f))))
print('gürültüde metin uydurmuyor' if not m else 'gürültüden metin uydurdu: %r' % m)
sys.exit(1 if m else 0)
'@
& $Py -c $kod ($Repo.Replace('\', '/'))
if ($LASTEXITCODE -ne 0) { HataYaz 'OpenVINO modeli yüklenemedi ya da gürültüde metin uydurdu' } else { Write-Host 'tamam' }

if ($Hata -eq 0) { Write-Host 'SONUÇ: testler geçti' } else { Write-Host "SONUÇ: $Hata test başarısız" }
exit $Hata
