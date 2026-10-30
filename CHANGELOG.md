# Değişiklikler

Her sürümde: ne değişti, ölçüm sonucu (varsa) ve **Ana makinede yapılacaklar**.

## v0.9.9 — kopyada API adları (2026-10-30)

- **Anlatımı kopyala** her adımda `Çağrılan API: <yön> · <metot> · <uç nokta> · <durum>` satırlarını da verir; gövde ve sorgu dizesi girmez. Rovo yanıtındaki bu satırlar anlatıma yazılmaz.
- **Kılavuz agent'ı** adımın altında API tablosunu, komut tablosundan önce yazar.

**Ana makinede yapılacaklar:** dock'taki **adımadım güncelle**; `rovo/ajan-talimati.md` ve `rovo/kilavuz-ajani.md` Talimat bölümlerini ilgili agent'lara yeniden yapıştır.

## v0.9.8 — kopyada gruplar ve komutlar, 5'li görsel kopyalama (2026-10-30)

- **Anlatımı kopyala** artık iş akışı başlıklarını, her adımın `Çalışan komut:` satırlarını ve arka plan bölümünü de verir; API gövdeleri girmez. Rovo yanıtındaki bu satırlar ve başlıklar anlatıma yazılmaz.
- **Kılavuz agent'ı** iç kullanım dokümanı üretir: adımlar durum başlıkları altında, komutlar adım altında tablo olarak. Müşteri dokümanı ayrı hazırlanacak.
- Bitiş ekranında **Görselleri kopyala (5'li)**: her basışta sıradaki 5 görsel ve adları panoya gelir, hangi beşlide olduğun yazar. Pano hem HTML hem dosya biçiminde doldurulur.

**Ana makinede doğrula:** Confluence panodaki görselleri kabul ediyor mu, adlar görselin altında mı? VM'de yalnız panonun doğru dolduğu sınandı.

**Ana makinede yapılacaklar:** dock'taki **adımadım güncelle**; `rovo/ajan-talimati.md` ve `rovo/kilavuz-ajani.md` Talimat bölümlerini ilgili Rovo agent'larına yeniden yapıştır.

## v0.9.7 — kopyada görsel adı (2026-10-30)

- **Anlatımı kopyala**, her `### Adım N` altına `Görsel: <dosya adı>` yazar; Rovo gövdeyi hangi görsele yazdığını adından bilir.
- Rovo yanıtındaki `Görsel:` satırları anlatıma yazılmaz; yalnız bu satırı olan adım değişmez. Görsel bağlantıları .md'de aynen kalır.
- `rovo/kilavuz-ajani.md`: kopyadan görsel adlarına bağlı kullanıcı kılavuzu yazan yeni Rovo agent'ının kurulumu ve talimatı.

**Ana makinede yapılacaklar:** dock'taki **adımadım güncelle**; `rovo/ajan-talimati.md` Talimat bölümünü Rovo ajanına yeniden yapıştır.

## v0.9.6 — workflow state gruplama ve arka plan komutları (2026-10-30)

Bu sürüm v0.9.4 ve v0.9.5'i de içerir: v0.9.3'ten sonra ana makineye giden ilk paket.

- **State grupları:** API'li dokümanda adımlar iş akışı durumuna göre `## Durum: <kod>` altında gruplanır; durum
  değiştiğinde başlık `(önceki → yeni)` der. Durum başlamadan önceki adımlar `## Başlamadan önce` altındadır.
  Adım sırası kronolojidir; aynı duruma dönüş ayrı grup olur. Durum okunamazsa düz liste (`## Ana akış`), uydurma yok.
- **Sabit geçişler:** `initialize` ve `submit` çağrıları iş akışı alanı taşımadığı için `ayar.json`'daki
  `sabit_gecisler` ile bilinir. Bu çağrıların komutları görünür: mevcut durumun post, sonraki durumun pre komutları.
  Geçiş kayda yazılmaz; eski dokümanlar HAR'sız da doğru çalışır.
- **Komutların görünmesi:** durum değişmeyen çağrıda mevcut durumun during komutları; durum değişince mevcut durumun
  post'u, sonra sonraki durumun pre'si. Her grup kendi içinde `sort_id` sırasıyla. CSV sırası akış sırasıdır.
- **`orderSubmit` sınırı (`son_ekran_durumu`):** bu durumdan sonra süren durumlar arka uçta çalışır ve HAR'da görünmez.
  Sınırdan sonraki çekimler son ekran durumu grubunda kalır; arka uç için ekran başlığı açılmaz. Dokümanın sonunda
  **Arka planda çalışan durumlar** bölümü: komut tablosunda sınırdan sonra gelen durumlar, her biri pre, during,
  post sırasıyla. Sınır boşsa ya da tabloda yoksa bölüm yok.
- **Çekimde imleç:** `gnome-screenshot -p` ile fare imleci ekran görüntüsünde görünür. Yedek araçlar değişmedi.
- **Karar noktası kalıbı:** Rovo talimatında anlatımdaki "Karar noktası: …" ifadesi
  `> **Karar noktası:** <koşul> → <sonuç>` bloğu olur; her dal ayrı `>` satırıdır. Söylenmemiş koşul uydurulmaz.
- **Çalışma kuralı:** **fareyi getir → çek → anlat → bas**.
- **Ölçüm** (gerçek 41 adımlı dokümanın kopyasında, içerik okunmadan): tüm .md ~2 MB iken anlatım kopyası ~4 KB;
  başlangıç + 8 durum grubu ve arka plan bölümü; LibreOffice 31 sn'de açtı, ~2300 sayfa. Word'ün kendisinde denenmedi.
- **Test:** `duman_testi.py`'ye iş akışı grupları kontrolü (sabit geçiş, sınır, arka plan, Anlatımı kopyala başlıksız).
  Eski "## Ana akış" varsayan assert, grup başlıkları gelince IndexError veriyordu; yalnız `### Adım 1`'den sonrasına bakacak
  biçimde düzeltildi.

**Ana makinede yapılacaklar:**
- Dock'taki **adımadım güncelle** düğmesi.
- Rovo agent'ı: `rovo/ajan-talimati.md`nin **Talimat** bölümünü agent'ın Instructions alanına bir kez yeniden yapıştır.
- Var olan dokümanı başla ekranından aç, **Komut tablosu** ile doğru komut tablosunu yeniden yükle. Doküman yeniden
  üretilir ve gruplar gelir.
- Doğrula: bir çekim yap, `gnome-screenshot -p` imleci gösteriyor mu.
- Doğrula: `grep -E "son_ekran_durumu|sabit_gecisler" ~/.config/adimadim/ayar.json` iki anahtarı da göstermeli.

## v0.9.5 — dokümana dönüş ve yalnız anlatımla Rovo (2026-10-30)

Bu sürüm v0.9.4 ile birlikte gönderildi (aynı push).

- **Sorun:** Rovo'ya tüm .md gidiyordu. 1 MB'ı aşan dokümanlar verilemiyordu; Rovo'nun yanıtı API bölümlerini
  ezebiliyordu. Rovo'dan dönen metin HAR ya da komut tablosu eklenince kayboluyordu; önceki hâli yalnız `.md.yedek`'te kalıyordu.
- **Çözüm:**
  - Bitiş ekranında "MD'yi kopyala" yerine **Anlatımı kopyala**: yalnız üst alanlar ve `### Adım N` + anlatım gider.
  - Rovo alanına yapıştırılan yanıt yalnız eşleşen adımların anlatımını değiştirir. Görseller ve API bölümleri
    aynen kalır. Yanıtta `Adım N` başlığı yoksa .md değişmez, alan silinmez, uyarı çıkar.
  - Rovo metni oturumda (`adim["metin"]`) tutulur: API ekle, komut tablosu ve .md'nin yeniden üretimi onu silmez.
    Elle yapılan düzeltmeler de aynı yerde kalır.
  - "Sesi baştan çevir" elle ve Rovo düzeltmelerini siler: metin sesten yeniden yazılır, önceki .md `.md.yedek`'te kalır.
  - Rovo talimatı (`rovo/ajan-talimati.md`) yeni akışa göre yazıldı: girdi yalnız anlatım, çıktı aynı biçimde tek
    ```markdown bloğunda. Anlatımdaki "Amaç:", "Aktör:", "Ön koşul:", "Son koşul:" üst alana taşınır.
- **Başla ekranı:** son dokümanlar listesi (başlık, adım sayısı, tarih). Çift tıkla ya da **Aç** ile dokümana dönülür.
  **Başka klasör…** ile elle seçilen klasör açılır; oturum.json'u yoksa ya da bozuksa uyarı çıkar.
- **Ölçüm:** yok. Konuşma tanıma ve ses kaydı değişmedi.
- Test: `duman_testi.py` arayüz kontrolü yeni davranışa çevrildi: kopya `anlatim_kopyasi` ile eşit, görsel ve API
  yok; Rovo yanıtı .md'de; API ve komut tablosu sonrası da metin duruyor; listeden açma. `xvfb-run -a` altında geçti.
  Kapılar: `kapi/rovo.py` (ayikla, uygula, senkron), `kapi/arayuz_rovo.py`, `kapi/arayuz_ac.py`.

**Ana makinede yapılacaklar:**
- Dock'taki **adımadım güncelle** düğmesi.
- Rovo agent'ı: `rovo/ajan-talimati.md`nin **Talimat** bölümünü agent'ın Instructions alanına bir kez yapıştır.
  Agent yoksa Kurulum bölümündeki gibi oluştur (ad, terim sözlüğü Knowledge, talimat).
- v0.9.5 öncesi bir dokümanın Word'ü için: pencereden dokümanı aç, **Word'ü yenile** (`adimadim word "<doküman klasörü>"` de olur).
- Ana makinede doğrula, gerçek bir dokümanda gidiş-dönüş: uygulamayı kapat, aç, dokümana listeden dön,
  **Anlatımı kopyala**, Rovo'ya yapıştır, çıktıyı Rovo alanına yapıştır. Görseller ve API bölümleri birebir kalmalı,
  anlatım değişmeli, Word açılmalı. Sonra bir HAR ekleyip komut tablosu yükle; Rovo metni kaybolmamalı.

## v0.9.4 — büyük API gövdeli Word dosyaları açılıyor (2026-10-30)

- **Sorun:** API gövdeli dokümanlarda pandoc her kod bloğunu tek paragraf yapıyordu. Gerçek bir dosyada tek
  paragrafta 1,17 milyon karakter ve 29 bin satır sonu oluştu; LibreOffice 7.3 dosyayı 400 sn'de açamadı.
  Renksiz (`--no-highlight`) tek paragraf da açılmadı.
- **Çözüm:** `kod_satirlari.lua` filtresi her kod satırını ayrı kod paragrafı yapar; `word` komutu
  filtreyi pandoc'a verir. Gövdeler kısaltılmaz (v0.9.2 kararı).
- **Ölçüm:** aynı dosya LibreOffice'te 400 sn'de açılmadı → 11 sn'de açıldı (pandoc 2.9.2.1). Yaklaşık 1300 sayfa, kısaltma yok.
  Word'ün kendisinde denenmedi.
- Test: `duman_testi.py` uydurma bir `~~~json` bloğundan üretilen docx'te kod satırlarının ayrı `SourceCode`
  paragrafları olduğunu, boş satırın kaybolmadığını, sıranın korunduğunu ve `<w:br>` bulunmadığını kontrol eder.

**Ana makinede yapılacaklar:**
- Dock'taki **adımadım güncelle** düğmesi.
- Var olan doküman için: `adimadim word "<doküman klasörü>"`.

## v0.9.3 — mikrofon seçimi (2026-10-30)

- **Kaynak seçimi:** `mikrofon` ayarı (ör. `bluez_input`) doluysa ses `parecord --device=<kaynak>` ile alınır.
  Varsayılan giriş artık kullanılmaz: ana makinede varsayılan giriş kulaklığın monitörüydü, arecord
  kulaklıkta çalan sesi kaydediyordu. Monitör kaynakları asla seçilmez.
- **Kulaklık profili:** `mikrofon_profil` (ör. `headset-head-unit-msbc`) doluysa sesli oturum başladığında
  kulaklık bu profile geçer; `bitir`de eski profile (`a2dp-sink`) döner. Oturum sırasında Bluetooth
  düşüp A2DP'ye dönerse her adımda yeniden mikrofon profiline geçilir. Oturum kaydı (`oturum.json`)
  eski profili tutar. Sistem varsayılan girişine dokunulmaz; sesli oturum dışında Teams etkilenmez, oturum sırasında kulaklık görüşme profilindedir.
- Kaynak ya da profil hazırlanamazsa `basla` oturum açmadan çıkar; oturum sırasında kaynak kaybolursa
  adım uyarıyla kaydedilir, sesi alınmaz.
- İki ayar da boşken davranış aynıdır: pactl çağrılmaz, arecord kullanılır.
- Test: `duman_testi.py` sahte `pactl` ve `parecord` ile 9 yeni kontrol (profil geçişi ve geri alma,
  monitör seçilmemesi, eski profilin ezilmemesi, kaynak ve kart yokken hata, Bluetooth düşmesi).

**Ölçüm** (ana makinede kayıt; tek 12 kelimelik cümle, whisper-medium; örneklem küçük):

| Kaynak | Hata (12 kelime) | Konuşma-gürültü farkı |
|---|---|---|
| Digital Microphone (dahili) | 3 | ~21 dB |
| FreeBuds mikrofonu, mSBC (görüşme profili) | 2 | ~51 dB |
| FreeBuds mikrofonu, CVSD | 1 | ~42 dB |
| FreeBuds mikrofonu, A2DP (müzik profili) | — | tamamen sıfır veri |

Kayıt sırasında kulaklığın ses kalitesi düşer (müzik profili yerine görüşme profili aktif). Bu oturum
boyunca geçerlidir ve bitince geri gelir.

**Ana makinede doğrula:** kayıt sırasında `pactl list cards | grep "Active Profile"` çıktısı
`headset-head-unit-msbc` olmalı; bitirince `a2dp-sink`'e dönmeli.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

Beklenen son satır: `SONUÇ: testler geçti`. Ardından ayarları bir kez yaz (diğer anahtarlar korunur):

    python3 - <<'EOF'
    import json, os
    p = os.path.expanduser("~/.config/adimadim/ayar.json")
    a = json.load(open(p, encoding="utf-8"))
    a.update({"mikrofon": "bluez_input", "mikrofon_profil": "headset-head-unit-msbc"})
    json.dump(a, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("tamam:", a["mikrofon"], a["mikrofon_profil"])
    EOF

Beklenen: `tamam: bluez_input headset-head-unit-msbc`. Sonra kulaklığı bağlayıp kısa bir sesli oturum
dene; geri getirmesi gereken: `Adım 1 — anlat` satırı ya da `Mikrofon bulunamadı` uyarısı, ve bitirdikten
sonra kulaklığın Ses ayarlarında eski profile dönüp dönmediği (evet/hayır).

## v0.9.2 — API gövdeleri kısaltılmadan (2026-10-07)

- İstek/yanıt gövdeleri dokümana tam yazılır: `… (+N satır)`, `… +N öğe` ve uzun metin kısaltmaları
  kaldırıldı (ana makinedeki ilk denemeden gelen istek). Gizleme aynen sürer (`api_gizle`, başlıklar yok).
- Gövdeler `api` çalışırken oturum.json'a yazıldığı için **önceden eklenmiş dokümanlarda** kısaltma ancak
  HAR yeniden eklenince kalkar; komut tablosu korunur, yeniden yüklemek gerekmez.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

Beklenen son satır: `SONUÇ: testler geçti`. Kısaltılmış bir doküman için HAR'ı yeniden ekle
(Bitiş ekranında **API ekle (HAR)** ya da `adimadim api <dosya.har> "<doküman klasörü>"`).

## v0.9.1 — tek tıkla güncelleme düğmesi (2026-10-07)

- Ana makinede dock'ta **adımadım güncelle** düğmesi: GitHub'dan son hâli çeker, kod son başarılı
  kurulumdan beri değiştiyse `./kur.sh` çalıştırır (adımadım açıksa kapatılmasını bekler), sonra
  pencereyi açar. Hata olursa terminal açık kalır. Genel araç: `beceriler/vm-ana-makine/ana-makine/guncelle.sh`,
  projenin ayarı `.ortam/guncelle`; başka projeler (ör. DBeaver-mm) aynı betikle kendi düğmesini alır.
- `test.sh` 1. adımı düğmeyi sahte bir GitHub reposuyla dener (`guncelle-test.sh`).

**Ana makinede yapılacaklar** (bir kez; sonra yalnızca düğme):

    cd ~/adimadim && git pull && ./kur.sh

Beklenen: `Düğme hazır: dock'ta ve Uygulamalar'da "adımadım güncelle".`

## v0.9.0 — iş akışında çalışan komutlar (2026-10-07)

- **Komut tablosu:** durumlarda çalışan komutların veritabanı kaydı (akış, durum, …, bean_name, is_pre,
  is_post, sort_id) bitmiş dokümana yüklenir: Bitiş ekranında **Komut tablosu** (DBeaver'da sonuç
  tablosunda Ctrl+A, Ctrl+C; pano boşsa CSV/TXT/Markdown dosyası seçilir) ya da
  `adimadim komutlar tablo.csv [klasör]`. Tablo oturum.json'da saklanır; HAR sonradan yeniden eklense de
  kalır. Birden çok akış içeren tablo reddedilir.
- **İş akışı çağrısı:** isteğinde `currentWorkFlowStateShortCode` olan çağrı (yanıtında
  `nextWorkFlowStateShortCode`) adımın altında `#### Çalışan komutlar` tablosuyla gösterilir:
  `workFlowStateChange` true ise mevcut durumun is_post=1 komutları, sonra sonraki durumun is_pre=1
  komutları (sonraki duruma girerken); false ise mevcut durumun during komutları (pre/post olmayan:
  durum atlamadan yapılan işlemler, asenkron durumlar dahil); her grup sort_id sırasıyla.
  Tabloda olmayan durum için "kayıt yok" yazar.
- Aynı uca aynı ekranda farklı gövdeyle giden çağrılar artık ayrı satır (önceden tek satıra iniyordu).
- Rovo talimatı: `#### Çalışan komutlar` bölümü de olduğu gibi korunur.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

Beklenen son satır: `SONUÇ: testler geçti`. Rovo agent'ının talimatını `rovo/ajan-talimati.md`'deki
"Talimat" bölümüyle yenile.

**Ana makinede doğrula** (şirket verisi gönderme): bir akışı HAR ile ekledikten sonra komut tablosunu
yükle. Geri getir: son satır (ör. `Komut tablosu yüklendi: 64 komut, 5 iş akışı çağrısı.`) ve komutların
beklediğin adımlarda ve sırada olup olmadığı (evet/hayır).

## v0.8.0 — adım adım API çağrıları (2026-10-06)

- **API ekle (HAR):** tarayıcının Ağ sekmesinden kaydedilen HAR dosyası bitmiş dokümana eklenir (Bitiş
  ekranında düğme ya da `adimadim api dosya.har [klasör]`). Çağrılar çekim zamanlarına göre adımlara
  dağıtılır: iki çekim arasındaki GET → verinin göründüğü sonraki ekran ("Ekrana gelen"), POST/PUT/PATCH/
  DELETE → butona basılan ekran ("Butonla giden"). Başla öncesi ve Bitir sonrası çağrılar atılır.
- Her adımın altında `#### API çağrıları` tablosu ve kısaltılmış istek/yanıt gövdeleri (`~~~json`;
  Rovo'nun ```markdown bloğunu bozmasın diye `~~~`). Yalnızca JSON/XML çağrılar; css, görsel ve analitik
  atılır. Aynı ekranda tekrarlanan çağrı tek satır.
- **Gizlilik:** istek/yanıt başlıkları (Authorization, Cookie…) dokümana hiç yazılmaz; `api_gizle`
  ayarındaki alanlar gövdede ve sorguda `***` olur. Ham HAR oturum klasörüne kopyalanmaz.
- Yeni ayarlar: `api_filtre` (`[]`), `api_gizle` (`["password", "parola", "sifre", "token", "secret"]`);
  kur.sh eksik anahtar olarak ekler, mevcut değerlere dokunmaz.
- Adımlar artık çekim zamanını, oturum başla/bitir zamanını tutar. v0.8.0'dan önceki dokümanlara API
  eklenemez (açık mesaj verir).
- Rovo talimatı: API bölümleri olduğu gibi korunur (`rovo/ajan-talimati.md`).
- Yeni bağımlılık yok.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

Beklenen son satır: `SONUÇ: testler geçti`. Rovo'daki agent'ın talimatını `rovo/ajan-talimati.md`'deki
"Talimat" bölümüyle yenile (API bölümünü koruma kuralı eklendi).

**Ana makinede doğrula** (şirket verisi gönderme, yalnızca sonucu söyle):
1. Firefox'ta uygulamayı açmadan önce F12 → Ağ → dişli → **Kayıtları sürdür**.
2. adımadım'da kısa bir akış kaydet (2-3 ekran, en az bir butonla kayıt), Bitir.
3. Ağ sekmesinde sağ tık → **Tümünü HAR olarak kaydet**; Bitiş ekranında **API ekle (HAR)** ile seç.
4. Geri getir: son satır (ör. `5 API çağrısı adımlara eklendi.`) ve "çağrılar doğru adımlarda mı, gereksiz
   çağrı var mı" (evet/hayır + gereksizlerin yalnızca URL kalıbı, ör. `/monitoring/`). Sonra HAR'ı sil.

## v0.7.0 — bölge çekme, işaretleme, Rovo alanı (2026-09-28)

Ana makinedeki denemeden gelen istekler:
- **Bölge çek:** kayıt ekranındaki düğme tüm ekranı çeker, sonra kırpma/işaretleme penceresi açılır.
  **Kırp** (alan seç), **Kutu**, **Ok**, **Yazı** (kırmızı, beyaz kenarlı), Geri al (Ctrl+Z), Kaydet (Enter).
  Önizlemedeki herhangi bir görsele tıklayınca da aynı pencere açılır (Ctrl+Alt+S ile çekilenler dahil).
  İlk düzenlemede orijinal görsel `gorseller/.orijinal/` altında saklanır. Flameshot yerine kendi
  düzenleyicimiz: GNOME Wayland'de flameshot her çekimde izin sorar.
- **Bitiş ekranı:** "MD'yi kopyala" düğmesi (panoya) ve Rovo alanı: Rovo'nun çıktısı yapıştırılınca
  (Ctrl+V) .md güncellenir (öncekisi `.md.yedek`), kod bloğu işaretleri atılır, Word kendiliğinden yenilenir.
- Önizlemede madde işaretleri; test sırasında pencere artık görünmez.
- `adimadim cek --tam`: ayardan bağımsız tüm ekranı çeker.
- kur.sh: `fonts-dejavu-core` (görsele yazılan yazı). requirements.txt: `pillow` (lock'ta zaten vardı).

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

Beklenen son satır: `SONUÇ: testler geçti`. **Ana makinede doğrula:** "Bölge çek" tüm ekranı çekip
düzenleyiciyi açıyor; Rovo çıktısı yapıştırınca önizleme ve Word güncelleniyor.

## v0.6.0 — pencere yeniden tasarlandı, Faz 2 (2026-09-28)

Ana makinedeki ilk denemeden gelen geri bildirimle:
- **Bekleme göstergesi:** bir işlem sürerken hareketli çubuk, ne beklendiği, geçen süre ve komutun son
  satırı görünür (ör. "Lütfen bekle: Doküman hazırlanıyor… (42 sn)").
- **Düzeltme:** komut çıktısı boruya yazılıyordu; Bitir uzun çıktı üretince tampon dolup takılabiliyordu.
  Artık `~/.config/adimadim/arayuz.log`'a yazılır (sorun olursa son satırı buradadır).
- **Başla ekranı:** "Yeni dokümanın adı", sesli/yazılı seçimi ve tek Başla düğmesi (Enter da başlatır).
- **Kayıt ekranı:** "Adım N" ve kırmızı "● KAYIT" göstergesi; çekilen ekranların küçük önizlemeleri
  adım adım yan yana. Düğmelerin altında ne yaptıkları yazar (Son adıma not yaz, Son adımı sil…).
- **Bitiş ekranı:** Bitir'den sonra dokümanın görselli önizlemesi; Word'ü aç, Klasörü aç, Word'ü yenile,
  Sesi baştan çevir, Yeni doküman. Pencereden bitirince dosya yöneticisi ayrıca açılmaz.
- Görünmeyen emoji simgeleri kaldırıldı. Komut satırı aynen çalışır.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./test.sh

Yeni paket yok. Pencereyi uygulama menüsünden (ya da `adimadim arayuz`) aç ve kısa bir sesli akış dene.
**Ana makinede doğrula:** Bitir'e basınca bekleme çubuğu görünüyor ve bitince önizleme açılıyor;
"Ekranı çek" düğmesi arayüzü değil önceki pencereyi çekiyor.

## v0.5.0 — düğmeli pencere, Faz 1 (2026-09-28)

- `arayuz.py`: hep üstte duran küçük pencere. Başla (sesli/yazılı), Ekranı çek, Not, Geri, Bitir,
  Word'ü yenile, Sesi yeniden çevir, Klasör düğmeleri; adım sayısı, kayıt göstergesi ve duruma göre ipucu.
  Düğmeler mevcut komutları ayrı süreçte çalıştırır; komut satırı aynen çalışır.
- kur.sh: `python3-tk` paketi ve uygulama menüsünde "adımadım" girdisi (terminal gerekmez).
- Anlık (adım bitince) çeviri ölçüldü ve alınmadı: gerçek oturumda WER %93 (tek tek) / %101 (önceki+bu)
  / **%7,6 (toplu, mevcut)**; adım başına 19-28 sn bekleme (VM CPU).

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

- kur.sh `python3-tk`'yı kurar (sudo şifresi sorar). Sonra uygulama menüsünden **adımadım**'ı aç
  (görünmezse oturumu kapatıp aç). Beklenen son satır: `SONUÇ: testler geçti`.
- **Ana makinede doğrula:** "📷 Ekranı çek" düğmesi arayüzü değil, önceki pencereyi çekiyor.
  Çekmiyorsa Ctrl+Alt+S kullan ve hangi pencerenin çekildiğini bildir.

## v0.4.1 — Rovo çıktısından Word (2026-09-28)

- `adimadim word`: Rovo'nun işlenmiş çıktısı kopyalanınca kaybolan görsel bağlantılarını ve `### Adım N`
  başlıklarını geri koyar, "Preview unavailable" satırlarını atar. Rovo talimatı: çıktı tek markdown kod bloğunda.

**Ana makinede yapılacaklar:** `cd ~/adimadim && git pull`; Rovo talimatının son kuralını güncelle.

## v0.4.0 — adımlar birlikte çevrilir (2026-09-28)

- **Sorun (gerçek kullanımda görüldü):** kullanıcı konuşurken Ctrl+Alt+S'ye basınca cümle iki dosyaya
  bölünüyor, her adım ayrı çevrilince sınırdaki kelimeler kayboluyor, kısa parçalarda model cümlenin
  devamını atlıyor ve ipucundaki "Şimdi bu ekranda…" cümlesi metne sızıyordu ("altyazı", "Sıstak").
- **Çözüm:** `bitir` ve `yeniden` adımların seslerini birleştirip tek seferde zaman damgalı çevirir;
  her cümle başladığı adıma yazılır. VAD'nin kestiği sessizlikler için zaman damgaları asıl sese geri
  taşınır. Motorlar artık `(başlangıç, bitiş, metin)` parçaları döndürür.
- **Ölçüm (gerçek oturum, 12 adım, 135 sn, `testler/gercek/`, VM CPU):** WER %93,0 → **%7,6**,
  terim 11/11, "bu ekran" sızıntısı 5 → 0. Paragrafları rastgele 14 adıma bölen benzetimde
  WER %75,7 → %17,1. Tek kayıtlık setler değişmedi (29 kayıt: 88/95, WER %15,3; paragraflar: %93,9, WER %15,8).
- Rovo talimatı: drawer kuralı yalnızca Interaction drawer için; koşullu ifadeler korunur.
- terimler.txt: Device Change, Summary, Order Summary vb. ekran terimleri (ipucu sınırına sığmıyor;
  ölçüm ve ileride ekran bazlı ipucu için).

**Ana makinede yapılacaklar:** `cd ~/adimadim && git pull && ./test.sh`. Önceki bir dokümanı yeni
yöntemle yeniden çevirmek için: `adimadim yeniden <doküman klasörü>` (eski .md `.yedek` olarak saklanır).
Rovo agent talimatını `rovo/ajan-talimati.md`'deki güncel metinle değiştir.

## v0.3.1 — göreli doküman klasörü düzeltmesi (2026-09-27)

- `klasor` ayarı göreli bir yolsa (ör. `...`) doküman terminalin bulunduğu dizine göre açılıyor,
  Ctrl+Alt+S ise GNOME'dan ev dizininde çalıştığı için "Açık doküman yok" diyordu. Göreli yol artık ev
  dizinine göre çözülür. Duman testine kontrol eklendi.

**Ana makinede yapılacaklar:** `cd ~/adimadim && git pull`; `~/.config/adimadim/ayar.json`'daki
`klasor` değerini `""` (Belgeler/adimadim) ya da mutlak bir yol yap.

## v0.3.0 — model kararı, doğruluk katmanları, Rovo (2026-09-27)

v0.2.0 ayrıca etiketlenmedi; model kararı (Faz 4) bu sürümde.

- **Model kararı (gerçek kayıtlar, 29 kayıt, VM CPU):** whisper-medium kalır; Türkçe adaylar İngilizce
  terimleri Türkçe okunuşla yazıyor.

  | Model | Terim isabeti | WER | Ortografik WER |
  |---|---|---|---|
  | whisper-medium | %66,3 | %29,0 | %41,0 |
  | Sercan/whisper-small-tr-2 | %28,4 | %46,8 | %64,3 |
  | Sercan/distil-whisper-large-v3-tr | %14,7 | %58,9 | %70,0 |

- **Doğruluk katmanları (whisper-medium, aynı 29 kayıt):**

  | Ayar | Terim isabeti | WER | Ortografik WER |
  |---|---|---|---|
  | hiçbiri | %67,4 | %29,0 | %41,0 |
  | düzeltme kuralları | %75,8 | %26,1 | %37,2 |
  | ipucu (yalnız terim listesi) + düzeltme | %90,5 | %47,0 | %63,7 — model liste üslubuna geçip kelime atlıyor |
  | **ipucu (doğal cümleyle biten) + düzeltme + VAD** | **%90,5** | **%16,4** | **%27,1** |

  FLEURS'ta (genel Türkçe) aynı ayar bozmuyor: WER %12,5 → %12,0. İpucu ve kurallar bu kayıtlardaki
  hatalara bakılarak seçildi; yeni kayıtlarda kazanç biraz daha düşük olabilir.
- Yeni ayarlar: `ipucu` (varsayılan `prompt`) ve `duzeltme` (varsayılan açık). kur.sh eksik anahtarları ekler.
  Yeni dosyalar: `duzeltmeler.txt` (genel kurallar), ana makinede `~/.config/adimadim/duzeltmeler.local.txt`.
- **VAD:** OpenVINO yolunda Silero VAD (faster-whisper ile gelir). Gürültü/klavye sesinde model
  "Altyazı M.K.", "tüm tüm tüm…" uyduruyordu; artık boş döner. test.sh gerçek modelle gürültü kontrolü yapar.
- Kayıt durdurulmadan önce 0,5 sn beklenir (son kelime kayboluyordu). **Ana makinede doğrula.**
- Rovo: `rovo/ajan-talimati.md` (agent talimatı), `rovo/confluence-sozluk.md` (sözlük sayfası).

- **Düzeltme:** Türkçe locale'de dönüştürülen OpenVINO modellerinde tokenizer XML'ine `precision="STRiNG"`
  yazılıyor, model yüklenemiyor ve araç sessizce faster-whisper `small`'a (CPU) düşüyordu. kur.sh artık
  `LC_ALL=C.UTF-8` ile dönüştürüyor ve mevcut bozuk modeli yeniden dönüştürmeden onarıyor.
- test.sh OpenVINO modelini yedeksiz yükler; yüklenemezse test başarısız olur.
- `testler/karsilastir.py`: modelleri aynı sette (WER, ortografik WER, RTF) karşılaştırır; `--fleurs 100`
  FLEURS tr test bölümünden sabit tohumla (42) 100 kayıt alır (CC BY 4.0; önbelleğe iner, repoya girmez).
- İlk ölçüm (FLEURS 100 kayıt, VM CPU), geçici; karar gerçek kayıtlarla verilecek:

  | Model | WER | Ortografik WER | RTF |
  |---|---|---|---|
  | whisper-medium (referans) | %12,5 | %19,1 | 0,59 |
  | Sercan/distil-whisper-large-v3-tr | %17,5 | %24,1 | 0,78 |
  | Sercan/whisper-small-tr-2 | %25,8 | %42,7 | 0,15 (küçük harf, noktalamasız yazıyor) |

  Adayların dönüştürülmesi elle yapıldı, kur.sh'ye işlenmedi (referans önde): distil 11 GB RAM'de doğrudan
  dönüştürülemiyor (OOM), önce fp16 kaydedilmeli; small-tr-2'nin tokenizer'ı eski, `openai/whisper-small`'dan
  alınmalı.

**Ana makinede yapılacaklar:**

    cd ~/adimadim && git pull && ./kur.sh && ./test.sh

- Model yeniden indirilmez. kur.sh `ipucu` ve `duzeltme` ayarlarını ekler, mevcut değerlere dokunmaz;
  Türkçe locale'de bozulmuş model varsa `Onarıldı: …` yazar.
- test.sh 29 kaydı GPU'da ölçer (~1-2 dk). Beklenen: `✓ OpenVINO modeli yüklendi: … GPU`,
  `✓ gürültüde metin uydurmuyor`, `terim isabeti` ~88/95.
- Şirkete özel düzeltmeler: `~/.config/adimadim/duzeltmeler.local.txt` ("yanlış → doğru").
- Rovo: agent talimatı `rovo/ajan-talimati.md`, Confluence sözlüğü `rovo/confluence-sozluk.md`.
- **Ana makinede doğrula:** gerçek bir akışta (`adimadim basla "…" --ses`) adımın son kelimesi kesilmiyor.

## v0.1.0 — iskelet

- Ekran görüntüsü + yazılı/sesli anlatımdan kullanım senaryosu (.md + .docx).
- Konuşma tanıma: OpenVINO (VM'de CPU, ana makinede GPU); çalışmazsa faster-whisper.
- Yeni komutlar: `cevir` (ses dosyasını metne çevirir), `yeniden` (bitmiş dokümanı baştan çevirir).
- kur.sh (tekrarlanabilir kurulum), test.sh (duman testi + doğruluk ölçümü).
- Belgeler: CLAUDE.md (kurallar), KARARLAR.md (arka plan ve kararlar), YOL_HARITASI.md (iş planı).
- Çalışma düzeni: CALISMA_DUZENI.md (VM ve ana makinenin ilk kurulumu, günlük akış, geri bildirim,
  sorun giderme); `.claude/settings.json` (VM'deki Claude Code push ve etiket için onay ister).
- `beceriler/vm-ana-makine`: her projede VM ile ana makine arasındaki kurulum farkını kapatan Claude Code
  becerisi (kurallar, şablonlar, `ortam.sh` fark ölçer). Bu projede `.ortam/` altında kullanılıyor.
- kur.sh aracın çağırdığı masaüstü yardımcılarını da kurar (xdg-utils, xdg-user-dirs, libglib2.0-bin);
  eksik kurulu bir makinede de çalışsın diye. .gitignore makineye özel dosyaları dışarıda tutar.

**Ana makinede yapılacaklar:** ilk kez repoyu klonla (CALISMA_DUZENI.md, 3. bölüm), sonra
`./kur.sh && ./test.sh`. Önce VM'de üretilen `requirements.lock`'un push'lanmış olmasını bekle.
Sonraki sürümlerde: `git pull && ./kur.sh && ./test.sh`
- Eski `~/.local/bin/adimadim` kopyası `adimadim.eski` olarak yedeklenir; artık repodaki araç çalışır.
- Mevcut `~/modeller/whisper-medium-ov` modeli kullanılır, yeniden dönüştürülmez.
- Python paketleri ayrı bir ortama kurulur (`~/.local/share/adimadim/venv`); `pip --user` ile
  daha önce kurulanlara dokunulmaz.
