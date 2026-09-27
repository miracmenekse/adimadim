#!/usr/bin/env bash
# Testler: 1) sözdizimi  2) sahte ekran/mikrofon/modelle uçtan uca akış  3) varsa gerçek STT ölçümü
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${ADIMADIM_VENV:-$HOME/.local/share/adimadim/venv}/bin/python"
[ -x "$PY" ] || { echo "Önce ./kur.sh çalıştır."; exit 1; }
HATA=0

echo "== 1/3 Sözdizimi"
if "$PY" -m py_compile "$REPO/adimadim.py" "$REPO"/araclar/*.py "$REPO"/testler/*.py; then
  echo "✓ tamam"
else
  echo "✗ sözdizimi hatası"; HATA=1
fi

echo "== 2/3 Uçtan uca akış (sahte ekran, mikrofon ve model)"
"$PY" "$REPO/testler/duman_testi.py" || HATA=1

echo "== 3/3 Konuşma tanıma doğruluğu (gerçek model)"
# Araç OpenVINO açılamazsa sessizce faster-whisper'a düşer; burada yedeksiz yüklenmeli.
if "$PY" -c "import sys; sys.path.insert(0, '$REPO/testler'); import stt_olc; a = stt_olc.adimadim.ayarlari_oku()
if str(a.get('stt', 'openvino')).lower() == 'openvino':
    c = stt_olc.adimadim.openvino_cevirici(a, str(a.get('cihaz') or 'CPU').upper()); print('✓ OpenVINO modeli yüklendi:', a.get('ov_model'), a.get('cihaz'))
    import numpy as n, tempfile, wave
    f = tempfile.mktemp(suffix='.wav'); w = wave.open(f, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes((n.random.default_rng(0).normal(0, .03, 80000) * 32767).astype('<i2').tobytes()); w.close()
    m = ' '.join(t for _, _, t in c(stt_olc.adimadim.wav_oku(stt_olc.adimadim.Path(f)))); print(('✓ gürültüde metin uydurmuyor' if not m else f'✗ gürültüden metin uydurdu: {m!r}')); sys.exit(1 if m else 0)"; then :
else
  echo "✗ OpenVINO modeli yüklenemedi ya da gürültüde metin uydurdu"; HATA=1
fi
if compgen -G "$REPO/testler/ses/*.wav" >/dev/null; then
  "$PY" "$REPO/testler/stt_olc.py" || HATA=1
else
  echo "Atlandı: testler/ses/ içinde kayıt yok (bkz. testler/README.md)."
fi

if [ "$HATA" -eq 0 ]; then echo "SONUÇ: testler geçti"; else echo "SONUÇ: hata var"; fi
exit "$HATA"
