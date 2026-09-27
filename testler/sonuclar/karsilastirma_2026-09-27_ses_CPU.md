# Karşılaştırma — ses, 29 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov | %66.3 (63/95) | %29.0 | %41.0 | 1.26 | 3.5 |
| distil-large-v3-tr-ov | %14.7 (14/95) | %58.9 | %70.0 | 1.74 | 1.5 |
| whisper-small-tr-2-ov | %28.4 (27/95) | %46.8 | %64.3 | 0.38 | 1.1 |

## whisper-medium-ov — kaçan terimler
interaction (4), category (3), shopping cart (2), sub category (2), fatura (1), faturalı hat (1), Fizz (1), Qualification (1), business interaction (1), Device Upgrade (1), device (1), Continue without plan change (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), CSR (1), CSR 360 (1), drawer (1), Save and Close (1), call center (1), Dhiragu (1), ECA (1), command (1), BI (1), New BI geliştirmeleri (1), Etiya Buddy (1), Unit Peace (1)

## whisper-medium-ov — örnekler
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

## distil-large-v3-tr-ov — kaçan terimler
device (6), CSR (5), interaction (5), Manage (4), Qualification (3), call center (3), toaster (3), category (3), product detail (2), CSR 360 (2), Device Upgrade (2), pop-up (2), shopping cart (2), Submit (2), CSR sayfası (2), RM ticket (2), drawer (2), detail modu (2), sub category (2), reason (2), channel (2), Add Note (2), Save and Close (2), Freedom (1), Change the plan (1), Qualification API (1), Fizz (1), Payment (1), Darwin (1), business interaction (1), Continue without plan change (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), Root ekibi (1), BI tarafında bir hata (1), parent-child (1), Dhiragu (1), Account Management (1), command (1), BI (1), New BI geliştirmeleri (1), Etiya Buddy (1), Unit Peace (1)

## distil-large-v3-tr-ov — örnekler
- beklenen: Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
  çıktı:    Şimdi Siyasal 360 ekranında müşterinin Fredin Faturalı hattına ait prodakta tıklıyoruz. Program Detel sayfası açılıyor.
- beklenen: Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
  çıktı:    Burada sağ üstteki menaj botonuna basıyoruz ve biray listesi geç.
- beklenen: Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
  çıktı:    Listeden Divaysap krali seçiyoruz. Karşımıza iki seçenekli bir popap çıkıyor.
- beklenen: Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
  çıktı:    Çenç The Plan seçeneni seçip ilerliyoruz. KALifikasyon api uygun planları getiriyor.
- beklenen: Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
  çıktı:    Müşteriye uygun olan fili tarifesini seçiyoruz ve Nexte tıklıyoruz.

## whisper-small-tr-2-ov — kaçan terimler
CSR (5), interaction (5), device (3), category (3), product detail (2), CSR 360 (2), pop-up (2), shopping cart (2), Submit (2), CSR sayfası (2), RM ticket (2), Manage (2), detail modu (2), sub category (2), reason (2), channel (2), Add Note (2), Save and Close (2), fatura (1), faturalı hat (1), Freedom (1), tarife (1), Fizz (1), Qualification (1), Darwin (1), business interaction (1), Device Upgrade (1), Continue without plan change (1), Number/SIM card için shopping cart üzerinde eksik kontrol var (1), BI tarafında bir hata (1), toaster (1), call center (1), parent-child (1), Dhiragu (1), drawer (1), Account Management (1), ECA (1), command (1), BI (1), New BI geliştirmeleri (1), Etiya Buddy (1), Unit Peace (1)

## whisper-small-tr-2-ov — örnekler
- beklenen: Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
  çıktı:    şimdi siyasar üç altmış ekranında müşterinin feridun faturola hatlına ait prolak ta tıklıyoruz prolak deeteli sayfası açılıyor
- beklenen: Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
  çıktı:    burada sağ üstteki manage butonuna basıyoruz ve bir ay listesi geldi
- beklenen: Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
  çıktı:    listeden device upgrade seçiyoruz karşımıza iki seçenekli bir popup çıkıyor
- beklenen: Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
  çıktı:    change the plan seçeneni seçip ilerliyoruz qualification api uygun planları getiriyor
- beklenen: Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
  çıktı:    müştereye uygun olan fista harifesini seçiyoruz ve nexte tıklıyoruz
