#!/usr/bin/env bash
# ortam.sh — VM (geliştirme) ile ana makine (kullanım) arasındaki kurulum farkını bulur.
# sürüm: 1
#
#   taban     VM'de, bir kez, proje işine başlamadan: VM'in temiz hâlini kaydeder
#             (~/.local/share/ortam/taban.txt; repoya girmez).
#   kaydet    VM'de: tabandan sonra VM'e eklenenleri <proje>/.ortam/vm.txt'ye yazar (commit'lenir).
#   denetle   VM'de, push'tan önce: vm.txt'deki ama projede hiçbir dosyada (kur betiği, requirements,
#             CHANGELOG…) adı geçmeyen öğeleri listeler. Bunlar ana makinede eksik kalacak olanlardır.
#   kontrol   Ana makinede: vm.txt'deki her öğenin burada olup olmadığına bakar ve YALNIZCA eksikleri
#             yazar; ana makinenin kendi paket listesi hiçbir yere gitmez. Çıktı VM'deki Claude'a verilir.
#   liste     Bu makinenin envanterini yazar (inceleme için).
#
# Envanter: apt (elle kurulanlar), snap, pip --user, ~/.local/bin, Ubuntu sürümü, mimari, python3
# sürümü, kullanıcının grupları ve <proje>/.ortam/komutlar.txt'deki komutlar.
# <proje>/.ortam/yoksay.txt: ana makinede gerekmeyen öğeler ("tür ad", ad'da * olabilir).
set -euo pipefail

TABAN="${XDG_DATA_HOME:-$HOME/.local/share}/ortam/taban.txt"
PROJE="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ORTAM="$PROJE/.ortam"
VM_DOSYA="$ORTAM/vm.txt"
YOKSAY="$ORTAM/yoksay.txt"
KOMUTLAR="$ORTAM/komutlar.txt"

temiz_satirlar() { [ -f "$1" ] && sed -e 's/#.*//' -e 's/[[:space:]]*$//' "$1" | grep -v '^[[:space:]]*$' || true; }

python_surumu() { python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo yok; }

pip_kullanici() {  # "ad sürüm" (küçük harf, - ve _ aynı)
  python3 -m pip list --user --format=freeze 2>/dev/null \
    | sed -n 's/^\([^=]*\)==\(.*\)$/\1 \2/p' | tr 'A-Z_' 'a-z-' || true
}

sistem_degeri() {  # $1: os | mimari
  case "$1" in
    os) if [ -r /etc/os-release ]; then (. /etc/os-release; echo "${ID:-?}-${VERSION_ID:-?}"); else echo bilinmiyor; fi ;;
    mimari) dpkg --print-architecture 2>/dev/null || uname -m ;;
  esac
}

envanter() {  # her satır: "tür ad [değer]"
  echo "sistem os $(sistem_degeri os)"
  echo "sistem mimari $(sistem_degeri mimari)"
  echo "surum python3 $(python_surumu)"
  # Her adım kendi başına başarısız olabilir (araç yok, liste boş); envanter yine de tamamlanmalı.
  { apt-mark showmanual 2>/dev/null | sed 's/^/apt /'; } || true
  { snap list 2>/dev/null | awk 'NR>1 {print "snap " $1}'; } || true
  { pip_kullanici | awk '{print "pip " $1}'; } || true
  { find "$HOME/.local/bin" -maxdepth 1 \( -type f -o -type l \) -printf 'bin %f\n' 2>/dev/null; } || true
  { id -nG 2>/dev/null | tr ' ' '\n' | grep -vx "$(id -un)" | sed 's/^/grup /'; } || true
  while read -r k _; do
    if command -v "$k" >/dev/null; then echo "komut $k"; fi
  done < <(temiz_satirlar "$KOMUTLAR")
}

yok_sayiliyor() {  # $1=tür $2=ad
  local tur ad
  while read -r tur ad _; do
    # shellcheck disable=SC2254
    [ "$tur" = "$1" ] && case "$2" in $ad) return 0 ;; esac
  done < <(temiz_satirlar "$YOKSAY")
  return 1
}

cmd_taban() {
  mkdir -p "$(dirname "$TABAN")"
  if [ -f "$TABAN" ] && [ "${1:-}" != "--zorla" ]; then
    echo "Taban zaten var: $TABAN (yenilemek için: ortam.sh taban --zorla)"; return 0
  fi
  { envanter | grep -v '^sistem \|^surum ' || true; } | sort -u > "$TABAN"
  echo "Taban kaydedildi: $TABAN ($(wc -l < "$TABAN") öğe). Bundan sonra kurulanlar 'kaydet' ile görünür."
}

cmd_kaydet() {
  [ -f "$TABAN" ] || echo "Uyarı: taban yok ($TABAN); VM'deki her şey kaydedilecek. Önce 'ortam.sh taban' önerilir." >&2
  mkdir -p "$ORTAM"
  local gecici; gecici="$(mktemp)"
  envanter | sort -u | while read -r tur ad deger; do
    case "$tur" in
      sistem|surum) echo "$tur $ad $deger" ;;
      *) if ! grep -qxF "$tur $ad" "$TABAN" 2>/dev/null && ! yok_sayiliyor "$tur" "$ad"; then echo "$tur $ad"; fi ;;
    esac
  done > "$gecici"
  {
    echo "# ortam.sh kaydet — VM'de tabandan sonra eklenenler ve sistem bilgisi. Elle düzenleme;"
    echo "# gereksiz öğeleri .ortam/yoksay.txt'e yaz. Ana makinede: .ortam/ortam.sh kontrol"
    cat "$gecici"
  } > "$VM_DOSYA"
  rm -f "$gecici"
  echo "Yazıldı: $VM_DOSYA ($(grep -vc '^#\|^sistem \|^surum ' "$VM_DOSYA" || true) öğe)."
}

cmd_denetle() {
  [ -f "$VM_DOSYA" ] || { echo "Önce: ortam.sh kaydet"; return 1; }
  local eksik=0 tur ad
  while read -r tur ad _; do
    case "$tur" in sistem|surum) continue ;; esac
    yok_sayiliyor "$tur" "$ad" && continue
    if ! git -C "$PROJE" grep -qwF -- "$ad" -- ':!.ortam' 2>/dev/null; then
      echo "İŞLENMEMİŞ $tur $ad"; eksik=$((eksik + 1))
    fi
  done < <(temiz_satirlar "$VM_DOSYA")
  if [ "$eksik" -eq 0 ]; then
    echo "Tamam: VM'e eklenen her öğe projede (kur betiği, requirements, CHANGELOG…) geçiyor ya da yok sayılıyor."
  else
    echo "$eksik öğe projede hiç geçmiyor: kur betiğine işle, CHANGELOG'daki ana makine adımlarına yaz"
    echo "ya da gerekmiyorsa .ortam/yoksay.txt'e ekle (not: denetim ada göre, commit'lenmiş dosyalarda arar)."
    return 1
  fi
}

cmd_kontrol() {
  [ -f "$VM_DOSYA" ] || { echo "Bulunamadı: $VM_DOSYA (VM'de 'ortam.sh kaydet' çalıştırılıp push'lanmalı)"; return 1; }
  local sorun=0 tur ad deger burada pipler
  pipler="$(pip_kullanici)"
  while read -r tur ad deger; do
    yok_sayiliyor "$tur" "$ad" && continue
    case "$tur" in
      sistem)
        burada="$(sistem_degeri "$ad")"
        [ "$burada" = "$deger" ] || { echo "FARKLI sistem $ad VM=$deger burada=$burada"; sorun=$((sorun + 1)); } ;;
      surum)
        burada="$(python_surumu)"
        [ "$burada" = "$deger" ] || { echo "FARKLI $ad VM=$deger burada=$burada"; sorun=$((sorun + 1)); } ;;
      apt)  dpkg-query -W -f='${Status}' "$ad" 2>/dev/null | grep -q "install ok installed" \
              || { echo "EKSIK apt $ad"; sorun=$((sorun + 1)); } ;;
      snap) snap list "$ad" >/dev/null 2>&1 || { echo "EKSIK snap $ad"; sorun=$((sorun + 1)); } ;;
      pip)  grep -q "^$ad " <<< "$pipler" || { echo "EKSIK pip $ad"; sorun=$((sorun + 1)); } ;;
      bin)  [ -e "$HOME/.local/bin/$ad" ] || command -v "$ad" >/dev/null \
              || { echo "EKSIK bin $ad"; sorun=$((sorun + 1)); } ;;
      grup) id -nG | tr ' ' '\n' | grep -qx "$ad" || { echo "EKSIK grup $ad"; sorun=$((sorun + 1)); } ;;
      komut) ;;  # komutlar.txt aşağıda doğrudan denetlenir
    esac
  done < <(temiz_satirlar "$VM_DOSYA")
  while read -r ad _; do
    command -v "$ad" >/dev/null || { echo "EKSIK komut $ad"; sorun=$((sorun + 1)); }
  done < <(temiz_satirlar "$KOMUTLAR")
  if [ "$sorun" -eq 0 ]; then
    echo "ORTAM: fark yok (VM'deki her öğe burada da var)."
  else
    echo "ORTAM: fark var. Yukarıdaki EKSIK/FARKLI satırlarını VM'deki Claude Code'a ver."
    return 1
  fi
}

case "${1:-}" in
  taban)   shift; cmd_taban "$@" ;;
  kaydet)  cmd_kaydet ;;
  denetle) cmd_denetle ;;
  kontrol) cmd_kontrol ;;
  liste)   envanter | sort -u ;;
  *) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
