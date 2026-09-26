#!/usr/bin/env bash
# vm-kisayol.sh — ANA MAKİNEDE çalıştırılır: geliştirme VM'ini açan bir kısayol oluşturur ve
# GNOME'da Sık Kullanılanlar'a (Ubuntu dock) ekler. Tıklayınca VM kapalıysa başlatılır, penceresi açılır.
#
#   vm-kisayol.sh              tek VM varsa onu kullanır; birden çoksa listeler
#   vm-kisayol.sh "VM adı"     belirtilen VM için
#   vm-kisayol.sh --kaldir     oluşturduğu kısayolları kaldırır
#   vm-kisayol.sh --komut "KOMUT" "Ad"
#                              VM kendi betiğinle ya da doğrudan qemu ile açılıyorsa: kısayol KOMUT'u
#                              çalıştırır (ör. --komut "RAM=12G CPU=6 ~/vm-is/vm.sh ac" "VM İş")
# Kısayolu ekledikten sonra VM'i de açar; yalnızca kısayol için ADIMADIM_ACMA=1 ver.
#
# Sanallaştırma yazılımını kendisi bulur: VirtualBox, libvirt (virt-manager / GNOME Boxes), VMware.
# Oluşturduğu dosyalar: ~/.local/bin/vm-ac-<ad>, ~/.local/share/applications/vm-ac-<ad>.desktop
# Defalarca çalıştırmak güvenlidir; mevcut sık kullanılanlara dokunmaz, yalnızca kendi kısayolunu ekler.
set -euo pipefail

BIN="$HOME/.local/bin"
UYG="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SEMA="org.gnome.shell"

uyari() { printf '\033[33mUyarı:\033[0m %s\n' "$*" >&2; }
hata()  { printf '\033[31mHata:\033[0m %s\n' "$*" >&2; exit 1; }

kisa_ad() {  # dosya adı için: küçük harf, Türkçe harfler sadeleşmiş, yalnızca a-z0-9-
  python3 - "$1" <<'PY'
import re, sys
s = sys.argv[1].translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower()
print(re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40])
PY
}

favoriler() {  # $1: ekle|cikar  $2: masaüstü dosyası adı
  if ! command -v gsettings >/dev/null || [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    uyari "Masaüstü oturumu bulunamadı; Sık Kullanılanlar değiştirilemedi. Masaüstündeki bir terminalde tekrar çalıştır."
    return 0
  fi
  local liste yeni
  liste="$(gsettings get "$SEMA" favorite-apps)"
  yeni="$(python3 - "$1" "$2" "$liste" <<'PY'
import ast, sys
islem, ad, metin = sys.argv[1], sys.argv[2], sys.argv[3].strip()
if metin.startswith("@as"):
    metin = metin[3:].strip()
liste = [str(x) for x in ast.literal_eval(metin)] if metin else []
if islem == "ekle" and ad not in liste:
    liste.append(ad)
if islem == "cikar":
    liste = [x for x in liste if x != ad]
print("[" + ", ".join("'" + x.replace("\\", "\\\\").replace("'", "\\'") + "'" for x in liste) + "]")
PY
)"
  [ "$yeni" = "$liste" ] || gsettings set "$SEMA" favorite-apps "$yeni"
}

if [ "${1:-}" = "--kaldir" ]; then
  for d in "$UYG"/vm-ac-*.desktop; do
    [ -e "$d" ] || continue
    favoriler cikar "$(basename "$d")"
    rm -f "$d" "$BIN/$(basename "$d" .desktop)"
    echo "Kaldırıldı: $(basename "$d" .desktop)"
  done
  exit 0
fi

# ------------------------------------------------------------ yazılımı ve VM'leri bul
YAZILIM=""; VMLER=(); URI=""; KOMUT=""
if [ "${1:-}" = "--komut" ]; then
  KOMUT="${2:-}"; [ -n "$KOMUT" ] || hata "--komut'tan sonra VM'i açan komutu tırnak içinde yaz."
  YAZILIM=komut; VMLER=("${3:-VM}"); set -- "${3:-VM}"
fi
if [ -z "$YAZILIM" ] && command -v VBoxManage >/dev/null; then
  mapfile -t VMLER < <(VBoxManage list vms 2>/dev/null | sed -n 's/^"\(.*\)" {.*}$/\1/p')
  [ ${#VMLER[@]} -gt 0 ] && YAZILIM=virtualbox
fi
if [ -z "$YAZILIM" ] && command -v virsh >/dev/null; then
  for u in qemu:///system qemu:///session; do
    mapfile -t VMLER < <(virsh -c "$u" list --all --name 2>/dev/null | grep -v '^$' || true)
    if [ ${#VMLER[@]} -gt 0 ]; then YAZILIM=libvirt; URI="$u"; break; fi
  done
fi
if [ -z "$YAZILIM" ] && command -v vmrun >/dev/null; then
  mapfile -t VMLER < <(find "$HOME" -maxdepth 4 -name '*.vmx' 2>/dev/null)
  [ ${#VMLER[@]} -gt 0 ] && YAZILIM=vmware
fi
if [ -z "$YAZILIM" ] && command -v gnome-boxes >/dev/null; then
  YAZILIM=boxes; VMLER=("GNOME Boxes")
fi
if [ -z "$YAZILIM" ]; then
  echo "VirtualBox, libvirt (virt-manager/Boxes) ya da VMware'de bir VM bulunamadı." >&2
  mapfile -t ADAYLAR < <(grep -ls 'qemu-system' "$HOME"/*/*.sh 2>/dev/null | head -5)
  if [ ${#ADAYLAR[@]} -gt 0 ]; then
    echo "VM'i qemu ile açan betik(ler) bulundu; kısayolu şöyle oluştur:" >&2
    for a in "${ADAYLAR[@]}"; do printf '  %s --komut "%s" "VM"\n' "$0" "${a/#$HOME/\~}" >&2; done
  else
    echo "VM'i başka bir komutla açıyorsan: $0 --komut \"KOMUT\" \"Ad\"" >&2
  fi
  exit 1
fi

VM="${1:-}"
if [ -z "$VM" ]; then
  if [ ${#VMLER[@]} -eq 1 ]; then
    VM="${VMLER[0]}"
  else
    echo "Birden çok VM var ($YAZILIM). Hangisi için kısayol istediğini VM adıyla yeniden çalıştır:"
    printf '  "%s"\n' "${VMLER[@]}"
    exit 2
  fi
elif [ "$YAZILIM" != boxes ] && [ "$YAZILIM" != komut ] && ! printf '%s\n' "${VMLER[@]}" | grep -qxF -- "$VM"; then
  echo "Bulunamadı: $VM ($YAZILIM). Mevcut VM'ler:"; printf '  %s\n' "${VMLER[@]}"; exit 2
fi
AD="$(basename "$VM" .vmx)"
KISA="vm-ac-$(kisa_ad "$AD")"; [ "$KISA" != "vm-ac-" ] || KISA="vm-ac-vm"

# ------------------------------------------------------------ açma betiği
case "$YAZILIM" in
  virtualbox)
    SIMGE=virtualbox
    GOVDE="if VBoxManage list runningvms | grep -qF \"\\\"\$VM\\\"\"; then
  notify-send -a VM \"\$VM zaten açık\" 2>/dev/null || true
else
  VBoxManage startvm \"\$VM\" --type gui
fi" ;;
  libvirt)
    SIMGE=virt-manager
    GOVDE="URI=$(printf '%q' "$URI")
[ \"\$(virsh -c \"\$URI\" domstate \"\$VM\" 2>/dev/null)\" = running ] || virsh -c \"\$URI\" start \"\$VM\"
if command -v virt-manager >/dev/null; then
  exec virt-manager --connect \"\$URI\" --show-domain-console \"\$VM\"
elif command -v virt-viewer >/dev/null; then
  exec virt-viewer --connect \"\$URI\" --wait \"\$VM\"
else
  exec gnome-boxes
fi" ;;
  vmware)
    SIMGE=vmware-workstation
    GOVDE="if vmrun list | grep -qxF \"\$VM\"; then
  notify-send -a VM \"VM zaten açık\" 2>/dev/null || true
else
  exec vmware -x \"\$VM\"
fi" ;;
  boxes)
    SIMGE=org.gnome.Boxes
    GOVDE="exec gnome-boxes" ;;
  komut)
    SIMGE=computer
    # Terminal olmadan çalışır; çıktı günlüğe gider. Hata olursa (ör. VM zaten açık, disk kilitli) bildirim.
    GOVDE="KOMUT=$(printf '%q' "$KOMUT")
GUNLUK=\"\${XDG_CACHE_HOME:-\$HOME/.cache}/$KISA.log\"
mkdir -p \"\$(dirname \"\$GUNLUK\")\"
if ! bash -c \"\$KOMUT\" >\"\$GUNLUK\" 2>&1; then
  notify-send -a VM \"\$VM açılamadı\" \"Zaten açık olabilir. Ayrıntı: \$GUNLUK\" 2>/dev/null || true
fi" ;;
esac

mkdir -p "$BIN" "$UYG"
{
  echo "#!/usr/bin/env bash"
  echo "# vm-kisayol.sh oluşturdu ($YAZILIM). Elle düzenleme; gerekirse vm-kisayol.sh'yi yeniden çalıştır."
  printf 'VM=%q\n' "$VM"
  echo "$GOVDE"
} > "$BIN/$KISA"
chmod +x "$BIN/$KISA"
bash -n "$BIN/$KISA" || hata "Oluşturulan betik bozuk: $BIN/$KISA"

cat > "$UYG/$KISA.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=VM: $AD
Comment=Geliştirme VM'ini başlatır ve penceresini açar ($YAZILIM)
Exec=$BIN/$KISA
Icon=$SIMGE
Terminal=false
Categories=System;Emulator;
EOF
command -v update-desktop-database >/dev/null && update-desktop-database "$UYG" 2>/dev/null || true

favoriler ekle "$KISA.desktop"
echo "Tamam: \"VM: $AD\" Sık Kullanılanlar'a eklendi ($YAZILIM)."
echo "Bundan sonra VM'i dock'taki simgeden ya da terminalde '$KISA' ile açabilirsin."
if [ -z "${ADIMADIM_ACMA:-}" ]; then
  echo "VM açılıyor…"
  nohup "$BIN/$KISA" >/dev/null 2>&1 &
fi
