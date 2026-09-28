# adımadım

Ekrandan ekrana gezerken ekran görüntüsü alıp her adımı yazarak ya da sesle anlattığın,
sonunda elinde kullanım senaryosu (.md + .docx) olan yerel araç. Görüntüler, notlar ve
ses kayıtları makineden çıkmaz.

**İlk kez mi kuruyorsun?** VM'de geliştirme ve ana makinede kullanım düzeninin adım adım kurulumu:
[CALISMA_DUZENI.md](CALISMA_DUZENI.md). Aynı düzeni her projeye taşıyan Claude Code becerisi:
[beceriler/vm-ana-makine](beceriler/vm-ana-makine/SKILL.md).

## Kurulum (VM'de ve ana makinede aynı)

Repoyu klonladıktan sonra (klonlama ve GitHub erişimi: CALISMA_DUZENI.md):

    ./kur.sh     # sistem paketleri, Python ortamı, model, komut, kısayollar
    ./test.sh    # her şeyin çalıştığını doğrular

## Kullanım

Uygulama menüsünden **adımadım**'ı aç: bütün adımlar düğmelerle yapılır. Çekilen görsele tıklayınca kırpılabilir, üzerine kutu/ok/yazı eklenebilir;
bitiş ekranında .md panoya kopyalanır ve Rovo çıktısı yapıştırılınca .md ile Word güncellenir. Komut satırı da aynen çalışır:

    adimadim basla "Sipariş iptal akışı"      # sesle anlatmak için sonuna --ses
    Ctrl+Alt+S                                # her ekranda: görüntü al, notunu yaz / anlat
    Ctrl+Alt+N                                # son adımın notunu düzelt
    adimadim geri                             # yanlış çekimi sil
    adimadim bitir                            # .md + .docx üret, klasörü aç
    adimadim word                             # .md'yi elle düzelttikten sonra Word'ü yenile
    adimadim yeniden                          # ses kayıtlarını güncel modelle baştan çevir
    adimadim cevir kayit.wav                  # tek bir ses dosyasını metne çevir
    adimadim arayuz                           # düğmeli pencere

## Ayarlar

`~/.config/adimadim/ayar.json` (kur.sh oluşturur, varsayılanlar `ayar.ornek.json`'da):

| Anahtar          | Anlamı                                                      |
|------------------|-------------------------------------------------------------|
| `klasor`         | dokümanların yeri; boşsa Belgeler/adimadim (ör. Obsidian vault) |
| `ekran`          | `pencere` (aktif pencere) ya da `tam`                       |
| `stt`            | `openvino` (varsayılan) ya da `faster-whisper`              |
| `cihaz`          | `CPU`, `GPU`, `NPU` (ilk kurulumda otomatik algılanır)      |
| `ov_kaynak`      | dönüştürülecek Whisper modeli                               |
| `ov_model`       | dönüştürülmüş modelin klasörü                               |
| `whisper_modeli` | OpenVINO çalışmazsa yedek faster-whisper modeli             |
| `dil`            | anlatım dili, varsayılan `tr`                               |
| `ipucu`          | terimleri Whisper'a ipucu olarak ver: `prompt`, `hotwords` ya da boş (kapalı) |
| `duzeltme`       | `duzeltmeler.txt` (+ `.local`) kurallarını çıktıya uygula (`true`/`false`) |

Şirket Word şablonu: `~/.config/adimadim/sablon.docx`.
Şirkete özel terimler: `~/.config/adimadim/terimler.local.txt` (repoya girmez).
Şirkete özel düzeltmeler ("yanlış → doğru"): `~/.config/adimadim/duzeltmeler.local.txt` (repoya girmez).

## Geliştirme akışı

    VM:           Claude Code geliştirir → ./test.sh → commit + etiket → push
    Ana makine:   git pull && ./kur.sh && ./test.sh
    Sorun olursa: yalnızca hata metnini VM'deki Claude Code'a ver

İlk kurulum, günlük akış, geri bildirim ve sorun giderme `CALISMA_DUZENI.md`'de;
Claude Code'un kuralları `CLAUDE.md`'de, projenin arka planı ve kararları `KARARLAR.md`'de,
iş planı `YOL_HARITASI.md`'de.
