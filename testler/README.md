# Test kayıtları (testler/ses/)

Konuşma tanıma doğruluğunu ölçmek için örnek kayıtlar. Her kayıt iki dosyadan oluşur:

    testler/ses/01.wav   16 kHz mono ses
    testler/ses/01.txt   o kayıtta tam olarak ne söylendiği (tek satır)

## Kayıt nasıl alınır

Kayıtları ANA MAKİNEDE, dokümanı hazırlarken kullandığın mikrofonla al; asıl sorun mikrofon
ve ortam koşulları olduğu için VM'deki mikrofon yanıltıcı olur.

    cd <repo>
    arecord -f S16_LE -r 16000 -c 1 testler/ses/01.wav      # konuş, bitince Ctrl+C
    echo "Müşterinin fatura döngüsünü ayın on beşine çekiyoruz." > testler/ses/01.txt

Sonra commit'leyip push'la; VM'deki Claude Code aynı kayıtlarla ölçüm yapar.

## Kurallar

- Cümleler UYDURMA ve GENEL olsun: gerçek müşteri, numara, şirkete özel bilgi yok.
- Doğal konuş: dokümanı anlatırken nasıl konuşuyorsan öyle (hız, "şimdi", "burada" vb.).
- Terimleri bol kullan: terimler.txt'deki kelimeler en çok hata yapılan yerler.
- 10-20 kayıt, her biri 5-20 saniye, ölçüm için yeterli.

## Ölçüm

    ./test.sh                      # hepsi
    ~/.local/share/adimadim/venv/bin/python testler/stt_olc.py   # yalnızca doğruluk
