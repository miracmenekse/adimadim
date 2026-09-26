# Çalışma düzeni: VM'de geliştir, ana makinede çalıştır

Bu dosya iki makinenin ilk kurulumunu ve günlük akışı adım adım anlatır. Ana makinede Claude Code
olmadığı için bu dosyayı orada GitHub'dan okuyup komutları kopyala-yapıştır ile çalıştırabilirsin.
Claude Code'un kuralları CLAUDE.md'de, arka plan KARARLAR.md'de, iş planı YOL_HARITASI.md'dedir.

## Düzen

```
  VM (Ubuntu 22.04)                                     Ana makine (Ubuntu 22.04)
  Claude Code geliştirir     ── git push ──► GitHub ── git pull ──►   sen çalıştırırsın
  uydurma test verisi, CPU                                      gerçek veri, Intel GPU/NPU
          ▲                                                                  │
          └────────── yalnızca hata metni (sen kopyalayıp yapıştırırsın) ────┘
```

İki makine yalnızca bu GitHub reposu üzerinden konuşur. VM'deki Claude Code ana makineyi göremez,
ana makinede Claude Code yoktur.

### Temel kural

> **Ana makinede yalnızca repodaki betikler çalışır.** Ana makinenin Ubuntu kurulumu her şeye hazır
> değil. Bu yüzden VM'de terminalde yapılan her kurulum ya da ayar (apt, pip, model indirme,
> kısayol, `~/.config` altındaki dosyalar) ya `kur.sh`'ye işlenir ya da, yalnızca bir kez
> gerekiyorsa, CHANGELOG.md'deki **"Ana makinede yapılacaklar"** bölümüne kopyala-yapıştır komut
> olarak yazılır. "VM'de çalışıyor" yetmez: ana makinede şu üç komutla aynı sonuç alınmalı:
>
>     git pull && ./kur.sh && ./test.sh

### Hangi iş nerede

| İş                                                        | VM (Claude Code)    | Ana makine (sen)                      |
|-----------------------------------------------------------|---------------------|---------------------------------------|
| Kod yazma, `./test.sh`                                    | evet                | her güncellemeden sonra `./test.sh`   |
| `./kur.sh`                                                | evet                | her güncellemeden sonra               |
| GPU / NPU ile çalıştırma ve ölçüm                         | yok (yalnızca CPU)  | evet, CHANGELOG'daki komutla          |
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

Ardından YOL_HARITASI.md'deki "Başlarken" adımlarıyla devam eder (test kaydı ister, Windows
desteğini sorar).

## 3. Ana makine: ilk kurulum (bir kez)

Ön koşul: 2. bölüm push'lanmış olmalı (GitHub'da `requirements.lock` görünmeli).

### 3.1 Temel paketler

```bash
sudo apt-get update
sudo apt-get install -y git openssh-client
```

### 3.2 GitHub erişimi

VM'dekiyle aynı blok; yalnızca anahtarın adı farklı. Bir kez çalıştır:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "adimadim-ana-makine" -f ~/.ssh/adimadim_ed25519   # parola sorar; boş bırakabilirsin
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

GitHub'da *Settings → Deploy keys → Add deploy key*: başlık `Ana makine`. **Allow write access**
kutusunu yalnızca test ses kayıtlarını bu makineden push'layacaksan işaretle (6. bölüm).
İşaretlemezsen ana makine repoya hiçbir şey yazamaz; en güvenlisi budur.

Repo public kalırsa anahtarsız da klonlayabilirsin:
`git clone https://github.com/miracmenekse/adimadim.git ~/adimadim` (push için yine anahtar gerekir).

### 3.3 Klonla

```bash
[ -e ~/adimadim ] && mv ~/adimadim ~/adimadim.eski-$(date +%Y%m%d)   # aynı adda eski bir klasör varsa kenara al
ssh -T github-adimadim      # ilk seferde "yes" yaz
git clone github-adimadim:miracmenekse/adimadim.git ~/adimadim
cd ~/adimadim
git config pull.ff only     # ana makinede birleştirme (merge) commit'i oluşmasın, yalnızca ileri sarılsın
ls requirements.lock        # "No such file" derse dur: 2. bölüm henüz push'lanmamış
```

### 3.4 Kur ve test et

Masaüstündeki bir terminalde çalıştır (SSH ile bağlıyken klavye kısayolları tanımlanamaz):

```bash
./kur.sh      # apt-get için sudo şifreni sorar
./test.sh     # sonunda "SONUÇ: testler geçti" görmelisin
.ortam/ortam.sh kontrol   # "ORTAM: fark yok" görmelisin; yoksa EKSIK/FARKLI satırlarını Claude Code'a ver
```

Bu makinede kur.sh şunları yapar (CHANGELOG, v0.1.0):

- Mevcut `~/modeller/whisper-medium-ov` modeli kullanılır, yeniden dönüştürülmez.
- `~/.config/adimadim/ayar.json`'daki mevcut değerler korunur (ör. `"cihaz": "GPU"`); yalnızca eksik
  anahtarlar eklenir.
- Eski `~/.local/bin/adimadim` kopyası `adimadim.eski` olarak yedeklenir; artık repodaki araç çalışır.
- Python paketleri ayrı bir ortama kurulur; daha önce `pip --user` ile kurulanlara dokunulmaz.

Repoyu `~/adimadim`'de tut: `adimadim` komutu ve kısayollar repo yolunu içerir. Klasörü taşırsan
`./kur.sh`'yi yeniden çalıştır.

### 3.5 GPU'da çalıştığını doğrula

```bash
arecord -f S16_LE -r 16000 -c 1 -d 5 /tmp/deneme.wav     # 5 saniye konuş
adimadim cevir /tmp/deneme.wav
```

İlk satırda `(OpenVINO / GPU)` görmelisin, ardından söylediğin metin gelir.
`OpenVINO (GPU) kullanılamadı: …` yazarsa araç CPU'daki yedek motora düşmüştür; o satırı VM'deki
Claude Code'a ver (5. bölüm).

### 3.6 VM kısayolu (isteğe bağlı)

VM'i açan bir simgeyi Sık Kullanılanlar'a (dock) ekler ve VM'i hemen açar:

```bash
~/adimadim/beceriler/vm-ana-makine/ana-makine/vm-kisayol.sh
```

Birden çok VM varsa adlarını listeler; istediğinin adını tırnak içinde ekleyerek yeniden çalıştır.
Sonra VM'i dock'taki "VM: …" simgesinden açarsın. Kaldırmak için aynı komutun sonuna `--kaldir`.

## 4. Günlük akış

**VM:**

```bash
cd ~/adimadim && git pull && claude
```

İsteğini yaz. Claude Code değişikliği yapar, `./test.sh`'yi geçirir, küçük commit'ler atar,
CHANGELOG'a "Ana makinede yapılacaklar"ı yazar; push ve sürüm etiketi için sana sorar
(`.claude/settings.json` push ve etiketi her seferinde onaya bağlar).

**Ana makine:**

```bash
cd ~/adimadim && git pull && ./kur.sh && ./test.sh && .ortam/ortam.sh kontrol
```

Sonra CHANGELOG.md'nin en üstündeki sürümün "Ana makinede yapılacaklar" maddelerini sırayla uygula.

Önceki bir sürüme dönmek için: `git checkout v0.1.0 && ./kur.sh`.
Yeniden en güncele geçmek için: `git checkout main && git pull && ./kur.sh`.

## 5. Ana makineden VM'e geri bildirim

VM'deki Claude Code'a yalnızca senin getirdiğin metin ulaşır.

- **Getir:** hata satırları, `./test.sh`'nin özet satırları, sürüm (`git log -1 --oneline`), cihaz satırı
  (ör. `(OpenVINO / GPU)`).
- **Getirme:** şirket ekranlarının görüntüsü, gerçek doküman ya da anlatım metni,
  `terimler.local.txt`'nin içeriği, müşteri bilgisi.

Şablon:

```
Ana makinede <çalıştırdığım komut> çalıştırdım. Sürüm: <git log -1 --oneline çıktısı>
Hata:
<yalnızca hata satırları>
Ortam:
<.ortam/ortam.sh kontrol çıktısı>
```

Sanallaştırma yazılımında pano paylaşımı açıksa yönünü "ana makineden VM'e" ile sınırla
(ör. VirtualBox: *Devices → Shared Clipboard → Host To Guest*); böylece VM'den ana makineye bir şey
taşınmaz, VM'e de yalnızca bilerek yapıştırdığın metin gider.

## 6. Test kayıtları: ana makineden VM'e

Önce repoyu private yap (0. bölüm) ve ana makinenin anahtarına yazma izni ver (3.2). Kayıt kuralları
testler/README.md'de.

```bash
cd ~/adimadim && git pull
arecord -f S16_LE -r 16000 -c 1 testler/ses/01.wav      # konuş, bitince Ctrl+C
echo "Müşterinin fatura döngüsünü ayın on beşine çekiyoruz." > testler/ses/01.txt
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
  `~/.config/adimadim/` altında durur ve repoya girmez.
- Eksik bir şey için elle `apt install` / `pip install` yapma. Hatayı VM'deki Claude Code'a ver,
  kur.sh'ye eklesin; böylece bir sonraki kurulumda da çalışır. Acil durumda elle bir şey kurduysan
  Claude Code'a söyle.
- `git add .` ya da `git add -A` kullanma; yalnızca `git add testler/ses/`.
- Şifresiz sudo tanımlama.

VM'e:

- Şirket verisi taşıma: ekran görüntüsü, doküman, `terimler.local.txt`, müşteri bilgisi.

## 8. Sorun giderme

| Belirti | Çözüm |
|---|---|
| `Permission denied (publickey)` | Deploy key eklenmemiş ya da adres `github-adimadim` yerine `github.com` yazılmış. `ssh -T github-adimadim` ile dene. |
| `connect to host github.com port 22: Connection timed out` (kurumsal ağ) | `~/.ssh/config`'teki `github-adimadim` bloğunda `HostName ssh.github.com` yaz ve altına `Port 443` ekle. |
| `git pull`: `untracked working tree files would be overwritten … requirements.lock` | Kilit dosyası push'lanmadan kur.sh çalışmış: `rm requirements.lock && git pull && ./kur.sh` |
| `git pull`: `Your local changes … would be overwritten` | Ana makinede bir repo dosyası değişmiş. `git status` ile bak; değişikliği atmak için `git restore <dosya>`. |
| `git pull`: `Not possible to fast-forward` | Push'lanmamış bir commit var (ör. test kayıtları): `git pull --rebase && git push` |
| `adimadim: command not found` | `source ~/.profile` ya da oturumu kapatıp aç. |
| VM'de kur.sh `sudo` şifresi istiyor | 1.3'ü uygula. |
| Ctrl+Alt+S / Ctrl+Alt+N çalışmıyor | Masaüstündeki terminalde `adimadim kisayol`. |
| Repo klasörünü taşıdın | `./kur.sh`'yi yeniden çalıştır. |
