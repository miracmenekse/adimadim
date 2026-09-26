# Değişiklikler

Her sürümde: ne değişti, ölçüm sonucu (varsa) ve **Ana makinede yapılacaklar**.

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
