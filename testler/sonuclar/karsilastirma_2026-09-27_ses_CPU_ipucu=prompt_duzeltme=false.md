# Karşılaştırma — ses, 29 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov [ipucu=prompt] [duzeltme=False] | %85.3 (81/95) | %48.9 | %65.6 | 1.39 | 2.1 |

## whisper-medium-ov [ipucu=prompt] [duzeltme=False] — kaçan terimler
shopping cart (2), interaction (2), Save and Close (2), fatura (1), faturalı hat (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), device (1), Dhiragu (1), call center (1), category (1), command (1)

## whisper-medium-ov [ipucu=prompt] [duzeltme=False] — örnekler
- beklenen: Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
  çıktı:    CSR 360 ekranında müşterinin Freedom Fatrı Ola hattına ait product'a tıklıyoruz. Product detail sayfası açılıyor.
- beklenen: Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
  çıktı:    Manage button, BI listesi,
- beklenen: Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
  çıktı:    Listeden Device Upgrade seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
- beklenen: Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
  çıktı:    Change the plan seçeneni seçip ilerliyoruz. Qualification API uygun planları getiriyoruz.
- beklenen: Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
  çıktı:    Fizz tarifesini seçiyoruz ve Next'e tıklıyoruz.
