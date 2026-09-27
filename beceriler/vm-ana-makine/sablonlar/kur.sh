#!/usr/bin/env bash
# <PROJE> kurulumu — VM'de ve ana makinede aynı komut: ./kur.sh
# Defalarca çalıştırmak güvenlidir: kurulu olanı atlar, eksiği tamamlar, kullanıcı ayarlarını ezmez.
# Kural: kodun ya da testlerin çağırdığı her dış komutun paketi PAKETLER'de; VM'de elle kurulan her şey buraya.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AD="<proje>"                                             # komut ve klasör adı
VENV="${PROJE_VENV:-$HOME/.local/share/$AD/venv}"
AYAR_DIZINI="${XDG_CONFIG_HOME:-$HOME/.config}/$AD"
BIN="$HOME/.local/bin"

PAKETLER=(python3-venv git)                              # apt paketleri
GRUPLAR=()                                               # ör. (render video): kullanıcının girmesi gereken gruplar

baslik() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
uyari()  { printf '\033[33mUyarı:\033[0m %s\n' "$*"; }

# ------------------------------------------------------------ 1. sistem paketleri
baslik "Sistem paketleri"
if [ -r /etc/os-release ]; then . /etc/os-release; fi
[ "${VERSION_ID:-}" = "22.04" ] || uyari "Ubuntu 22.04 bekleniyordu, bulunan: ${PRETTY_NAME:-bilinmiyor}."
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

# ------------------------------------------------------------ 2. kullanıcı grupları
if [ ${#GRUPLAR[@]} -gt 0 ]; then
  baslik "Kullanıcı grupları"
  for g in "${GRUPLAR[@]}"; do
    if id -nG | tr ' ' '\n' | grep -qx "$g"; then echo "Tamam: $g"
    else sudo usermod -aG "$g" "$USER"; uyari "$g grubuna eklendi; etkili olması için oturumu kapatıp aç."; fi
  done
fi

# ------------------------------------------------------------ 3. python ortamı (kilit dosyasıyla)
if [ -f "$REPO/requirements.txt" ]; then
  baslik "Python ortamı: $VENV"
  [ -x "$VENV/bin/python" ] || { mkdir -p "$(dirname "$VENV")"; python3 -m venv "$VENV"; }
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  if [ -f "$REPO/requirements.lock" ]; then
    "$VENV/bin/python" -m pip install -r "$REPO/requirements.lock"
  else
    "$VENV/bin/python" -m pip install -r "$REPO/requirements.txt"
    "$VENV/bin/python" -m pip freeze > "$REPO/requirements.lock"
    uyari "requirements.lock oluşturuldu. VM'deysen commit'le; ana makinedeysen sil ve VM'dekini bekle."
  fi
fi

# ------------------------------------------------------------ 4. ayarlar (var olanı ezme)
baslik "Ayarlar: $AYAR_DIZINI"
mkdir -p "$AYAR_DIZINI"
if [ -f "$REPO/ayar.ornek.json" ] && [ ! -f "$AYAR_DIZINI/ayar.json" ]; then
  cp "$REPO/ayar.ornek.json" "$AYAR_DIZINI/ayar.json"; echo "Varsayılan ayar yazıldı."
else
  echo "Tamam."
fi

# ------------------------------------------------------------ 5. komut
# Örnek: repodaki giriş noktasını ~/.local/bin/$AD olarak yayınla. Projeye göre düzenle ya da sil.
# baslik "Komut: $BIN/$AD"
# mkdir -p "$BIN"
# printf '#!/usr/bin/env bash\nexec "%s" "%s" "$@"\n' "$VENV/bin/python" "$REPO/$AD.py" > "$BIN/$AD"
# chmod +x "$BIN/$AD"
case ":$PATH:" in *":$BIN:"*) ;; *) uyari "$BIN PATH'te değil; oturumu kapatıp açınca eklenir." ;; esac

baslik "Kurulum bitti. Sıradaki adım: ./test.sh"
