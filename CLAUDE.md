# adımadım — Claude Code çalışma kuralları

## Proje

Ekrandan ekrana gezerken alınan ekran görüntüleri ve kullanıcının sesli/yazılı anlatımından
kullanım senaryosu dokümanı (.md + .docx) üreten yerel bir araç. Kullanıcı bir iş analisti;
dokümanlar Türkçe ve telekom/BSS alanında. Asıl sorun: konuşma tanıma, alan terimlerini
ve Türkçe anlatımı yeterince doğru yazmıyor.

Projenin arka planı, alınan kararlar ve gerekçeleri, ana makine hakkında bilinenler ve açık kararlar
`KARARLAR.md`'dedir; işe başlamadan önce oku.

## İki ortam

|                          | Geliştirme (bu VM)      | Kullanım (ana makine)                  |
|--------------------------|-------------------------|----------------------------------------|
| İşletim sistemi          | Ubuntu 22.04, Python 3.10, GNOME | aynı                          |
| Konuşma tanıma cihazı    | OpenVINO CPU            | OpenVINO Intel GPU (NPU isteğe bağlı)  |
| Claude Code              | var                     | YOK: komutları kullanıcı çalıştırır    |
| Gerçek şirket verisi     | YOK                     | var                                    |
| sudo                     | yalnızca `apt-get`, şifresiz (kur.sh için); başka sudo gerekirse kullanıcıya sor | komutları kullanıcı çalıştırır |

Ana makineye yalnızca git üzerinden, etiketli sürümler gider:
`git pull && ./kur.sh && ./test.sh`. Ana makinede senin yapacağın hiçbir şey yok;
her şey bu üç komutla tekrarlanabilir olmalı. Ana makinenin Ubuntu kurulumu eksik olabilir: VM'de
kurulu olduğu için çalışan hiçbir şeyi orada da var sayma. İki makinenin ilk kurulumu, günlük akış
ve ana makineden geri bildirimin nasıl geldiği `CALISMA_DUZENI.md`'dedir. `vm-ana-makine` becerisini
(`beceriler/vm-ana-makine/SKILL.md`) izle: push'tan önce `.ortam/ortam.sh kaydet && .ortam/ortam.sh denetle`
temiz olmalı; ana makineden gelen geri bildirim `.ortam/ortam.sh kontrol` çıktısıdır.

## Kurallar

1. **Tekrarlanabilirlik.** Kalıcı her sistem değişikliği (apt, pip, model, ayar anahtarı,
   kısayol, dosya yolu) kur.sh ya da requirements üzerinden yapılır. Deneme için elle bir şey
   kurduysan ve kalacaksa kur.sh'ye işle, sonra kur.sh'yi yeniden çalıştırarak doğrula.
   kur.sh idempotent kalmalı ve ayar.json'daki mevcut değerleri ezmemeli (yalnızca eksik anahtar ekler).
   Terminalde elle çalıştırdığın her kurulum ya da ayar komutu ya kur.sh'ye işlenir ya da, yalnızca
   bir kez gerekiyorsa, CHANGELOG'daki "Ana makinede yapılacaklar"a birebir, kopyala-yapıştır komut
   olarak yazılır. Kodun ya da testlerin çağırdığı her dış komutun paketi kur.sh'deki `PAKETLER`'dedir.
2. **Bağımlılıklar.** Doğrudan bağımlılık requirements.txt'e yazılır; ardından
   `rm requirements.lock && ./kur.sh` ile kilit yeniden üretilip commit'lenir. PyTorch yalnızca
   CPU sürümü (CUDA paketi indirilmez). Python 3.10 uyumu zorunlu: 3.11+ sözdizimi ya da
   kütüphanesi kullanma.
3. **Makineye özel her şey ayar.json'da.** Kodda sabit cihaz adı ya da mutlak yol yok. Yeni ayar
   anahtarı: ayar.ornek.json'a varsayılanıyla ekle, adimadim.py'nin başındaki açıklamaya ve README'ye yaz.
4. **Veri.** Bu VM'e ve repoya gerçek şirket verisi girmez: gerçek ekran görüntüsü, müşteri bilgisi,
   şirkete özel terim yok. Testler uydurma ekranlar ve kullanıcının okuduğu genel cümlelerle yapılır.
   Şirkete özel terimler ana makinede `~/.config/adimadim/terimler.local.txt` dosyasındadır;
   kod bu dosyayı (ve ileride `duzeltmeler.local.txt` gibi eşlerini) okuyabilmeli ama içeriğine
   hiçbir test ya da varsayım bağlı olmamalı.
5. **Gizlilik.** Araç çalışırken ağa veri göndermez. İnternet yalnızca kurulumda (paket, model indirme).
6. **Test.** Her değişiklikten sonra `./test.sh` geçmeli. Yeni özellik = `testler/duman_testi.py`'ye
   yeni kontrol. Doğruluğu etkileyen her değişiklikten önce ve sonra `testler/stt_olc.py` ile ölç.
7. **CHANGELOG.** Her sürümde: ne değişti, ölçüm sonucu, ve "Ana makinede yapılacaklar"
   (ör. "kur.sh yeni modeli dönüştürür, ~10 dk sürer").
8. **Git.** Küçük, açıklamalı commit'ler. Push ve sürüm etiketi (v0.x.y) kullanıcı onayıyla
   (`.claude/settings.json` ikisini de onaya bağlar). Ana makinenin izlediği dal `main`.
9. **Dil.** Kullanıcıyla yazışma ve kullanıcıya dönük her metin (bildirim, hata mesajı, doküman) Türkçe.
10. **GPU/NPU.** Bu VM'de GPU/NPU yok. Cihaza özgü kod her zaman CPU'ya ya da yedek motora zarifçe
    düşmeli; bu kısımları CHANGELOG'da "ana makinede doğrula" diye işaretle.
11. **Yalnızca ana makinede yapılabilenler** (GPU/NPU, gerçek mikrofon, gerçek veriyle deneme): kullanıcıya
    kopyala-yapıştır komut ver ve geri getirmesi gereken çıktıyı tam olarak söyle (ör. tek bir özet ya
    da hata satırı). Şirket verisi içerebilecek çıktı (doküman metni, ekran görüntüsü) isteme.

## Mimari

- `adimadim.py`: tek giriş noktası. Komutlar: basla, cek, not, geri, durum, bitir, word, yeniden, cevir, kisayol.
  Gerekirse modüllere bölünebilir; komut satırı arayüzü korunmalı.
- Oturum klasörü: `oturum.json` (kaynak), `gorseller/`, `ses/`, `<Başlık>.md`, `<Başlık>.docx`.
  Oturum açıkken .md her kayıtta oturum.json'dan yeniden üretilir; bitince .md elle düzenlenebilir,
  `word` komutu .docx'i ondan üretir.
- Konuşma tanıma: tümü `cevirici_olustur(ayar)` üzerinden geçer (OpenVINO GenAI WhisperPipeline;
  hata olursa faster-whisper). Model kur.sh'de optimum-cli ile `ov_kaynak` → `ov_model` dönüştürülür
  (`LC_ALL=C.UTF-8`: Türkçe locale tokenizer'ı bozar). Katmanlar: Silero VAD (konuşma yoksa boş),
  `ipucu` (terimler.local + sözlük + terimler.txt, doğal cümleyle biten initial_prompt; ~700 karakter),
  `duzeltme` (duzeltmeler.txt + .local, Türkçe eki koruyan "yanlış → doğru"). Model: whisper-medium
  (Türkçe adaylar elendi, bkz. CHANGELOG v0.3.0). Resmi dile çevirme Rovo'da (`rovo/`).
  Motorlar `parcala(ses) -> [(bas, son, metin)]` döndürür; `bitir`/`yeniden` adımların seslerini
  birleştirip tek seferde çevirir ve cümleleri başladıkları adıma dağıtır (`adimlara_dagit`):
  adım adım çevirmek sınırda kelime kaybettiriyordu (gerçek oturumda WER %93 → %7,6).
- Testler: `testler/duman_testi.py` (sahte ekran/mikrofon/model ile uçtan uca), `testler/stt_olc.py`
  (testler/ses/*.wav + .txt ile WER ve terim isabeti), `testler/karsilastir.py` (model/ayar
  karşılaştırması: `--ses <klasör>` ya da `--fleurs 100`, `--ayar k=v`), `araclar/kayit_al.sh`
  (ana makinede test kaydı; `paragraflar` ikinci set). `testler/gercek/`: gerçek bir oturumun adım sesleri + referans metin. Ana makinedeki arecord WAV başlık uzunluğunu
  bozuk bırakabiliyor; okuyan kod veriyi sonuna kadar okur.

## Yol haritası

Güncel yol haritası `YOL_HARITASI.md`'dedir. Fazları sırayla uygula; 🛑 işaretli noktalarda dur ve
kullanıcıya sor. Bir faz bittiğinde bu dosyadaki Mimari bölümünü de güncel tut.
