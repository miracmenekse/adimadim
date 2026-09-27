#!/usr/bin/env bash
# Test kayıtları: metin dosyasındaki her satırı gösterir, okuyuşunu kaydeder.
#   kayit_al.sh                    testler/cumleler.txt → testler/ses/
#   kayit_al.sh paragraflar        testler/paragraflar/metinler.txt → testler/paragraflar/
# Çıktı: <klasör>/NN.wav + NN.txt (16 kHz mono). Var olan kayıtlar atlanır.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "${1:-}" = paragraflar ]; then KAYNAK=testler/paragraflar/metinler.txt; HEDEF=testler/paragraflar
else KAYNAK=testler/cumleler.txt; HEDEF=testler/ses; fi
mkdir -p "$HEDEF"
n=0
while IFS= read -r cumle; do
  n=$((n + 1)); ad=$(printf '%s/%02d' "$HEDEF" "$n")
  [ -f "$ad.wav" ] && continue
  echo; echo "[$n] Doğal hızınla oku, bitince Enter:"; echo "    $cumle"
  read -rp "Hazırsan Enter… " < /dev/tty
  arecord -q -f S16_LE -r 16000 -c 1 "$ad.wav" 2>/dev/null & pid=$!
  read -r < /dev/tty; sleep 0.5; kill -INT "$pid"; wait "$pid" 2>/dev/null || true
  echo "$cumle" > "$ad.txt"
done < "$KAYNAK"
echo; echo "KAYIT TAMAM: $(ls "$HEDEF"/*.wav | wc -l) kayıt $HEDEF/ altında"
