# Karşılaştırma — ses, 29 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov [ipucu=prompt] [duzeltme=True] | %90.5 (86/95) | %16.4 | %27.1 | 1.71 | 1.2 |

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — kaçan terimler
category (3), Save and Close (2), fatura (1), faturalı hat (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), sub category (1)

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — örnekler
- beklenen: Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
  çıktı:    Şimdi CSR 360 ekranında müşterinin Freedom Fatrıola hattına ait product'a tıklıyoruz. Product detail sayfası açılıyor.
- beklenen: Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
  çıktı:    Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
- beklenen: Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
  çıktı:    Listeden Device Upgrade seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
- beklenen: Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
  çıktı:    Change the plan seçeneğini seçip ilerliyoruz. Qualification API uygun planları getiriyoruz.
- beklenen: Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
  çıktı:    Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e tıklıyoruz.
