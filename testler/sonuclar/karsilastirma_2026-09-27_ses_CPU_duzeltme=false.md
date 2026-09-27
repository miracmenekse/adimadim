# Karşılaştırma — ses, 29 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov [duzeltme=False] | %67.4 (64/95) | %29.0 | %41.0 | 2.18 | 3.0 |

## whisper-medium-ov [duzeltme=False] — kaçan terimler
interaction (4), category (3), shopping cart (2), sub category (2), fatura (1), faturalı hat (1), Fizz (1), Qualification (1), business interaction (1), Device Upgrade (1), device (1), Continue without plan change (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), CSR (1), drawer (1), Save and Close (1), Dhiragu (1), call center (1), ECA (1), command (1), BI (1), New BI geliştirmeleri (1), Etiya Buddy (1), Unit Peace (1)

## whisper-medium-ov [duzeltme=False] — örnekler
- beklenen: Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
  çıktı:    Şimdi CSR 360 ekranında müşterinin Freedom Fatrı Ola hattına ait producta tıklıyoruz. Product Detail sayfası açılıyor.
- beklenen: Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
  çıktı:    Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
- beklenen: Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
  çıktı:    Listeden Device Upgrade seçiyoruz. Karşımıza iki seçenekli bir pop-up çıkıyor.
- beklenen: Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
  çıktı:    Change the plan seçeneni seçip ilerliyoruz. Qualification API uygun planları getiriyoruz.
- beklenen: Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
  çıktı:    Müşteriye uygun olan FIS tarifesini seçiyoruz ve Next'e tıklıyoruz.
