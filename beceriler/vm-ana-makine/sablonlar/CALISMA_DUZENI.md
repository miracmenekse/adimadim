# Çalışma düzeni: VM'de geliştir, ana makinede çalıştır

<!-- vm-ana-makine becerisinin şablonu. <PROJE>, <SAHIP>, <REPO>, <KUR>, <TEST> yer tutucularını doldur;
     projeye özgü adımları (donanım doğrulaması, ilk veri, masaüstü kısayolu…) ilgili bölüme ekle. -->

Bu dosya iki makinenin ilk kurulumunu ve günlük akışı anlatır. Ana makinede Claude Code olmadığı için
orada bu dosyayı GitHub'dan okuyup komutları kopyala-yapıştır ile çalıştır.

```
  VM: Claude Code geliştirir ── git push ──► GitHub ── git pull ──► Ana makine: sen çalıştırırsın
        ▲                                                                   │
        └──── yalnızca hata metni ve `.ortam/ortam.sh kontrol` çıktısı ─────┘
```

**Temel kural:** Ana makinede yalnızca repodaki betikler çalışır. VM'de yapılan her kurulum ya da ayar
`<KUR>`'a ya da CHANGELOG'daki "Ana makinede yapılacaklar"a girer. Güncelleme her zaman:

    git pull && <KUR> && <TEST>

## 0. GitHub'da bir kez

- Repo gerçek veriye yakın bir şey içerecekse **private** yap (*Settings → General → Change visibility*).
- Ana dal `main`. Her makineye ayrı bir deploy key eklenir (*Settings → Deploy keys*).

## 1. VM: ilk kurulum (bir kez)

```bash
sudo apt-get update && sudo apt-get install -y git curl openssh-client
git config --global user.name "Adın Soyadın"
git config --global user.email "GITHUB_NOREPLY_ADRESIN"

mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "<REPO>-vm" -f ~/.ssh/<REPO>_ed25519 -N ""
cat >> ~/.ssh/config <<'EOF'

Host github-<REPO>
    HostName github.com
    User git
    IdentityFile ~/.ssh/<REPO>_ed25519
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
cat ~/.ssh/<REPO>_ed25519.pub     # GitHub → Deploy keys → "VM", Allow write access İŞARETLİ
ssh -T github-<REPO>              # ilk seferde "yes"
git clone github-<REPO>:<SAHIP>/<REPO>.git ~/<REPO>
```

Kur betiğini Claude Code'un çalıştırabilmesi için yalnızca VM'de şifresiz apt-get (ana makinede YAPMA):

```bash
echo "$USER ALL=(root) NOPASSWD: /usr/bin/apt-get" | sudo tee /etc/sudoers.d/<REPO>-apt
sudo chmod 440 /etc/sudoers.d/<REPO>-apt && sudo visudo -c
```

Claude Code ve fark ölçerin tabanı (proje işlerinden ÖNCE; bu an ana makinenin kurulum öncesine benzer).
`vm-ana-makine` becerisi VM'de `~/.claude/skills/` altında kurulu olmalı:

```bash
curl -fsSL https://claude.ai/install.sh | bash
~/.claude/skills/vm-ana-makine/ortam.sh taban     # VM'de bir kez; tüm projeler için geçerli, varsa atlar
```

## 2. VM: ilk tur (Claude Code yapar)

`cd ~/<REPO> && claude` ve: *"CLAUDE.md ve CALISMA_DUZENI.md'yi oku, `<KUR>` ve `<TEST>`'i çalıştır,
kilit dosyalarını ve `.ortam/ortam.sh kaydet` çıktısını commit'le, `denetle` temiz olsun; push'tan önce
bana sor."*

## 3. Ana makine: ilk kurulum (bir kez)

Ön koşul: 2. bölüm push'lanmış olmalı (kilit dosyaları ve `.ortam/vm.txt` GitHub'da görünmeli).

```bash
sudo apt-get update && sudo apt-get install -y git openssh-client
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "<REPO>-ana-makine" -f ~/.ssh/<REPO>_ed25519
cat >> ~/.ssh/config <<'EOF'

Host github-<REPO>
    HostName github.com
    User git
    IdentityFile ~/.ssh/<REPO>_ed25519
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
cat ~/.ssh/<REPO>_ed25519.pub     # GitHub → Deploy keys → "Ana makine"; yazma izni yalnızca gerekiyorsa
ssh -T github-<REPO>
git clone github-<REPO>:<SAHIP>/<REPO>.git ~/<REPO>
cd ~/<REPO>
git config pull.ff only
<KUR>
<TEST>
.ortam/ortam.sh kontrol           # "ORTAM: fark yok" görmelisin
```

## 4. Günlük akış

- **VM:** `cd ~/<REPO> && git pull && claude`. Claude Code değiştirir, test eder, `ortam.sh kaydet/denetle`
  ile farkı kapatır, CHANGELOG'a ana makine adımlarını yazar, push için sorar.
- **Ana makine:** `cd ~/<REPO> && git pull && <KUR> && <TEST> && .ortam/ortam.sh kontrol`, ardından
  CHANGELOG'un en üstündeki "Ana makinede yapılacaklar".

## 5. Ana makineden VM'e geri bildirim

VM'deki Claude Code'a yapıştır:

```
Sürüm: <git log -1 --oneline>
Komut: <çalıştırdığım komut>
Hata: <yalnızca hata satırları>
Ortam: <.ortam/ortam.sh kontrol çıktısı>
```

Getirme: şirket ekranları, gerçek doküman/veri, müşteri bilgisi, özel terim listeleri.

## 6. Yapılmayacaklar (ana makinede)

- Repo dosyalarını elle düzenleme; `git add .` / `git add -A` kullanma.
- Eksik bir şeyi elle kurup geçme: hatayı Claude Code'a ver, kur betiğine eklesin.
- Şifresiz sudo tanımlama.
