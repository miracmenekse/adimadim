# Arka plan ve kararlar

Bu dosya, projenin tasarlandığı sohbetin özetidir: neyin neden seçildiği, neyin denenip bırakıldığı ve
açık kalan kararlar. Kurallar CLAUDE.md'de, iş planı YOL_HARITASI.md'dedir.

## Kullanıcı ve ihtiyaç

- Kullanıcı bir iş analisti; telekom/BSS alanında teknik analiz, tasarım ve dokümantasyon yapıyor.
  Kullanıcıyla Türkçe yazışılır.
- İhtiyaç: bir iş akışını ekranda adım adım gezerken her ekranı yakalamak, her adımda ne yapıldığını
  yazarak ya da konuşarak anlatmak ve sonunda görselli bir kullanım senaryosu dokümanı elde etmek.

## Temel ilkeler

1. **Şirket verisi Claude'a ya da herhangi bir buluta gitmez.** Araç tamamen yerel çalışır; ekran
   görüntüleri, ses ve metin makinede kalır. Claude Code bu yüzden şirket araçlarına bağlanmadı.
2. **Claude yalnızca aracın kodunu ve uydurma test verisini görür.** Geliştirme izole bir VM'de,
   gerçek kullanım ana makinede yapılır; iki makine yalnızca bu GitHub reposu üzerinden konuşur.
3. **Tekrarlanabilir kurulum.** VM'de ne yapıldıysa ana makinede `git pull && ./kur.sh && ./test.sh`
   ile aynı sonuç alınmalı. Ana makinede Claude Code yok; komutları kullanıcı çalıştırır.

## Araç tasarımı (v0.1.0)

- Akış: `adimadim basla "Başlık" [--ses]` → her ekranda Ctrl+Alt+S (ekran görüntüsü + yeni adım) →
  `adimadim bitir` (.md + .docx). Ctrl+Alt+N son adımın notunu açar; `geri` son adımı siler.
- Yazılı modda her çekimde not penceresi açılır. Sesli modda anlatım bir sonraki Ctrl+Alt+S'ye kadar o
  adıma kaydedilir ve `bitir`'de toplu olarak metne çevrilir.
- Çıktı kullanım senaryosu biçiminde: Amaç, Aktör, Ön koşullar, Son koşullar ve Ana akış (her adımda
  görsel + metin). Markdown Obsidian'da açılabilir; Word pandoc ile üretilir, şirket şablonu
  `~/.config/adimadim/sablon.docx` olarak verilebilir.
- `word` elle düzeltilmiş .md'den Word'ü yeniler; `yeniden` bir dokümanın ses kayıtlarını güncel modelle
  baştan çevirir; `cevir` tek ses dosyasını çevirir.

## Konuşma tanıma: şimdiye kadar

- İlk sürümde faster-whisper "small" (CPU) kullanıldı; Türkçe'de yetersiz kaldı.
- Ana makinede Intel GPU ve NPU var. faster-whisper yalnızca NVIDIA'da hızlandığı için OpenVINO'ya
  geçildi. `openai/whisper-medium` fp16 olarak `~/modeller/whisper-medium-ov` klasörüne dönüştürüldü ve
  ayar GPU'ya çevrildi. GPU yolunun gerçekten çalıştığı henüz doğrulanmadı (`bitir` çıktısında
  "GPU üzerinde metne çevriliyor" satırı görülmeli).
- Ağırlık biçimi: fp16 seçildi. int8 kabul edilebilir; int4 kaliteyi belirgin biçimde bozar.
- OpenVINO yolunda faster-whisper'daki VAD ve beam search yok; eşitlenmesi yol haritasında.
- Aday modeller, Sercan Çepni'nin Hugging Face sayfasındaki 8 model incelenerek seçildi:
  `Sercan/distil-whisper-large-v3-tr` (en güçlü taban, Türkçe'ye damıtılmış) ve kullanıcının small
  modeller arasından seçtiği `Sercan/whisper-small-tr-2`. Elenenler: `distil-whisper-medium-tr` ve
  `wav2vec2-xls-r-300m-call` boş repolar; `wav2vec2-*` modelleri Whisper değil (CTC mimarisi),
  altyapıya uymuyor ve bildirilen WER %28,6; diğer iki small model small-tr-2 ile aynı sınıfta.

## Ses kaydı kalitesi: bulgular

- Kalitenin ilk engeli modelden önce mikrofondu. Dahili mikrofon %153'e (+11 dB) yükseltilmişti ve
  varsayılan giriş "Echo-Cancel Source" idi; kayıtlar kirliydi. Seviye %100'e çekildi.
- Bluetooth kulaklık (HUAWEI FreeBuds SE) mikrofon modunda PulseAudio ile robotik sesliydi. Ana makinede
  PipeWire'a geçildi; 22.04'ün PipeWire'ı daha da kötü sonuç verince PipeWire upstream PPA'sı ve HWE
  çekirdeği kuruldu. Şimdi kulaklık mikrofonu kullanılabilir durumda (kullanıcının ifadesiyle
  "fena değil"); kodekin (mSBC) seçili olduğu doğrulanmadı.
- Kullanıcı bu kulaklıkla Teams toplantılarına da giriyor. Ses ayarlarına dokunan çözümler önermeden
  önce sor.
- Ders: konuşma tanıma sonucunu değerlendirmeden önce kaydı dinle. Test kayıtları gerçek mikrofonla,
  ana makinede alınır.

- **Ölçüm (2026-10-30):** ana makinede varsayılan giriş `bluez_output…monitor` (kulaklık A2DP'de), arecord
  kulaklıkta çalan sesi kaydediyordu. FreeBuds mikrofonu (`bluez_input`) A2DP'de tamamen sıfır veri veriyor;
  PipeWire kendiliğinden görüşme moduna geçmiyor. `headset-head-unit-msbc` profiliyle `parecord --device`
  temiz kayıt aldı. Tek 12 kelimelik cümle, whisper-medium: Digital Microphone 3 hata (~21 dB), FreeBuds
  mSBC 2 hata (~51 dB), CVSD 1 hata (~42 dB). Örneklem küçük.
- **Karar (Kullanıcı A seçeneğini seçti):** adımadım kulaklık profilini yalnız sesli oturum boyunca yönetir,
  bitince eski profile döner; sistem varsayılan girişine (`set-default-source`) dokunulmaz, çünkü kullanıcı
  Teams kullanıyor. Ayarlar `mikrofon` ve `mikrofon_profil` (ikisi de boşsa eski davranış).
- Kayıt sırasında kulaklığın ses kalitesi düşer (görüşme profili). Bu bilinen bir ödünleşim.
- 2026-10-15'teki BT kart çökmesinde görüşme modu şüpheliydi; kanıtlanmadı.

## Ana makine hakkında bilinenler

- Ubuntu 22.04, GNOME, Python 3.10; Intel GPU ve NPU.
- Kurumsal bir güvenlik ajanı çalışıyor. HWE çekirdeğine geçildikten sonra ajanın bu çekirdekte tam
  çalıştığı doğrulanmadı. Çekirdek ya da sürücü değişikliği önerme; sistem düzeyinde bir değişiklik
  gerekiyorsa önce kullanıcıya sor.
- 22.04 paketleriyle yaşanan sorunlar: sistem pip'i bağımlılık çözerken çöktü (pip güncellenerek
  çözüldü); sistem Pillow'u (9.0) yeni transformers için eski kaldı; `optimum-intel` kurulumu CUDA'lı
  PyTorch'u ve birkaç GB NVIDIA paketini de indirdi. kur.sh bu yüzden ayrı bir venv, güncel pip ve CPU
  PyTorch kullanıyor.
- Kullanıcı daha önce `pip --user` ile openvino-genai, optimum-intel ve faster-whisper kurdu; kur.sh
  bunlara dokunmaz. O ortamdaki gereksiz CUDA paketleri henüz temizlenmedi. Temizlik ai-terminal'i
  etkileyebilir; önce onun hangi Python ortamını kullandığına bakılmalı.
- `ai-terminal` adlı yerel asistan OpenVINO ile GPU'da bir LLM çalıştırıyor; Faz 6'da yeniden
  kullanılabilir.

## Açık kararlar

- **Windows desteği.** Kullanıcı aracı Windows kullanan birine vermeyi düşünüyor; karar verilmedi
  (YOL_HARITASI.md, Başlarken).
  - Taşınabilen: OpenVINO + Whisper ve doküman üretimi.
  - Linux'a bağlı olan: gnome-screenshot, zenity, GNOME kısayolları, arecord, notify-send, fcntl,
    /proc ve kur.sh/apt. Kod Windows'ta daha açılışta `import fcntl` satırında durur.
  - Gerekenler: kısayolları kendisi dinleyen ve sesi kendi içinde kaydeden tek parça bir uygulama
    (ör. mss, sounddevice, tkinter; Word için python-docx); Windows paketi (ör. PyInstaller + kurulum
    sihirbazı); kurumsal engellere hazırlık (imzasız .exe'de SmartScreen uyarısı, IT onayı; kısayollar
    tüm tuşları dinleyen klavye kancasıyla değil RegisterHotKey ile).

## İş akışı gruplama ve komut kuralı (2026-10-30)

- **Komut kuralı** (kullanıcı kararı; `calisan_komutlar` buna uyar):
  - pre=0, post=0: durum içinde işlem yapılınca (during).
  - pre=1: yeni duruma geçilirken, durum başlarken.
  - post=1: durum biterken, sonraki durumun pre'sinden önce.
  - İkisi birden 1 olmaz. Durum içinde sıra: pre, during, post; her biri kendi içinde sort_id. CSV sırası akış sırasıdır.
- **Ekran sınırı:** `orderSubmit` (`son_ekran_durumu`) sonrası süren durumlar arka uçta çalışır ve HAR'da görünmez.
  Bu durumlar ekran adımı sayılmaz; "Arka planda çalışan durumlar" bölümüne gider. Sınır repo ile ana makinede aynıdır (kullanıcı kararı).
- **Sabit geçiş:** `initialize` ve `submit` çağrıları iş akışı alanı (`currentWorkFlowStateShortCode`) taşımaz; bu yüzden
  geçiş `sabit_gecisler` ile bilinir. Geçiş kayda yazılmaz, eski dokümanlar HAR'sız çalışır.
- **Geri dönüş:** aynı duruma dönüş ayrı grup olur; adım sırası (kronoloji) korunur.
- **Karar noktası:** sesli kalıp `Karar noktası: <koşul> → <sonuç>` seçildi. Rovo bunu `> **Karar noktası:** <koşul> → <sonuç>` bloğuna çevirir; her dal ayrı satır.
