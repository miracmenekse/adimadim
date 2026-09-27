# Değişiklikler

Her sürümde: ne değişti, ölçüm sonucu (varsa) ve **Ana makinede yapılacaklar**.

## Yayınlanmamış

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

**Ana makinede yapılacaklar:** `git pull && ./kur.sh && ./test.sh` (model yeniden indirilmez, ~1 dk).
Bozuk model varsa kur.sh çıktısında `Onarıldı: …openvino_tokenizer.xml` görünür. Geri getirilecek:
test.sh'deki `✓ OpenVINO modeli yüklendi: … GPU` satırı (ya da `✗` satırı ve üstündeki hata).

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
