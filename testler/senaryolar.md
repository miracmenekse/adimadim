# Test senaryoları (okuma metinleri)

İki iş akışı ve her akış için iki okuma senaryosu. Her numaralı cümle ayrı bir kayıttır
(`araclar/kayit_al.sh` bunları `testler/cumleler.txt`'ten sırayla okutur). Cümlelere
`terim_sozlugu_ham_→_normalize.md`'deki terimler normalize biçimleriyle yedirildi; beklenen metin
normalize yazımdır.

## Akış 1 — Device Upgrade

1. CSR, CSR 360 ekranında müşterinin product listesinden ilgili product'a tıklar; product detail sayfası açılır.
2. Manage butonuna basar; business interaction (BI) listesi açılır.
3. Listeden Device Upgrade'i seçer; iki seçenekli bir pop-up açılır: "Change the plan" ve "Continue without plan change".
4. a) Change the plan: Qualification API Device Upgrade'e uygun planları getirir, CSR planı seçip ilerler.
   b) Continue without plan change: plan seçim adımı atlanır.
5. Qualification, seçilen plan (ya da mevcut plan) ve müşterinin mevcut device'ına göre yeniden çalışır; uygun device'lar listelenir, CSR bir device seçer.
6. CSR payment yöntemini ve ödeme koşullarını seçer, Submit'e basar; süreç biter.

### Senaryo 1A — plan değişikliğiyle

1. Şimdi CSR 360 ekranında müşterinin Freedom faturalı hattına ait product'a tıklıyoruz, product detail sayfası açılıyor.
2. Burada sağ üstteki Manage butonuna basıyoruz ve BI listesi geliyor.
3. Listeden Device Upgrade'i seçiyoruz, karşımıza iki seçenekli bir pop-up çıkıyor.
4. Change the plan seçeneğini seçip ilerliyoruz, Qualification API uygun planları getiriyor.
5. Müşteriye uygun olan Fizz tarifesini seçiyoruz ve Next'e basıyoruz.
6. Qualification bu kez seçilen plana ve müşterinin mevcut device'ına göre çalışıyor, uygun device'lar listeleniyor.
7. Device'ı seçince Configurator aksesuar ve coverage ürünlerini shopping cart'a otomatik ekliyor.
8. Payment adımında taksitli ödemeyi ve ödeme koşullarını seçip Submit'e basıyoruz, süreç tamamlanıyor.

### Senaryo 1B — plan değişikliği olmadan

1. CSR sayfasında müşterinin Darwin ön ödemeli hattını açıp product detail ekranına geçiyoruz.
2. Manage butonuna tıklıyoruz, business interaction'lar listeleniyor ve Device Upgrade'i seçiyoruz.
3. Açılan pop-up'ta Continue without plan change diyoruz, plan seçim adımı atlanıyor.
4. Qualification müşterinin mevcut planına ve device'ına göre çalışıyor, sadece uygun device'lar geliyor.
5. Burada Number/SIM card için shopping cart üzerinde eksik kontrol var, bunu RM ticket olarak açıyoruz.
6. Device'ı seçtikten sonra RIM stok bilgisini kontrol ediyor, Resource Inventory Management tarafında cihaz rezerve ediliyor.
7. Peşin ödemeyi seçip Submit'e basıyoruz; BI tarafında bir hata çıkarsa Root ekibine iletiyoruz.

## Akış 2 — Interaction Management

1. Müşteri call center'ı arar ve bir CSR'a bağlanır.
2. CSR müşterinin ekranını (CSR 360) açar; bir toaster çıkar.
3. Toaster'dan sonra otomatik olarak bir interaction başlar; sağdaki drawer'da filtreleme modunda açılır.
4. CSR açık olan yeni kayda tıklar; kayıt detail modunda açılır.
5. CSR category, sub category, reason ve channel bilgilerini girer; sistem Add Note butonunu aktifleştirir.
6. CSR Add Note'a basar, notunu girer ve kaydeder.
7. CSR Save and Close ile interaction'ı kapatır; sistem ana interaction ile notları parent-child olarak bağlar.

### Senaryo 2A — fatura itirazı

1. Müşteri call center'ı arıyor ve bir CSR'a bağlanıyor.
2. CSR müşterinin CSR 360 ekranına giriyor, ekranda bir toaster çıkıyor.
3. Toaster'dan sonra otomatik olarak bir interaction başlıyor ve sağdaki drawer'da filtreleme modunda açılıyor.
4. Açık olan yeni kayda tıklıyoruz, kayıt detail modunda açılıyor.
5. Category olarak Fatura, sub category olarak Fatura İtirazı, reason olarak Yanlış Ücretlendirme, channel olarak Call Center seçiyoruz.
6. Sistem Add Note butonunu aktifleştiriyor; Add Note'a basıp müşterinin itirazını not olarak yazıyoruz.
7. Save and Close ile interaction'ı kapatıyoruz, sistem ana interaction ile notu parent-child olarak bağlıyor.

### Senaryo 2B — Account Management ve hata kaydı

1. Dhiragu müşterisi call center'ı arıyor, CSR çağrıyı alıp CSR sayfasını açıyor.
2. Toaster görünüyor ve interaction drawer'da filtreleme modunda kendiliğinden açılıyor.
3. Yeni kaydı detail modunda açıp category olarak Account Management'ı seçiyoruz.
4. Sub category, reason ve channel alanlarını doldurunca Add Note aktif oluyor.
5. Notta, ECA modülündeki adres değişikliği command'ının çalışmadığını yazıyoruz.
6. Bu hata New BI geliştirmeleri kapsamında, Etiya Buddy üzerinden RM ticket açılıyor.
7. Save and Close ile kapattığımızda notlar ana interaction'a child olarak bağlanıyor ve Unit Peace dashboard'unda görünüyor.
