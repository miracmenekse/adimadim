#!/usr/bin/env bash
# Test kayıtları: testler/cumleler.txt'deki her cümleyi gösterir, okuyuşunu kaydeder.
# Çıktı: testler/ses/NN.wav + NN.txt (16 kHz mono). Var olan kayıtlar atlanır.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p testler/ses
n=0
while IFS= read -r cumle; do
  n=$((n + 1)); ad=$(printf 'testler/ses/%02d' "$n")
  [ -f "$ad.wav" ] && continue
  echo; echo "[$n] Doğal hızınla oku, bitince Enter:"; echo "    $cumle"
  read -rp "Hazırsan Enter… " < /dev/tty
  arecord -q -f S16_LE -r 16000 -c 1 "$ad.wav" & pid=$!
  read -r < /dev/tty; kill -INT "$pid"; wait "$pid" 2>/dev/null || true
  echo "$cumle" > "$ad.txt"
done < testler/cumleler.txt
echo; echo "KAYIT TAMAM: $(ls testler/ses/*.wav | wc -l) kayıt testler/ses/ altında"
