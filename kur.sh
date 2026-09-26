#!/usr/bin/env bash
# adımadım kurulumu — VM'de ve ana makinede aynı komut.
# Defalarca çalıştırmak güvenlidir: kurulu olanı atlar, eksiği tamamlar,
# ayar.json'daki mevcut değerlere dokunmaz.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ADIMADIM_VENV:-$HOME/.local/share/adimadim/venv}"
PY="$VENV/bin/python"
AYAR="${XDG_CONFIG_HOME:-$HOME/.config}/adimadim/ayar.json"
BIN="$HOME/.local/bin"
TORCH_INDEX="https://download.pytorch.org/whl/cpu"  # PyTorch'un CPU sürümü: CUDA paketleri inmesin

baslik() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
uyari()  { printf '\033[33mUyarı:\033[0m %s\n' "$*"; }
ayar_oku() { "$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ""))' "$AYAR" "$1"; }

# ------------------------------------------------------------------ 1. sistem paketleri
baslik "Sistem paketleri"
if [ -r /etc/os-release ]; then . /etc/os-release; fi
[ "${VERSION_ID:-}" = "22.04" ] || uyari "Ubuntu 22.04 bekleniyordu, bulunan: ${PRETTY_NAME:-bilinmiyor}. Devam ediliyor."
PAKETLER=(python3-venv git gnome-screenshot zenity pandoc alsa-utils libnotify-bin)
EKSIK=()
for p in "${PAKETLER[@]}"; do
  dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "install ok installed" || EKSIK+=("$p")
done
if [ ${#EKSIK[@]} -gt 0 ]; then
  echo "Kurulacak: ${EKSIK[*]}"
  sudo apt-get update
  sudo apt-get install -y "${EKSIK[@]}"
else
  echo "Tamam."
fi

# ------------------------------------------------------------------ 2. python ortamı
baslik "Python ortamı: $VENV"
[ -x "$PY" ] || { mkdir -p "$(dirname "$VENV")"; python3 -m venv "$VENV"; }
"$PY" -m pip install --quiet --upgrade pip   # 22.04'ün pip'indeki çözümleyici hatasına karşı
if [ -f "$REPO/requirements.lock" ]; then
  echo "Birebir sürümler kuruluyor (requirements.lock)…"
  "$PY" -m pip install --extra-index-url "$TORCH_INDEX" -r "$REPO/requirements.lock"
else
  echo "requirements.lock yok: sürümler çözülecek ve kilit dosyası üretilecek."
  if grep -qiE '^optimum-intel' "$REPO/requirements.txt"; then
    "$PY" -m pip install --index-url "$TORCH_INDEX" torch torchvision
  fi
  "$PY" -m pip install -r "$REPO/requirements.txt"
  "$PY" -m pip freeze | grep -viE '^pkg[-_]resources==' > "$REPO/requirements.lock"
  echo "requirements.lock oluşturuldu. Commit'le ki diğer makine birebir aynı sürümleri kursun."
fi

# ------------------------------------------------------------------ 3. ayarlar
baslik "Ayarlar: $AYAR"
"$PY" "$REPO/araclar/ayar_kur.py" "$REPO/ayar.ornek.json" "$AYAR"

# ------------------------------------------------------------------ 4. konuşma modeli
baslik "Konuşma modeli (OpenVINO)"
OV_KAYNAK="$(ayar_oku ov_kaynak)"
OV_MODEL="$(ayar_oku ov_model)"
OV_MODEL="${OV_MODEL/#\~/$HOME}"
if [ -z "$OV_KAYNAK" ] || [ -z "$OV_MODEL" ]; then
  uyari "ayar.json'da ov_kaynak / ov_model boş; model adımı atlandı."
elif [ -f "$OV_MODEL/openvino_encoder_model.xml" ]; then
  echo "Hazır: $OV_MODEL"
elif [ ! -x "$VENV/bin/optimum-cli" ]; then
  uyari "optimum-cli kurulu değil; model dönüştürülemedi (requirements.txt'i kontrol et)."
else
  echo "$OV_KAYNAK → $OV_MODEL dönüştürülüyor (bir kez yapılır, birkaç dakika sürer)…"
  mkdir -p "$(dirname "$OV_MODEL")"
  "$VENV/bin/optimum-cli" export openvino --model "$OV_KAYNAK" --weight-format fp16 "$OV_MODEL"
fi

# ------------------------------------------------------------------ 5. komut
baslik "Komut: $BIN/adimadim"
mkdir -p "$BIN"
if [ -e "$BIN/adimadim" ] && ! grep -q "adimadim-sarmalayici" "$BIN/adimadim" 2>/dev/null; then
  mv "$BIN/adimadim" "$BIN/adimadim.eski"
  echo "Önceki kopya yedeklendi: $BIN/adimadim.eski"
fi
cat > "$BIN/adimadim" <<SARMALAYICI
#!/usr/bin/env bash
# adimadim-sarmalayici — kur.sh oluşturdu. Elle düzenleme; gerekirse kur.sh'yi yeniden çalıştır.
exec "$PY" "$REPO/adimadim.py" "\$@"
SARMALAYICI
chmod +x "$BIN/adimadim"
echo "Tamam: adimadim → $REPO/adimadim.py"
case ":$PATH:" in *":$BIN:"*) ;; *) uyari "$BIN PATH'te değil; oturumu kapatıp açınca eklenir." ;; esac

# ------------------------------------------------------------------ 6. kısayollar
baslik "Klavye kısayolları"
if [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] && command -v gsettings >/dev/null 2>&1; then
  "$BIN/adimadim" kisayol || uyari "Kısayollar tanımlanamadı; sonra 'adimadim kisayol' ile dene."
else
  uyari "Masaüstü oturumu bulunamadı; kısayolları sonra 'adimadim kisayol' ile tanımla."
fi

baslik "Kurulum bitti. Sıradaki adım: ./test.sh"
