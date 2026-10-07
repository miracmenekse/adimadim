#!/usr/bin/env bash
# guncelle.sh — ANA MAKİNEDE çalışır: bir projeyi tek tıkla günceller. GitHub'dan son hâli çeker,
# kod son başarılı kurulumdan beri değiştiyse kurar (uygulama açıksa önce kapatılmasını bekler),
# sonra uygulamayı açar. Hata olursa terminal penceresi Enter'a basılana kadar açık kalır.
#
#   guncelle.sh REPO                        düğmenin yaptığı iş
#   guncelle.sh --kisayol REPO [UZAK/DAL]   Uygulamalar'a ve Sık Kullanılanlar'a (dock) "AD güncelle"
#                                           düğmesini ekler; UZAK/DAL verilirse (ör. mm/main) repo önce o dala geçer
#
# Proje ayarı repodaki .ortam/guncelle dosyasındadır; her seferinde pull'dan SONRA okunur, yani VM'den
# değiştirilebilir:
#   AD="adımadım"                       düğmenin adı
#   KUR="./kur.sh"                      kod değişince repo kökünde çalışır (kur, derle…)
#   AC="~/.local/bin/adimadim arayuz"   en sonda uygulamayı açar (boşsa açmaz)
#   SUREC="adimadim.py arayuz"          çalışan uygulamayı bulan `pgrep -f` deseni (repo yolunu içermemeli)
# Son başarılı kurulumun commit'i: ~/.local/state/guncelle/<repo klasörünün adı>
set -euo pipefail

calisiyor() { [ -n "$SUREC" ] && pgrep -f -- "$SUREC" >/dev/null; }

if [ "${1:-}" = --kisayol ]; then
  REPO="$(cd "${2:?REPO verilmedi}" && pwd)"
  if [ -n "${3:-}" ]; then
    git -C "$REPO" fetch "${3%%/*}"
    git -C "$REPO" checkout -B "${3#*/}" --track "$3"
  fi
  . "$REPO/.ortam/guncelle"
  KISA="guncelle-$(basename "$REPO")"
  UYG="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  mkdir -p "$UYG"
  cat > "$UYG/$KISA.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$AD güncelle
Comment=Son hâli GitHub'dan al, kur ve aç
Exec=$(readlink -f "$0") $REPO
Icon=system-software-update
Terminal=true
Categories=Development;
EOF
  FAV="$(gsettings get org.gnome.shell favorite-apps 2>/dev/null)" || FAV=""
  case "$FAV" in
    ""|*"'$KISA.desktop'"*) ;;
    *) gsettings set org.gnome.shell favorite-apps "${FAV%]}, '$KISA.desktop']" 2>/dev/null || true ;;
  esac
  echo "Düğme hazır: dock'ta ve Uygulamalar'da \"$AD güncelle\"."
  exit 0
fi

REPO="$(cd "${1:?REPO verilmedi}" && pwd)"
cd "$REPO"
DAMGA="${XDG_STATE_HOME:-$HOME/.local/state}/guncelle/$(basename "$REPO")"
bitti() { local k=$?; [ "$k" -eq 0 ] || read -rp $'\n'"HATA (kod $k). Bu pencereyi Claude'a göster. Kapatmak için Enter… "; }
trap bitti EXIT

echo "== GitHub'dan son hâl alınıyor: $REPO"
ONCE="$(git rev-parse HEAD)"
git pull --ff-only
git log --oneline "$ONCE..HEAD"
. .ortam/guncelle
SIMDI="$(git rev-parse HEAD)"

if [ "$(cat "$DAMGA" 2>/dev/null)" = "$SIMDI" ]; then
  echo "== $AD zaten güncel."
else
  while calisiyor; do read -rp "$AD açık. Kapat, sonra Enter'a bas… "; done
  echo "== Kuruluyor: $KUR"
  eval "$KUR"
  mkdir -p "$(dirname "$DAMGA")" && echo "$SIMDI" > "$DAMGA"
fi

if [ -n "$AC" ] && ! calisiyor; then
  echo "== $AD açılıyor"
  setsid -f bash -c "$AC" </dev/null >/dev/null 2>&1
fi
read -rt 5 -p "Tamam. Pencere 5 sn sonra kapanır." || true
