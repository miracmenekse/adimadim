# Karşılaştırma — paragraflar, 10 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov [ipucu=prompt] [duzeltme=True] | %90.9 (60/66) | %15.4 | %25.4 | 1.15 | 2.2 |
| distil-large-v3-tr-ov [ipucu=prompt] [duzeltme=True] | %0.0 (0/66) | %97.3 | %97.4 | 1.14 | 1.7 |
| whisper-small-tr-2-ov [ipucu=prompt] [duzeltme=True] | %63.6 (42/66) | %28.8 | %48.2 | 0.23 | 1.1 |

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — kaçan terimler
toaster (1), category (1), sub category (1), Add Note (1), heatmap & resource allocation (1), command (1)

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — örnekler
- beklenen: Device Upgrade akışını baştan anlatıyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve product detail sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca business interaction listesi geliyor, buradan Device Upgrade'i seçiyoruz.
  çıktı:    Device Upgrade akışını baştan unutuyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve Product Details sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca Business Interaction listesi geliyor. Buradan Device Upgrade'i seçiyoruz.
- beklenen: Açılan pop-up'ta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum, sistem bir sonraki adımda uygun device'ları listeliyor.
  çıktı:    Açılan pop-upta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun 3 plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum. Sistem bir sonraki adımda uygun device'leri listeliyor.
- beklenen: Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM, yani Resource Inventory Management tarafı stok bilgisini anlık getiriyor. Uygun bir device seçince Configurator, coverage ürünlerini shopping cart'a kendiliğinden ekliyor.
  çıktı:    Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM yani Resource Inventory Management tarafı stok bilgisini alınır getiriyor. Uygun bir device seçince Configurator, Coverage ürünleri shopping cart'a kendinden ekliyor.
- beklenen: Payment adımında müşteri on iki ay taksit istiyor. Ödeme koşullarını seçip Submit'e basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
  çıktı:    Payment adımında müşteri 12 ayat hakset istiyor, ödeme koşullarını seçip Submitte basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
- beklenen: Şimdi Interaction Management tarafına geçiyoruz. Müşteri call center'ı aradığında CSR ekranında bir toaster çıkıyor ve sağdaki drawer'da yeni bir interaction filtreleme modunda açılıyor. Kayda tıklayınca detail moduna geçiyoruz.
  çıktı:    Şimdi Interaction Management tarafına geçiyoruz. Müşterik Call Center aradığında, CSR ekranda bir toster çıkıyor. Sağdaki drawer da yeni bir interaction filtrinin modunda açılıyor. Kayda tıklayınca Detail moduna geçiyoruz.

## distil-large-v3-tr-ov [ipucu=prompt] [duzeltme=True] — kaçan terimler
BI (6), Manage (4), device (4), interaction (3), CSR (2), call center (2), detail modu (2), Add Note (2), Fizz (1), CSR 360 (1), product detail (1), business interaction (1), Device Upgrade (1), pop-up (1), Change the plan (1), Qualification API (1), Qualification (1), ek paket (1), RIM (1), shopping cart (1), RM ticket (1), Root ekibi (1), BI tarafında bir hata (1), Payment (1), Submit (1), toaster (1), drawer (1), category (1), sub category (1), reason (1), channel (1), Account Management (1), Save and Close (1), parent-child (1), Darwin (1), New BI geliştirmeleri (1), Obeya (1), heatmap & resource allocation (1), metrics (1), Windsurf (1), Hexagonal architecture (1), Low-code (1), command (1), playground (1), Dhiragu (1), Unit Peace (1), Etiya Buddy (1), reports / dashboards (1), Admin toolbox (1)

## distil-large-v3-tr-ov [ipucu=prompt] [duzeltme=True] — örnekler
- beklenen: Device Upgrade akışını baştan anlatıyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve product detail sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca business interaction listesi geliyor, buradan Device Upgrade'i seçiyoruz.
  çıktı:    I
- beklenen: Açılan pop-up'ta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum, sistem bir sonraki adımda uygun device'ları listeliyor.
  çıktı:    Açılan popap'ta, bu sefer
- beklenen: Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM, yani Resource Inventory Management tarafı stok bilgisini anlık getiriyor. Uygun bir device seçince Configurator, coverage ürünlerini shopping cart'a kendiliğinden ekliyor.
  çıktı:    I
- beklenen: Payment adımında müşteri on iki ay taksit istiyor. Ödeme koşullarını seçip Submit'e basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
  çıktı:    P, I is
- beklenen: Şimdi Interaction Management tarafına geçiyoruz. Müşteri call center'ı aradığında CSR ekranında bir toaster çıkıyor ve sağdaki drawer'da yeni bir interaction filtreleme modunda açılıyor. Kayda tıklayınca detail moduna geçiyoruz.
  çıktı:    Şimdi

## whisper-small-tr-2-ov [ipucu=prompt] [duzeltme=True] — kaçan terimler
device (2), Add Note (2), CSR 360 (1), product detail (1), Manage (1), CSR (1), shopping cart (1), Submit (1), category (1), sub category (1), reason (1), channel (1), interaction (1), Save and Close (1), Darwin (1), Obeya (1), heatmap & resource allocation (1), metrics (1), command (1), Dhiragu (1), Etiya Buddy (1), reports / dashboards (1)

## whisper-small-tr-2-ov [ipucu=prompt] [duzeltme=True] — örnekler
- beklenen: Device Upgrade akışını baştan anlatıyorum. CSR 360 ekranında müşterinin Fizz hattını buluyoruz ve product detail sayfasını açıyoruz. Sağ üstteki Manage butonuna tıklayınca business interaction listesi geliyor, buradan Device Upgrade'i seçiyoruz.
  çıktı:    device upgrade akışını baştan unutuyorum siyasal 360 ekranda üşüterinin fizz attığını buluyoruz ve prodakti tele sayfasına açıyoruz sağ üsteki manaj butonuna tıklayınca business interaction listesi geliyor buradan device upgradei seçiyoruz
- beklenen: Açılan pop-up'ta bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor. Ben en yüksek paketi seçiyorum ve Next'e basıyorum, sistem bir sonraki adımda uygun device'ları listeliyor.
  çıktı:    Açılan pop-up da bu sefer Change the plan seçeneğiyle ilerliyoruz. Qualification API müşteriye uygun üç plan getiriyor ben en yüksek paketi seçiyorum ve nexte basıyorum sistem bir sonraki adımda uygun devaisleri listeliyoruz
- beklenen: Device listesinde stokta olmayan cihazlar gri görünüyor. Burada RIM, yani Resource Inventory Management tarafı stok bilgisini anlık getiriyor. Uygun bir device seçince Configurator, coverage ürünlerini shopping cart'a kendiliğinden ekliyor.
  çıktı:    divay siscesinde stokta olmayan cihazlar gri görünüyor burada rim yani resource inventory management tarafı stok bilgisini almak getiriyor uygun bir divay seçince configurator covrux ürünleri şopin karta kendilerine ekliyor
- beklenen: Payment adımında müşteri on iki ay taksit istiyor. Ödeme koşullarını seçip Submit'e basıyoruz. Eğer bu adımda BI tarafında bir hata alırsak ekran görüntüsüyle birlikte RM ticket açıp Root ekibine atıyoruz.
  çıktı:    Payment adımda müşteri on iki aya taksit istiyor ödeme koşullarını seçip sapmete basıyoruz eğer bu adımda BI tarafında bir hata alırsak ekran göndese birlikte RM Ticket açıp Root ekibine atıyoruz
- beklenen: Şimdi Interaction Management tarafına geçiyoruz. Müşteri call center'ı aradığında CSR ekranında bir toaster çıkıyor ve sağdaki drawer'da yeni bir interaction filtreleme modunda açılıyor. Kayda tıklayınca detail moduna geçiyoruz.
  çıktı:    şimdi interaction management tarafına geçiyoruz müşterik call center aradığımda CSR adında bir toaster çıkıyor ve sağdaki drawerda yeri bir interaction tiltelerimin modunda açılıyor kaydettiklayınca detail moduna geçiyoruz
