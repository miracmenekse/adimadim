# Çalışma düzeni: VM'de geliştir, ana makinede çalıştır

Bu dosya iki makinenin ilk kurulumunu ve günlük akışı adım adım anlatır. Ana makine Windows'tur;
orada Claude Code olmadığı için bu dosyayı GitHub'dan okuyup komutları kopyala-yapıştır ile
çalıştırabilirsin. Claude Code'un kuralları CLAUDE.md'de, arka plan KARARLAR.md'de, iş planı
YOL_HARITASI.md'dedir.

## Düzen

```
  VM (Ubuntu 22.04)                                     Ana makine (Windows 10/11)
  Claude Code geliştirir     ── git push ──► GitHub ── git pull ──►   sen çalıştırırsın
  uydurma test verisi, CPU                                      gerçek veri, Intel GPU/NPU
          ▲                                                                  │
          └────────── yalnızca hata metni (sen kopyalayıp yapıştırırsın) ────┘
```

İki makine yalnızca bu GitHub reposu üzerinden konuşur. VM'deki Claude Code ana makineyi göremez,
ana makinede Claude Code yoktur. WSL yalnızca geliştirme içindir; kullanımda yerel Windows Python
3.10 çalışır.

### Temel kural

> **Ana makinede yalnızca repodaki betikler çalışır.** Ana makinenin Windows kurulumu her şeye hazır
> değil. Bu yüzden VM'de terminalde yapılan her kurulum ya da ayar (paket, pip, model indirme,
> kısayol, `%APPDATA%\adimadim` altındaki dosyalar) ya `kur.ps1`'ye işlenir ya da, yalnızca bir kez
> gerekiyorsa, CHANGELOG.md'deki **"Ana makinede yapılacaklar"** bölümüne kopyala-yapıştır komut
> olarak yazılır. "VM'de çalışıyor" yetmez: ana makinede şu üç komutla aynı sonuç alınmalı:
>
>     git pull; .\kur.ps1; .\test.ps1

### Hangi iş nerede

| İş                                                        | VM (Claude Code)    | Ana makine (sen)                      |
|-----------------------------------------------------------|---------------------|---------------------------------------|
| Kod yazma, `./test.sh`                                    | evet                | her güncellemeden sonra `.\test.ps1`  |
| `./kur.sh`                                                | evet                | her güncellemeden sonra `.\kur.ps1`   |
| GPU / NPU ile çalıştırma ve ölçüm                         | yok (yalnızca CPU)  | evet, `adimadim cevir` ile            |
| Gerçek mikrofonla test kaydı                              | hayır               | evet (6. bölüm)                       |
| Gerçek şirket ekranları, dokümanlar, `terimler.local.txt` | **asla**            | evet                                  |
| `git push`                                                | evet, senin onayınla | yalnızca `testler/ses/` kayıtları    |
| Çekirdek, sürücü, ses ayarı gibi sistem değişiklikleri    | hayır               | yalnızca sen, önce konuşarak          |

## 0. GitHub'da bir kez (tarayıcıdan)

1. **Görünürlük.** Repo şu an herkese açık (public). Test ses kayıtların (kendi sesin) ve işine dair
   notlar (KARARLAR.md, ör. ana makinedeki güvenlik ajanı) buraya girdiği için **private** yapman
   önerilir: *Settings → General → Danger Zone → Change visibility*.
2. **Ana dal.** İlk içerik `claude/ubuntu-vm-host-setup-xtctcd` dalıyla geldi ve varsayılan dal oldu.
   Adını `main` yap: *Settings → General → Default branch → kalem simgesi (Rename branch) → `main`*.
   Bu rehberdeki komutlar `main` dalını varsayar.
3. **Erişim anahtarları** aşağıda her makine için ayrı ayrı eklenir (deploy key: yalnızca bu repoya
   erişebilen anahtar).

## 1. VM: ilk kurulum (bir kez, sen yaparsın)

Kaynak: en az 8 GB RAM (Faz 2'deki büyük modeli dönüştürmek için 12-16 GB daha rahat) ve proje için
yaklaşık 25 GB boş disk (Python ortamı ve modeller; tahmini). VM'e GPU aktarımı gerekmez.

### 1.1 Temel paketler

```bash
sudo apt-get update
sudo apt-get install -y git curl openssh-client
git config --global user.name "Adın Soyadın"
git config --global user.email "GITHUB_NOREPLY_ADRESIN"   # GitHub → Settings → Emails'teki noreply adresi
```

### 1.2 GitHub erişimi (yalnızca bu repoya yazabilen anahtar)

Bu blok bir kez çalıştırılır:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "adimadim-vm" -f ~/.ssh/adimadim_ed25519 -N ""
cat >> ~/.ssh/config <<'EOF'

Host github-adimadim
    HostName github.com
    User git
    IdentityFile ~/.ssh/adimadim_ed25519
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
cat ~/.ssh/adimadim_ed25519.pub
```

Son komutun yazdığı tek satırı GitHub'da *Settings → Deploy keys → Add deploy key*'e yapıştır:
başlık `VM`, **Allow write access işaretli**. Böylece VM'deki Claude Code bu anahtarla yalnızca bu
repoya erişir; GitHub hesabındaki diğer repolara erişemez.

```bash
ssh -T github-adimadim      # ilk seferde "yes" yaz
# Beklenen: Hi miracmenekse/adimadim! You've successfully authenticated, but GitHub does not provide shell access.
git clone github-adimadim:miracmenekse/adimadim.git ~/adimadim
```

### 1.3 kur.sh için şifresiz apt-get (yalnızca VM'de)

Claude Code'un `kur.sh`'yi kendisi çalıştırabilmesi için (CLAUDE.md, "İki ortam"):

```bash
echo "$USER ALL=(root) NOPASSWD: /usr/bin/apt-get" | sudo tee /etc/sudoers.d/adimadim-apt
sudo chmod 440 /etc/sudoers.d/adimadim-apt
sudo visudo -c              # "parsed OK" görmelisin
```

VM izole olduğu için bu kabul edilebilir. **Ana makinede yapma.**

### 1.4 Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Yeni bir terminal aç ve `claude --version` ile kurulumu doğrula. İlk açılışta tarayıcıdan giriş ister.

### 1.5 vm-ana-makine becerisi ve fark tabanı

Bu repodaki `beceriler/vm-ana-makine`, VM ile ana makine arasındaki farkı kapatan Claude Code
becerisidir (skill); proje ne olursa olsun geçerlidir. VM'de bir kez kullanıcı düzeyine bağla ve
VM'in şimdiki (proje kurulumundan önceki) hâlini taban olarak kaydet:

```bash
mkdir -p ~/.claude/skills
ln -sfn ~/adimadim/beceriler/vm-ana-makine ~/.claude/skills/vm-ana-makine   # git pull ile güncel kalır
~/.claude/skills/vm-ana-makine/ortam.sh taban
```

Taban, `kur.sh`'den önce alınmalı: sonradan VM'e ne kurulursa `ortam.sh kaydet` onu görür, `denetle`
kur betiğine işlenmemiş olanları gösterir, ana makinede `kontrol` eksikleri yazar. Başka projelerde
Claude Code bu beceriyle aynı düzeni (`.ortam/`, kur betiği, bu belgenin bir benzeri) kendisi kurar.

### 1.6 (İsteğe bağlı) Temiz anlık görüntü

Bu noktada VM'in anlık görüntüsünü (snapshot) al. Bu hâli, ana makinenin "kur.sh'den önceki" durumuna
benzer. Büyük bir sürümden önce bu görüntüden bir kopya açıp `git clone … && ./kur.sh && ./test.sh`
denersen kur.sh'nin eksik kurulu bir makinede de çalıştığını görmüş olursun.

## 2. VM: ilk tur (Claude Code yapar)

```bash
cd ~/adimadim && claude
```

Claude Code'a şunu yaz:

> CLAUDE.md, KARARLAR.md, YOL_HARITASI.md ve CALISMA_DUZENI.md'yi oku. CALISMA_DUZENI.md'deki
> "VM: ilk tur" adımlarını uygula; push'tan önce bana sor.

Claude Code'un bu turda yapacakları:

1. `./kur.sh`: sistem paketleri, Python ortamı (`~/.local/share/adimadim/venv`) ve
   `openai/whisper-medium` modelinin OpenVINO'ya dönüştürülmesi. Birkaç GB indirir, ilk seferde uzun
   sürer. Bu adım `requirements.lock`'u üretir.
2. `./test.sh` geçer.
3. `requirements.lock` commit'lenir. Ana makine birebir aynı sürümleri bu dosyadan kurar.
   **Bu dosya push'lanmadan ana makinede `kur.sh` çalıştırma.**
4. `.ortam/ortam.sh kaydet && .ortam/ortam.sh denetle`: VM'e kur.sh ile eklenenler `.ortam/vm.txt`'ye
   yazılır ve commit'lenir; `denetle` kur.sh'ye işlenmemiş bir şey bırakmaz.
5. Onayınla `git push`; istersen sürüm etiketi: `git tag v0.1.0 && git push origin v0.1.0`.

Ardından YOL_HARITASI.md'deki "Başlarken" adımlarıyla devam eder (test kaydı ister; Windows kararı
verildi, ana makine Windows).

## 3. Ana makine: ilk kurulum (Windows, bir kez)

Ön koşul: 2. bölüm push'lanmış olmalı (GitHub'da `requirements.lock` ve `kur.ps1` görünmeli).

### 3.1 Temel paketler

Windows 10/11, PowerShell 5.1+ ve Git for Windows yeterli. Python'u `kur.ps1` uv ile kurar; yönetici
hakkı gerekmez.

```powershell
git --version
```

### 3.2 GitHub erişimi

VM'dekiyle aynı mantık; yalnızca anahtarın adı farklı. Bir kez çalıştır:

```powershell
New-Item -ItemType Directory -Force $HOME\.ssh | Out-Null
ssh-keygen -t ed25519 -C "adimadim-ana-makine" -f $HOME\.ssh\adimadim_ed25519   # parola sorar; boş bırakabilirsin
Add-Content $HOME\.ssh\config @"

Host github-adimadim
    HostName github.com
    User git
    IdentityFile ~/.ssh/adimadim_ed25519
    IdentitiesOnly yes
"@
Get-Content $HOME\.ssh\adimadim_ed25519.pub
```

GitHub'da *Settings → Deploy keys → Add deploy key*: başlık `Ana makine`. **Allow write access**
kutusunu yalnızca test ses kayıtlarını bu makineden push'layacaksan işaretle (6. bölüm).
İşaretlemezsen ana makine repoya hiçbir şey yazamaz; en güvenlisi budur.

Repo public kalırsa anahtarsız da klonlayabilirsin:
`git clone https://github.com/miracmenekse/adimadim.git $HOME\adimadim` (push için yine anahtar gerekir).

### 3.3 Klonla

```powershell
cd $HOME
if (Test-Path .\adimadim) { Rename-Item .\adimadim "adimadim.eski-$(Get-Date -Format yyyyMMdd)" }
ssh -T github-adimadim      # ilk seferde "yes" yaz
git clone github-adimadim:miracmenekse/adimadim.git adimadim
cd adimadim
git config pull.ff only     # ana makinede birleştirme (merge) commit'i oluşmasın, yalnızca ileri sarılsın
Test-Path requirements.lock # False derse dur: 2. bölüm henüz push'lanmamış
```

### 3.4 Kur ve test et

```powershell
.\kur.ps1     # uv + Python 3.10, bağımlılıklar, model dönüşümü, masaüstü kısayolu, klavye kısayolları
.\test.ps1    # sonunda "SONUÇ: testler geçti" görmelisin
```

`kur.ps1` tekrar çalıştırılabilir; kurulu olanı atlar, eksiği tamamlar. Şunları yapar:

- Python 3.10'u uv ile `%LOCALAPPDATA%\adimadim\venv` ortamına kurar; yönetici hakkı istemez.
- `%APPDATA%\adimadim\ayar.json` varsa mevcut değerler korunur (ör. `"cihaz": "GPU"`); yalnızca eksik
  anahtarlar eklenir.
- OpenVINO modeli hazırsa yeniden dönüştürmez; değilse `optimum-cli` ile bir kez dönüştürür.
- Masaüstüne `adımadım.lnk` kısayolunu ve `adimadim.cmd` komutunu ekler; klavye kısayollarını tanımlar.

PowerShell betiği engellerse: `powershell -ExecutionPolicy Bypass -File .\kur.ps1`.

Repoyu `$HOME\adimadim`'de tut: `adimadim` komutu ve kısayollar repo yolunu içerir. Klasörü taşırsan
`.\kur.ps1`'yi yeniden çalıştır.

### 3.5 GPU/NPU'da çalıştığını doğrula

Kısa bir WAV dosyasını (16 kHz, tek kanal) `kayit.wav` olarak kaydet, sonra:

```powershell
adimadim cevir kayit.wav
```

İlk satırda `(OpenVINO / GPU)` ya da `(OpenVINO / NPU)` görmelisin, ardından söylediğin metin gelir.
`OpenVINO (GPU) kullanılamadı: …` yazarsa araç CPU'daki yedek motora düşmüştür; o satırı VM'deki
Claude Code'a ver (5. bölüm).

### 3.6 Eski: Ubuntu ana makine (2026-11-11'e kadar)

Ubuntu 22.04 ana makine düzeni Windows'a geçilince bırakıldı. Kurulum `./kur.sh`, test `./test.sh`,
güncelleme `git pull && ./kur.sh && ./test.sh`; GPU doğrulaması
`arecord -f S16_LE -r 16000 -c 1 -d 5 /tmp/deneme.wav && adimadim cevir /tmp/deneme.wav`.
Dock'taki **adımadım güncelle** düğmesi ve `vm-kisayol.sh` yalnız bu düzende vardı; ayrıntılar git
geçmişinde.

## 4. Günlük akış

**VM:**

```bash
cd ~/adimadim && git pull && claude
```

İsteğini yaz. Claude Code değişikliği yapar, `./test.sh`'yi geçirir, küçük commit'ler atar,
CHANGELOG'a "Ana makinede yapılacaklar"ı yazar; push ve sürüm etiketi için sana sorar
(`.claude/settings.json` push ve etiketi her seferinde onaya bağlar).

**Ana makine (Windows):** PowerShell'de:

```powershell
cd $HOME\adimadim
git pull; .\kur.ps1; .\test.ps1
```

`kur.ps1` değişiklik yoksa hızlı geçer; kurulu olanı atlar, eksiği tamamlar. Hata olursa çıktıyı
VM'deki Claude Code'a ilet (5. bölüm). Sonra CHANGELOG.md'nin en üstündeki sürümün **"Ana makinede
yapılacaklar"** maddelerini sırayla uygula.

Önceki bir sürüme dönmek için: `git checkout v0.1.0; .\kur.ps1`.
Yeniden en güncele geçmek için: `git checkout main; git pull; .\kur.ps1`.

## 5. Ana makineden VM'e geri bildirim

VM'deki Claude Code'a yalnızca senin getirdiğin metin ulaşır.

- **Getir:** hata satırları, `.\test.ps1`'nin özet satırları, sürüm (`git log -1 --oneline`), cihaz satırı
  (ör. `(OpenVINO / GPU)`).
- **Getirme:** şirket ekranlarının görüntüsü, gerçek doküman ya da anlatım metni,
  `terimler.local.txt`'nin içeriği, müşteri bilgisi.

Şablon:

```
Ana makinede <çalıştırdığım komut> çalıştırdım. Sürüm: <git log -1 --oneline çıktısı>
Hata:
<yalnızca hata satırları>
Ortam:
<Windows sürümü; PowerShell sürümü>
```

Sanallaştırma yazılımında pano paylaşımı açıksa yönünü "ana makineden VM'e" ile sınırla
(ör. VirtualBox: *Devices → Shared Clipboard → Host To Guest*); böylece VM'den ana makineye bir şey
taşınmaz, VM'e de yalnızca bilerek yapıştırdığın metin gider.

## 6. Test kayıtları: ana makineden VM'e

Önce repoyu private yap (0. bölüm) ve ana makinenin anahtarına yazma izni ver (3.2). Kayıt kuralları
testler/README.md'de.

```powershell
cd $HOME\adimadim
git pull
# Kaydı 16 kHz, tek kanal WAV olarak testler\ses\01.wav dosyasına al (herhangi bir kaydedici olur)
"Müşterinin fatura döngüsünü ayın on beşine çekiyoruz." | Set-Content testler\ses\01.txt -Encoding UTF8
# … 10-20 kayıt
git status --short          # yalnızca testler/ses/ altındaki dosyalar görünmeli
git add testler/ses/
git commit -m "Test kayıtları eklendi"
git push
```

Sonra VM'de `git pull`; Claude Code ölçümleri bu kayıtlarla yapar.

## 7. Yapılmayacaklar

Ana makinede:

- Repodaki dosyaları elle düzenleme; değişiklik VM'den gelir. Makineye özel ayarların
  `%APPDATA%\adimadim\` altında durur ve repoya girmez.
- Eksik bir şey için elle `winget` / `pip install` yapma. Hatayı VM'deki Claude Code'a ver,
  `kur.ps1`'ye eklesin; böylece bir sonraki kurulumda da çalışır. Acil durumda elle bir şey
  kurduysan Claude Code'a söyle.
- `git add .` ya da `git add -A` kullanma; yalnızca `git add testler/ses/`.
- Yönetici haklarıyla kurulum yapma; `kur.ps1` buna gerek duymaz.

VM'e:

- Şirket verisi taşıma: ekran görüntüsü, doküman, `terimler.local.txt`, müşteri bilgisi.

## 8. Sorun giderme

| Belirti | Çözüm |
|---|---|
| `Permission denied (publickey)` | Deploy key eklenmemiş ya da adres `github-adimadim` yerine `github.com` yazılmış. `ssh -T github-adimadim` ile dene. |
| `connect to host github.com port 22: Connection timed out` (kurumsal ağ) | `~/.ssh/config`'teki `github-adimadim` bloğunda `HostName ssh.github.com` yaz ve altına `Port 443` ekle. |
| `git pull`: `untracked working tree files would be overwritten … requirements.lock` | Kilit dosyası push'lanmadan kur betiği çalışmış: `Remove-Item requirements.lock; git pull; .\kur.ps1` |
| `git pull`: `Your local changes … would be overwritten` | Ana makinede bir repo dosyası değişmiş. `git status` ile bak; değişikliği atmak için `git restore <dosya>`. |
| `git pull`: `Not possible to fast-forward` | Push'lanmamış bir commit var (ör. test kayıtları): `git pull --rebase; git push` |
| `'adimadim' is not recognized` | Oturumu kapatıp aç ya da `$env:Path`'e `%USERPROFILE%\.local\bin` ekle. |
| PowerShell betiği engelliyor | `powershell -ExecutionPolicy Bypass -File .\kur.ps1` ya da `.\test.ps1`. |
| VM'de kur.sh `sudo` şifresi istiyor | 1.3'ü uygula. |
| Ctrl+Alt+S / Ctrl+Alt+N çalışmıyor | `adimadim kisayol` komutunu çalıştır. |
| Repo klasörünü taşıdın | `.\kur.ps1`'yi yeniden çalıştır. |
