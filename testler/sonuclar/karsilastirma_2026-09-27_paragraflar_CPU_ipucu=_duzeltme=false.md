# Karşılaştırma — paragraflar, 10 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| distil-large-v3-tr-ov [ipucu=] [duzeltme=False] | %13.6 (9/66) | %47.9 | %56.7 | 0.74 | 1.0 |

## distil-large-v3-tr-ov [ipucu=] [duzeltme=False] — kaçan terimler
Manage (4), device (4), interaction (3), CSR (2), call center (2), detail modu (2), Add Note (2), Fizz (1), CSR 360 (1), product detail (1), business interaction (1), Device Upgrade (1), pop-up (1), Change the plan (1), Qualification API (1), Qualification (1), shopping cart (1), RM ticket (1), Root ekibi (1), Payment (1), Submit (1), toaster (1), drawer (1), category (1), sub category (1), reason (1), channel (1), Account Management (1), Save and Close (1), parent-child (1), Darwin (1), New BI geliştirmeleri (1), Obeya (1), heatmap & resource allocation (1), metrics (1), Windsurf (1), Hexagonal architecture (1), Low-code (1), command (1), playground (1), Dhiragu (1), Unit Peace (1), Etiya Buddy (1), reports / dashboards (1), Admin toolbox (1)

## distil-large-v3-tr-ov [ipucu=] [duzeltme=False] — örnekler
- beklenen: Device Upgrade akışını baştan anlatıyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve product detail sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca business interaction listesi geliyor, buradan Device Upgrade'i seçiyoruz.
  çıktı:    Devaz Üpredit akışını baştan unutuyorum. Siyasar 360 ekranında müşterinin Fis hattını buluyoruz ve ''Ve, ''Podak Detel sayfasını açıyoruz.'' Sağ üsteki menaj botonuna tıklayınca, Bizas İntemasyonu listesi geliyor. Buradan Devayse Apte seçiyoruz.
- beklenen: Açılan pop-up'ta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum, sistem bir sonraki adımda uygun device'ları listeliyor.
  çıktı:    Açılan popap'ta bu sefer Çenide Plan seçene ile ilerliyoruz. KALifikasyon APi müşteriye uygun 3 plan getiriyor. Ben en yüksek paketi seçiyorum ve nekte basıyorum. Sistem bir sonraki adımda uygun duvayaları listeliyor.
- beklenen: Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM, yani Resource Inventory Management tarafı stok bilgisini anlık getiriyor. Uygun bir device seçince Configurator, coverage ürünlerini shopping cart'a kendiliğinden ekliyor.
  çıktı:    Devay listesinde stokta olmayan cihazlar gri görünüyor. Burada Rim yani resoru menajmenajman tarafı stok bilgisine almak getiriyor. Uygun bir devay seçince konfigiratoru. Kavruç ürünleri şoping kartı kendiniden ekliyor.
- beklenen: Payment adımında müşteri on iki ay taksit istiyor. Ödeme koşullarını seçip Submit'e basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
  çıktı:    Payman adımında müşteri 12 aya taksit istiyor. Ödeme koşullarını seçip sapmete basıyoruz. Eğer bu adımda Bİ' tarafında bir hata alırsak ekren gözüle birlikte aran tıkıt açıp Rüt ekibine atıyoruz.
- beklenen: Şimdi Interaction Management tarafına geçiyoruz. Müşteri call center'ı aradığında CSR ekranında bir toaster çıkıyor ve sağdaki drawer'da yeni bir interaction filtreleme modunda açılıyor. Kayda tıklayınca detail moduna geçiyoruz.
  çıktı:    Şimdi İntereakşim Menajmut tarafına geçiyoruz. Müşterek Kol-Sentir aradığında, siyese rejanda bir tosteri bir toster çıkıyor. Ve sağdaki duruverde yeri bir İntirlerinin modunda açılıyor. Kayda tıklayınca Detel moduna geçiyoruz.
