# Değişiklikler

Her sürümde: ne değişti, ölçüm sonucu (varsa) ve **Ana makinede yapılacaklar**.

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
