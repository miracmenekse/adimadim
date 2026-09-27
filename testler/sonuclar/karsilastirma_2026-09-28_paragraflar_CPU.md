# Karşılaştırma — paragraflar, 10 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov | %93.9 (62/66) | %15.8 | %25.7 | 0.56 | 1.2 |

## whisper-medium-ov — kaçan terimler
category (1), sub category (1), Add Note (1), heatmap & resource allocation (1)

## whisper-medium-ov — örnekler
- beklenen: Device Upgrade akışını baştan anlatıyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve product detail sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca business interaction listesi geliyor, buradan Device Upgrade'i seçiyoruz.
  çıktı:    Device Upgrade akışını baştan unutuyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve Product Details sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca Business Interaction listesi geliyor. Buradan Device Upgrade'i seçiyoruz.
- beklenen: Açılan pop-up'ta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum, sistem bir sonraki adımda uygun device'ları listeliyor.
  çıktı:    Açılan pop-upta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun 3 plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum. Sistem bir sonraki adımda uygun device'leri listeliyor.
- beklenen: Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM, yani Resource Inventory Management tarafı stok bilgisini anlık getiriyor. Uygun bir device seçince Configurator, coverage ürünlerini shopping cart'a kendiliğinden ekliyor.
  çıktı:    Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM yani Resource Inventory Management tarafı stok bilgisini alınır getiriyor. Uygun bir device seçince Configurator, Coverage ürünleri shopping cart'a kendinden ekliyor.
- beklenen: Payment adımında müşteri on iki ay taksit istiyor. Ödeme koşullarını seçip Submit'e basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
  çıktı:    Payment adımında müşteri 12 ayat hakset istiyor. Ödeme koşullarını seçip Submitte basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran göndersizleri birlikte RM ticket açıp Root ekibine atıyoruz.
- beklenen: Şimdi Interaction Management tarafına geçiyoruz. Müşteri call center'ı aradığında CSR ekranında bir toaster çıkıyor ve sağdaki drawer'da yeni bir interaction filtreleme modunda açılıyor. Kayda tıklayınca detail moduna geçiyoruz.
  çıktı:    Şimdi Interaction Management tarafına geçiyoruz. Müşteri Call Center aradığında CSR ekranda bir toaster çıkıyor. Sağdaki drawer da yeni bir Interaction Filter Modu'nda açılıyor. Kayda tıklayınca Detail Modu'na geçiyoruz.
