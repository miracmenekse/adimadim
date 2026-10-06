# Yol haritası: Türkçe konuşma tanıma modeli seçimi ve doğruluk katmanları

Bu dosya Claude Code içindir. CLAUDE.md'deki kurallar her fazda geçerlidir.

## Çalışma biçimi

- Fazları sırayla uygula. Her fazın sonunda `./test.sh` geçer, küçük commit'ler atılır, CHANGELOG'a
  kısa not düşülür ve kullanıcıya 3-5 satırlık bir özet verilir.
- 🛑 işaretli noktalarda dur ve kullanıcıya sor. Bunların dışında kararı kendin ver, gerekçesini
  CHANGELOG'a yaz ve devam et.
- Ölçmeden karar yok: doğruluğu etkileyen her değişiklikten önce ve sonra ölç; sonuçlar
  `testler/sonuclar/` altında saklanır.
- Bir yolda takılırsan (sürüm uyumsuzluğu, eksik özellik) en fazla iki alternatif dene; olmazsa sorunu,
  denediklerini ve önerini kullanıcıya yaz.

## Amaç ve bitti tanımı

Kullanıcının serbest Türkçe anlatımını, özellikle telekom/BSS terimlerini, dokümana uygun biçimde
(noktalama, büyük harf) yazıya dökmek. İş şu durumda bitmiş sayılır:

1. Seçilen model ana makinede GPU'da çalışıyor ve gerçek kayıtlarda terim isabeti ile ortografik WER'de
   referans modelden (medium) iyi.
2. Doğruluk katmanlarının her birinin katkısı ölçülmüş; kazandıranlar varsayılan, diğerleri ayarla
   açılabilir durumda.
3. `./test.sh` hem VM'de hem ana makinede geçiyor; karşılaştırma tabloları ve CHANGELOG repoda.

## Modeller

| Rol | Hugging Face kimliği | Bilinenler (model kartı ve repo dosyalarından) |
|---|---|---|
| Referans | `openai/whisper-medium` | Şu an kullanılan model. Ana makinede `~/modeller/whisper-medium-ov` olarak fp16 dönüştürülmüş ve GPU'ya ayarlı; GPU'da çalıştığı henüz doğrulanmadı. |
| Aday 1 | `Sercan/distil-whisper-large-v3-tr` | whisper-large-v3'ten damıtılmış Türkçe model: kodlayıcı 32, çözücü 2 katman, 128 mel, ~756M parametre (F32 safetensors, ~3 GB). generation_config.json'da `<\|tr\|>` ve `transcribe` tanımlı. Lisans Apache-2.0. Kartta WER %14,4 (normalize) ve %21,6 (ortografik), Common Voice 17 tr; bağımsız doğrulanmamış. |
| Aday 2 | `Sercan/whisper-small-tr-2` | whisper-small'ın (medium'dan küçük) Türkçe ince ayarı. Kartta Common Voice 11 tr testte WER %16,6 (doğrulanmamış). Lisans Apache-2.0. Repoda generation_config.json ve tokenizer.json yok; ağırlıklar `pytorch_model.bin`; eğitim artıkları var (`runs/`, `.ipynb_checkpoints/`, `training_args.bin`; repo depolaması ~12,6 GB). |

Yalnızca bu iki aday denenir. İkisi de referansı geçemezse yeni bir aday önerisini
(ör. `openai/whisper-large-v3-turbo`) kullanıcıya sun; kendiliğinden ekleme.

## Ölçütler

- **Terim isabeti (birincil):** terimler.txt (+ varsa terimler.local.txt) içindeki terimlerden, beklenen
  metinde geçenlerin kaçı çıktıda doğru yazılmış.
- **WER (normalize)** ve **ortografik WER** (büyük/küçük harf ve noktalama dahil). Doküman kalitesini
  ortografik WER gösterir.
- **Hız:** RTF (işlem süresi / ses süresi) ve model yükleme süresi ayrı ayrı. VM'de CPU ölçülür;
  GPU hızı ana makinede ölçülür.
- **Halüsinasyon:** sessiz ve yalnızca gürültü içeren kliplerde çıktı boş olmalı. Türkçe Whisper'da
  bilinen bir örnek, sessizlikte "Altyazı M.K." gibi altyazı imzaları üretmesidir.
- **Uzun kayıt:** 30 saniyeden uzun anlatım kesilmeden ve tekrarsız yazılmalı.

## Başlarken

1. 🛑 Kullanıcıdan ana makinede, dokümanı hazırlarken kullanacağı mikrofonla 10-20 test kaydı iste
   (testler/README.md). Yanıt beklemeden devam et; kayıtlar gelince ölçümleri onlarla tekrarla.
2. 🛑 Kullanıcıya Windows desteğinin hedeflenip hedeflenmediğini sor (bkz. KARARLAR.md, Açık kararlar).
   Yanıt beklerken platformdan bağımsız işlere devam et. Yanıt evetse bundan sonraki her işte iki kural
   geçerli: platforma özel kod (ekran görüntüsü, kısayol, pencereler, ses kaydı, bildirim, dosya kilidi)
   ince bir katmanda toplanır; yeni bileşenler Windows'ta da kurulabilir olmalı, apt'e bağlı kalmamalı.
   Windows paketlemesi Faz 4'ten sonra ayrı bir faz olarak planlanır.
3. `./kur.sh && ./test.sh` ile başlangıç durumunu doğrula.

## Faz 0 — Ölçüm ve karşılaştırma altyapısı

1. **Model profilleri.** ayar.json birden çok modeli ve aktif profili tutar. Önerilen biçim:

   ```json
   "model": "medium",
   "modeller": {
     "medium":             {"kaynak": "openai/whisper-medium",             "klasor": "~/modeller/whisper-medium-ov"},
     "distil-large-v3-tr": {"kaynak": "Sercan/distil-whisper-large-v3-tr", "klasor": "~/modeller/distil-large-v3-tr-ov"},
     "small-tr-2":         {"kaynak": "Sercan/whisper-small-tr-2",         "klasor": "~/modeller/whisper-small-tr-2-ov"}
   }
   ```

   Geriye uyumluluk şart: `ov_kaynak` / `ov_model` içeren mevcut ayar.json'lar bozulmadan `medium`
   profiline taşınır. Ana makinedeki `~/modeller/whisper-medium-ov` yeniden dönüştürülmemeli.
2. **`adimadim model [ad]` komutu.** Profilleri, hangilerinin dönüştürüldüğünü ve aktif olanı listeler;
   ad verilirse aktif modeli değiştirir; model dönüştürülmemişse nasıl dönüştürüleceğini söyler.
3. **kur.sh.** Varsayılan olarak yalnızca aktif modeli dönüştürür; `--tum-modeller` ile hepsini.
   Bir modelin dönüştürülememesi diğer adımları durdurmaz, net biçimde raporlanır. Modele özel
   dönüştürme düzeltmeleri (bkz. Faz 3) kur.sh'nin içinde ve tekrarlanabilir olmalı.
4. **OpenVINO yolunu faster-whisper ile eşitle.**
   - Sessizlik ayıklama: şu anki genlik eşiği (0,01) kaba. faster-whisper'daki `vad_filter`'a denk bir
     VAD ekle; faster-whisper zaten bağımlılık olduğu için içindeki Silero VAD kullanılabilir.
   - Beam search: OpenVINO GenAI belgelerine göre beam search desteği mimariye bağlı; Whisper'da
     `num_beams` dene ve ölç.
   - GPU açılışı: `bitir` her seferinde modeli yeniden yüklüyor; OpenVINO'nun derleme önbelleğini
     (CACHE_DIR) değerlendir.
5. **stt_olc.py'yi genişlet:** ortografik WER, RTF, yükleme süresi, halüsinasyon ve uzun kayıt ölçümleri;
   `--model <ad>` ve `--set <gercek|sentetik|fleurs>` seçenekleri; sonuçlar
   `testler/sonuclar/<tarih>_<model>_<set>.json` olarak kaydedilir.
6. **`testler/karsilastir.py`:** seçilen modelleri aynı setlerde ölçüp tek bir Markdown tablo üretir
   (`testler/sonuclar/karsilastirma_<tarih>.md`). Ana makinede `cihaz: GPU` ile de çalışmalı.

**Kabul:** test.sh geçiyor; karsilastir.py referans modelle çalışıyor; duman testine profil ve `model`
komutu kontrolleri eklendi.

## Faz 1 — Test verisi

1. **Sentetik set** (yalnızca VM'de üretilir):
   - Terimleri bol kullanan, iş analisti anlatımına benzeyen 30-50 uydurma Türkçe cümle
     (`testler/sentetik/cumleler.txt`). Bir kısmı ekran anlatımı gibi olsun ("Şimdi müşteri hesabı
     ekranına geçiyoruz, burada tarife seçiliyor."). Gerçek şirket verisi yok.
   - Yerel bir Türkçe TTS ile seslendir (ör. Piper; birden fazla Türkçe ses varsa karıştır).
   - Koşullar: temiz; fan/klavye gürültüsü (SNR 10-20 dB); Bluetooth mikrofon benzetimi (8 kHz'e düşürüp
     16 kHz'e geri örnekleme); oda yankısı.
   - Ek klipler: 3 adet sessiz ya da yalnızca gürültü (halüsinasyon), 2 adet 45-60 saniyelik uzun anlatım.
   - Üretim tekrarlanabilir bir betikle yapılır (`araclar/sentetik_uret.py`, sabit rastgele tohum).
     TTS gibi geliştirme bağımlılıkları `kur.sh --gelistirme` ile kurulur; normal kurulum (ana makine)
     bunları kurmaz.
   - Üretilen WAV'lar (16 kHz mono) ve beklenen metinler commit'lenir; toplam boyut 30 MB'ı geçmesin.
2. **Bağımsız kıyas (önerilir):** `google/fleurs` Türkçe (tr_tr) test bölümünden sabit tohumla seçilmiş
   100 kayıtlık alt küme. Adayların model kartlarına göre eğitim verilerinde yok; kartlardaki iddiaları
   bağımsız sınar. Ses dosyaları repoya girmez, önbellekte tutulur; alt kümenin kimlik listesi repoya
   girer. Lisansı (CC BY 4.0) CHANGELOG'da belirt.
3. test.sh sentetik seti de ölçer; gerçek kayıtlar ve FLEURS varsa ayrı raporlar.

Model kararı gerçek kayıtlara göre verilir. Sentetik set regresyon ve göreli kıyas içindir; FLEURS genel
Türkçe kalitesini gösterir.

**Kabul:** Sentetik set commit'lendi; referans modelin tüm setlerdeki temel ölçümü CHANGELOG'da.

## Faz 2 — Aday 1: `Sercan/distil-whisper-large-v3-tr`

1. Profili ekle; kur.sh ile OpenVINO'ya (fp16) dönüştür; WhisperPipeline'da CPU'da yüklendiğini doğrula.
   Mimari standart `WhisperForConditionalGeneration` olduğu için ek düzeltme beklenmez; OpenVINO'nun
   Distil-Whisper için resmi örnek not defteri var.
2. **Bellek:** ~3 GB'lık F32 modeli dönüştürürken 8 GB RAM'li VM'de bellek yetmeyebilir. Yetmezse
   🛑 kullanıcıdan VM belleğini artırmasını iste; swap eklemek gibi sistem değişikliklerini kendin yapma.
3. Çözücü yalnızca 2 katmanlı: halüsinasyonu, uzun kayıt davranışını ve (Faz 5'te) ipucu metnine
   duyarlılığı özellikle ölç.
4. karsilastir.py ile referansla karşılaştır.

**Kabul:** Sonuç tablosu hazır; bulunan sorunlar CHANGELOG'da.

## Faz 3 — Aday 2: `Sercan/whisper-small-tr-2`

1. Yalnızca gerekli dosyaları indir (config, ağırlık, tokenizer, preprocessor, normalizer). `runs/`,
   `.ipynb_checkpoints/` ve `training_args.bin` indirilmez.
2. **Eğitim ayarlarını incele:** `run.sh`, model kartı ve `config.json`. Eğitimde metin küçük harfe
   çevrilmiş ya da noktalama kaldırılmışsa model noktalamasız yazar; bunu ortografik WER'le doğrula ve
   karşılaştırma tablosuna not düş. `forced_decoder_ids` ve `suppress_tokens` değerlerini de kontrol et.
3. **Eksik dosyaları tamamla.** Önce bu modelin `vocab.json` ve `merges.txt` dosyalarının
   `openai/whisper-small` ile birebir aynı olduğunu özet değeriyle doğrula. Aynıysa eksik
   generation_config.json'ı (`lang_to_id`, `task_to_id`, `suppress_tokens`, `no_timestamps_token_id` vb.)
   ve gerekirse tokenizer dosyalarını oradan al. Bu düzeltmeler kur.sh'nin dönüştürme adımında otomatik
   uygulanmalı.
4. **Ağırlıklar** `pytorch_model.bin` (pickle biçimi): yalnızca `torch.load(..., weights_only=True)` ile
   yükle. Kurulu transformers sürümü yüklemezse safetensors'a çevir; bu da dönüştürme adımına işlenir.
5. Dönüştür, yükle, karşılaştır.

**Kabul:** Faz 2 ile aynı.

## Faz 4 — Model kararı ve v0.2.0 🛑 (sonuç: whisper-medium kalır, bkz. CHANGELOG)

1. Referans ve iki aday için tüm setlerde karsilastir.py tablosunu hazırla.
2. **Karar kuralı:**
   1. Eleme: Sessiz kliplerde metin uyduran ya da uzun kayıtta kesilen/tekrarlayan model, bu sorun
      ayarla (VAD, eşik, çözme ayarları) giderilemiyorsa elenir.
   2. Gerçek kayıtlarda terim isabeti en yüksek olan kazanır.
   3. Fark 5 yüzde puanından azsa (küçük test setinde bu fark gürültü düzeyinde) ortografik WER'i düşük
      olan seçilir; o fark da 2 puandan azsa RTF'si düşük olan.
   4. Hiçbir aday referansı terim isabetinde geçemiyorsa referans kalır.
   5. Gerçek kayıt yoksa karar "geçici" olarak işaretlenir.
3. Tabloyu ve önerini kullanıcıya sun. Onay gelince varsayılan profili (ayar.ornek.json) değiştir ve
   mevcut kurulumların yeni modele nasıl geçeceğini CHANGELOG'a yaz.
4. 🛑 Push ve v0.2.0 etiketi için onay al; ardından ana makine teslimi (aşağıda).

## Faz 5 — Doğruluk katmanları ve v0.3.0

Seçilen model üzerinde çalış; her alt adımda önce ve sonra ölç. Kazandırmayan katman varsayılan
yapılmaz, ayarla açılabilir kalır.

- **5a. Terim ipucu.** terimler.txt ve terimler.local.txt'i Whisper'a ipucu olarak ver. OpenVINO GenAI
  belgelerine göre initial prompt ve hotwords destekleniyor; kurulu sürümde doğrula. İpucu en fazla
  yaklaşık 224 token olabilir; liste uzunsa o adıma en ilgili terimleri seç. İpucunu noktalamalı, düzgün
  Türkçe cümle olarak yaz; Whisper yazım üslubunu da ipucundan alır. İpucunun sessizlikte halüsinasyonu
  artırıp artırmadığını ölç.
- **5b. Ekrandan ipucu.** Her adımın ekran görüntüsünden yerel OCR (tesseract-ocr + tesseract-ocr-tur) ile
  kelimeleri çıkar, oturum.json'da sakla ve o adımın ipucuna ekle; OCR'dan gelen terimler önceliklidir.
  Test için uydurma form ekranları (alan adları, butonlar) üret ve sentetik cümlelerle eşleştir.
- **5c. Düzeltme sözlüğü.** `duzeltmeler.txt` (+ `.local`) ile "yanlış → doğru" kuralları. Ölçümlerdeki
  sık hatalardan bir başlangıç listesi öner.

**Kabul:** Her katmanın katkısı tabloda; test.sh geçiyor. 🛑 Push ve v0.3.0 onayı.

## Faz 6 — Rovo ile toparlama ✅ (karar: 2026-09-27)

Yerel LLM yerine şirketin resmi LLM'i Rovo kullanılır (kullanıcı kararı). adımadım ham ama terimleri
düzeltilmiş .md üretir; resmi senaryo diline çevirme elle Rovo agent'ında yapılır.
Agent talimatı: `rovo/ajan-talimati.md`; Confluence'taki sözlük sayfası: `rovo/confluence-sozluk.md`.

## Faz 7 — API çağrıları (HAR) ve v0.8.0 (2026-10-06)

Kullanıcı, dokümanda her ekrana gelen ve butonla giden API çağrılarını da görmek istiyor. Kararlar
(kullanıcı): ana makinede Firefox, F12 açılıyor; çağrılar tarayıcının Ağ sekmesinde görünüyor; API'ler
REST; dokümanda tablo + kısaltılmış gövde.

Yol: tarayıcının kendi ağ kaydı (HAR). Proxy (sertifika, şirket proxy'si/SSO çakışması), eklenti
(Firefox imza ister) ve canlı CDP (Firefox CDP'yi bıraktı, websocket bağımlılığı) elendi.

1. ✅ **Zaman.** `basla` → `baslangic`, `cek` → adımda `zaman`, `bitir` → `bitis` (saat dilimli ISO).
   Zamanı olmayan eski oturumlara API eklenemez, açık mesajla reddedilir.
2. ✅ **Akış.** Bayrak yok: bitmiş dokümana `adimadim api dosya.har [klasör]` ya da Bitiş ekranında
   "API ekle (HAR)" (İndirilenler'de açılan dosya seçici). .md `.md.yedek`'e alınıp yeniden üretilir,
   Word yenilenir; tekrar çalıştırmak çağrıları çoğaltmaz. Ham HAR kopyalanmaz (çerez/jeton içerir).
   Başla ekranı F12 → Ağ → Kayıtları sürdür'ü hatırlatır.
3. ✅ **Eşleme.** Adım N ile N+1'in çekimi arasındaki çağrılar: GET → Adım N+1 "Ekrana gelen";
   POST/PUT/PATCH/DELETE → Adım N "Butonla giden". İlk çekimden önceki GET'ler Adım 1'e, son çekimden
   sonrakiler son adıma; basla öncesi ve bitir sonrası (Kayıtları sürdür'ün eski kaydı) atılır.
4. ✅ **Ayıklama.** İstek ya da yanıtı JSON/XML olan (HTML/SVG değil) çağrılar; `api_filtre` doluysa yalnızca
   URL'si eşleşenler; status 0 (iptal) atılır; aynı adımda aynı metot+URL tek satır.
5. ✅ **Gizleme.** Başlıklar dokümana hiç yazılmaz. `api_gizle` anahtarları JSON'da (iç içe), XML öğesinde,
   `anahtar=değer`'de ve sorguda `***` olur.
6. ✅ **Çıktı.** `#### API çağrıları` tablosu (Yön | Metot | Uç nokta | Durum) + istek/yanıt `~~~json`/`~~~xml`
   blokları; diziler ilk öğeden sonra `… +N öğe`, en çok 40 satır / 3000 karakter.
7. ✅ **Python 3.10.** "Z" sonekli ve 3/6 dışı kesirli zamanlar normalize edilir; base64 gövde çözülür.
8. ✅ **Test.** Duman testi Firefox 157 HAR 1.2 biçiminde (kullanıcının VM'de aldığı gerçek HAR'dan
   çıkarıldı) girdi üretir: eşleme, tekrar, kısaltma, JSON/XML/sorgu maskeleme, aralık dışı/css/analitik
   atma, ~~~ blokları, yalnızca analitik içeren HAR'ın reddi; pencerede "API ekle (HAR)".
   Kullanıcının gerçek HAR'ı (yalnızca analitik) hatasız okundu, iki çağrı da süzüldü.

Bilinen sınırlar: Ağ sekmesi yalnızca açıkken kaydeder; akış yeni sekme/açılır pencere açarsa oradaki
çağrılar kaçar. Hepsi-POST API'lerde (SOAP/GraphQL) yön bilgisi yanlış olur. Gövdesiz 204 yanıtlı
çağrılar (ör. DELETE) varsayılan süzgeçte görünmez; `api_filtre` ile alınır.

**Kabul:** test.sh geçiyor; ana makinede Firefox ile gerçek bir akışta API tablosu doğru adımlarda.
🛑 Push ve v0.8.0 onayı.

## Her sürümde: ana makine teslimi

Ana makinede Claude Code yok; CHANGELOG'daki "Ana makinede yapılacaklar" bölümü, kullanıcının kopyalayıp
çalıştırabileceği kadar net olmalı ve şunları içermeli:

1. `git pull && ./kur.sh && ./test.sh`
2. İndirilecek ve dönüştürülecek modeller, tahmini süre ve disk ihtiyacı; dönüştürmeden sonra Hugging Face
   önbelleğindeki orijinal ağırlıkların nasıl temizleneceği.
3. GPU doğrulaması: karsilastir.py'yi `cihaz: GPU` ile seçilen model ve medium için çalıştıran tek komut.
   Sonuçlar VM'deki CPU sonuçlarıyla tutarlı olmalı; kullanıcı yalnızca çıktıyı geri getirir.
4. Gerçek kullanımla deneme: `adimadim basla "Deneme" --ses` ile birkaç ekranlık kısa bir doküman ve
   `adimadim bitir`.

## Düşük öncelikli işler

Faz 6'dan sonra ya da bir faz beklerken ele alınabilir:

- `bitir` için klavye kısayolu (GNOME'un mevcut kısayollarıyla çakışmayan bir tuş).
- Sesli modda kaydın sürdüğünü gösteren görünür bir gösterge.

## Kontrol noktaları

| Yer | Neden durulur |
|---|---|
| Başlarken | Gerçek test kayıtlarını iste; Windows desteği hedefleniyor mu sor (ikisinde de beklemeden devam et) |
| Faz 2 | Bellek yetmezse VM RAM artırımı |
| Faz 4 | Model kararı onayı, push ve v0.2.0 |
| Faz 5 | Push ve v0.3.0 |
| Faz 6 | LLM model seçimi, push ve v0.4.0 |
| Faz 7 | Push ve v0.8.0 |

## Kapsam dışı

- Bulut konuşma tanıma servisleri ya da aracın çalışırken ağa veri göndermesi.
- VM'e GPU aktarımı.
- Ana makinede elle sistem değişikliği gerektiren çözümler; her şey kur.sh üzerinden.
- Bu iki aday dışında model denemek (kullanıcı onayı olmadan).
