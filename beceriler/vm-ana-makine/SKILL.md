---
name: vm-ana-makine
description: Kodun bir VM'de Claude Code ile geliştirildiği, git (GitHub) üzerinden ayrı bir ana makineye taşınıp orada kullanıcı tarafından çalıştırıldığı HER projede kullan; iki makine arasındaki kurulum farkını kapatır. Ana makinede Claude Code yoktur, Ubuntu kurulumu eksik olabilir, gerçek veri oradadır. Şu anlarda yükle - yeni bir projeye başlarken ya da bu düzeni kurarken; apt/pip/snap/npm ile bir şey kurmadan, sistem ayarı değiştirmeden, yeni bir dış komut ya da bağımlılık eklemeden önce; commit, push ya da sürüm etiketinden önce; kullanıcı ana makineden hata ya da "ana makinede çalışmıyor", "VM'de çalışıyor ama", "fark", "host" gibi bir geri bildirim getirdiğinde.
disable-model-invocation: true
---

# VM ↔ ana makine: farkı kapat

## Düzen

- **VM (sen buradasın):** geliştirme, testler, uydurma veri. Genellikle GPU yok, gerçek mikrofon/donanım yok.
- **Ana makine:** kullanım. Claude Code YOK; komutları kullanıcı kopyala-yapıştır ile çalıştırır.
  Ubuntu kurulumu eksik olabilir. Gerçek şirket verisi yalnızca oradadır.
- **Köprü:** yalnızca git. VM push'lar, ana makine `git pull` yapar. Ana makineden sana gelen tek şey
  kullanıcının yapıştırdığı metindir (hata satırları, `.ortam/ortam.sh kontrol` çıktısı).

## Altın kural

Ana makinede yalnızca repodaki betikler çalışır; her güncelleme şu kalıpla uygulanabilmeli:

    git pull && <kur betiği> && <test betiği>

Bu yüzden VM'de terminalde yaptığın **her** kurulum ya da ayar (apt, pip, snap, npm, model/veri
indirme, `~/.config` ya da `~/.local` altındaki dosyalar, gsettings, kullanıcı grupları, PATH)
şu ikisinden birine girer, başkasına değil:

1. **Kur betiğine** (tercih edilen): idempotent, eksikse kurar, varsa atlar, kullanıcı ayarlarını ezmez.
2. **CHANGELOG'daki "Ana makinede yapılacaklar"a** birebir, kopyala-yapıştır komut olarak; yalnızca
   bir kez gereken ya da otomatikleştirilemeyen adımlar için (ör. oturumu kapatıp açmak).

"VM'de çalışıyor" bir kanıt değildir. VM'de zaten kurulu olan hiçbir şeyi ana makinede de var sayma.

## Projeye kurulum (her projede bir kez)

Önce projenin mevcut adlarını ve alışkanlıklarını bul (kur betiği `kur.sh`/`setup.sh`/`install.sh`/
`Makefile`, test betiği, CHANGELOG, belgelerin dili); varsa onları kullan, yeniden adlandırma.
Eksik olanları ekle:

1. **Kur betiği** yoksa `sablonlar/kur.sh`'den başlat. Kodun ya da testlerin çağırdığı her dış komutun
   paketi betiğin paket listesinde olmalı. Dil bağımlılıkları bir kilit dosyasıyla sabitlenir
   (Python: venv + `requirements.lock`, Node: `package-lock.json`); kilit VM'de üretilip commit'lenir.
2. **Test betiği:** tek komut, sonunda net bir "geçti/geçmedi" satırı. Ana makinede de çalışır.
3. **CHANGELOG** ve her sürümde "Ana makinede yapılacaklar" bölümü.
4. **`.ortam/`**: bu becerinin `ortam.sh`'sini kopyala (`cp <beceri>/ortam.sh .ortam/`), yanına
   `sablonlar/yoksay.txt`'i koy; projenin dış komutlarını `.ortam/komutlar.txt`'e yaz (satır başına bir).
5. **Çalışma düzeni belgesi** yoksa `sablonlar/CALISMA_DUZENI.md`'den üret: yer tutucuları doldur,
   projeye özgü adımları (donanım doğrulaması, ilk veri) ekle.
6. **CLAUDE.md**'ye aşağıdaki "CLAUDE.md bölümü"nü ekle.
7. **`.claude/settings.json`**: `git push` ve `git tag` için `permissions.ask`.
8. **`.gitignore`**: makineye özel ayarlar, `*.local.*`, üretilen çıktılar.

VM'de taban kaydı yoksa (`~/.local/share/ortam/taban.txt`) kullanıcıya söyle: taban, VM'in proje
işlerinden önceki hâlidir; şimdi alınırsa o ana kadar elle kurulanlar görünmez, bunları kur betiğine
bakarak elle gözden geçir.

## Bir şey kurmadan ya da sistemi değiştirmeden önce

- Önce kur betiğine yaz, sonra kur betiğini çalıştırarak kur. Elle denediysen ve kalacaksa betiğe işle
  ve betiği yeniden çalıştırarak doğrula.
- Sistem genelinde değil kullanıcı/proje düzeyinde kur (venv, `~/.local`); `pip install --user` ve
  sistem Python'una paket kurma.
- Mutlak yol, kullanıcı adı, cihaz adı, makineye özel değer koda girmez; ayar dosyasına girer, kur
  betiği varsayılanla oluşturur, var olan değeri ezmez.
- Donanıma bağlı kod (GPU, NPU, ses, kamera) VM'de yoksa zarifçe yedeğe düşmeli ve CHANGELOG'da
  "ana makinede doğrula" diye işaretlenmeli.
- Çekirdek, sürücü, ses sunucusu, güvenlik yazılımı gibi sistem düzeyi değişiklikleri önermeden önce
  kullanıcıya sor; ana makinede bunlar kurumsal kurallara takılabilir.

## Push'tan ya da sürümden önce

```bash
.ortam/ortam.sh kaydet      # VM'e tabandan sonra eklenenleri .ortam/vm.txt'ye yazar
.ortam/ortam.sh denetle     # projede hiç geçmeyen öğeleri listeler
```

Her `İŞLENMEMİŞ` satırı için karar ver: kur betiğine işle, CHANGELOG'a ana makine adımı olarak yaz ya
da ana makinede gerekmiyorsa (VM'e özgü araçlar, ör. `claude`, misafir eklentileri) gerekçesiyle
`.ortam/yoksay.txt`'e ekle. Sonra:

- Kur betiği yeniden çalıştı, idempotent (ikinci çalıştırmada bir şey değişmiyor) ve test betiği geçiyor.
- Kilit dosyaları güncel ve commit'li; `.ortam/vm.txt` commit'li.
- CHANGELOG'daki "Ana makinede yapılacaklar" tam: kopyala-yapıştır komutlar, tahmini süre ve disk,
  ana makinede doğrulanacaklar ve kullanıcının sana geri getireceği çıktı.
- Push ve etiket kullanıcı onayıyla.

## Ana makineden geri bildirim geldiğinde

Kullanıcıdan şu çıktıyı iste (kopyala-yapıştır):

```bash
cd <repo> && git log -1 --oneline && .ortam/ortam.sh kontrol
```

`kontrol` yalnızca eksik ya da farklı olanları yazar; ana makinenin paket listesini açığa çıkarmaz.
Hatayı sınıflandır ve kalıcı olarak düzelt; tek seferlik elle çözüm önerme:

| Belirti | Kalıcı çözüm |
|---|---|
| `EKSIK apt/snap/pip/bin/komut …`, `command not found`, `No module named` | Kur betiğine ekle. |
| `FARKLI python3`, sürüm uyumsuzluğu | Kilit dosyası, venv ya da betikte sürüm denetimi. |
| `EKSIK grup render/video/audio`, izin hatası | Kur betiği `sudo usermod -aG …` yapar; CHANGELOG'a "oturumu kapatıp aç". |
| Yol, kullanıcı adı, dosya bulunamadı | Ayar dosyasına taşı; kur betiği varsayılanı üretir. |
| Donanım (GPU/NPU/mikrofon) çalışmıyor | Yedek yol + ana makinede tek komutluk doğrulama adımı. |
| Kısayol, pencere, bildirim çalışmıyor | Masaüstü oturumu gerekir (SSH değil); belgeye yaz. |
| Ağ, proxy, sertifika hataları | Kurulumu indirmeye bağlı adımlardan ayır; kullanıcıya sor. |
| `git pull` reddediliyor | Ana makinede repo dosyası değişmiş ya da kilit dosyası orada üretilmiş; belgeye bak. |

Düzeltmeden sonra kullanıcıya ana makinede çalıştıracağı komutu ve beklenen son satırı söyle.

## Yalnızca ana makinede yapılabilenler

GPU/NPU ölçümü, gerçek mikrofon ya da donanım, gerçek veriyle deneme: kullanıcıya tek bir
kopyala-yapıştır komut ver ve geri getireceği çıktıyı tam olarak tanımla (ör. "son satır",
"`(OpenVINO / GPU)` satırı var mı"). Şirket verisi içerebilecek çıktı (doküman metni, ekran görüntüsü,
müşteri bilgisi, özel terim listesi) isteme. Ana makineye özel ölçüm sonuçları gerekiyorsa uydurma
veriyle üretilecek biçimde tasarla.

## Veri ve gizlilik

- VM'e ve repoya gerçek şirket verisi girmez. Repo public olabilir; kullanıcıya bunu hatırlat.
- Ana makinede kullanıcı yalnızca açıkça belirtilen dosyaları commit'ler (`git add <yol>`); ona asla
  `git add .` / `git add -A` önerme.
- Ana makineye şifresiz sudo önerme; VM'de kur betiği için yalnızca paket yöneticisine şifresiz sudo
  kabul edilebilir.

## Sık görülen fark kaynakları (Ubuntu)

- VM takılıyor ya da donuyor: çoğunlukla ekran hızlandırması yoktur (VM'de *Hakkında → Grafik*: `llvmpipe`).
  QEMU'da `virtio-vga` yerine `-device virtio-vga-gl -display gtk,gl=on` (virgl); sonra bellek.
  Kullanıcı VM'i terk etmeyi düşünmeden önce bunu öner; VM, ana makinedeki veriyi en iyi yalıtan düzen.
- `~/.local/bin` PATH'te değil: Ubuntu onu yalnızca oturum açılışında, klasör varsa ekler.
- `pip --user` ile sistem Python'una kurulmuş eski paketler; venv kullan, onlara dokunma.
- apt ile snap sürümleri farklı; hangisinin kullanılacağını kur betiği belirler.
- Wayland / X11 farkı: ekran görüntüsü ve kısayol araçları farklı davranır.
- Intel GPU için kullanıcının `render` grubunda olması ve sürücü paketleri gerekir; VM'de ölçülemez.
- Kurumsal güvenlik ajanı, proxy ya da özel sertifikalar indirmeleri ve bazı sistem çağrılarını
  etkileyebilir.
- Ana makinede eski bir kurulumun kalıntıları olabilir (aynı adda komut, eski ayar dosyası): kur
  betiği bunları yedekleyip üzerine yazmalı, silmemeli.

## CLAUDE.md bölümü

Projenin CLAUDE.md'sine eklenecek metin (projeye göre uyarla):

```markdown
## İki ortam

Bu proje VM'de geliştirilir, git üzerinden ana makinede çalıştırılır; ana makinede Claude Code yoktur
ve kurulumu eksik olabilir. `vm-ana-makine` becerisini izle. Özet: VM'de yapılan her kurulum/ayar kur
betiğine ya da CHANGELOG'daki "Ana makinede yapılacaklar"a girer; push'tan önce
`.ortam/ortam.sh kaydet && .ortam/ortam.sh denetle`; ana makinede güncelleme
`git pull && <kur> && <test>`; ana makineden gelen geri bildirim `.ortam/ortam.sh kontrol` çıktısıdır.
Ayrıntılar: CALISMA_DUZENI.md.
```

## Dosyalar

- `ortam.sh`: fark ölçer (`taban`, `kaydet`, `denetle`, `kontrol`, `liste`). Projeye `.ortam/`
  altına kopyalanır; başındaki `sürüm:` satırı değişirse proje kopyasını güncelle.
- `sablonlar/kur.sh`: idempotent kur betiği iskeleti.
- `sablonlar/CALISMA_DUZENI.md`: iki makinenin ilk kurulumu ve günlük akış, yer tutuculu.
- `sablonlar/yoksay.txt`: VM'e özgü öğelerin varsayılan listesi.
- `ana-makine/vm-kisayol.sh`: ana makinede VM'i açan kısayolu Sık Kullanılanlar'a ekler ve VM'i açar
  (VirtualBox, libvirt/virt-manager, GNOME Boxes, VMware'i kendisi bulur). Kullanıcı VM'i nasıl
  açacağını sorarsa bunu ver.
