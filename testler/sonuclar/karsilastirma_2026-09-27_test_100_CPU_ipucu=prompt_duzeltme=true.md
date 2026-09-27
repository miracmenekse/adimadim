# Karşılaştırma — test_100, 100 kayıt, CPU

| Model | Terim isabeti | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|---|
| whisper-medium-ov [ipucu=prompt] [duzeltme=True] | %96.9 (63/65) | %12.0 | %18.5 | 0.79 | 3.0 |

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — kaçan terimler
BI (2)

## whisper-medium-ov [ipucu=prompt] [duzeltme=True] — örnekler
- beklenen: Apia, Samoa'nın başkentidir. Şehir Upolu adasındadır ve 40.000'in biraz altında bir nüfusa sahiptir.
  çıktı:    Apia, Samoa'nın başkentidir. Şehir, Upol adasındadır ve 40.000'in biraz altında bir nüfusa sahiptir.
- beklenen: Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
  çıktı:    Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
- beklenen: Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.
  çıktı:    Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.
- beklenen: Moldova'nın başkenti Kişinev'dir. Ülkenin yerel dili Rumencedir, fakat yaygın olarak Rusça kullanılmaktadır.
  çıktı:    Moldova'nın başkenti Kişinevdir. Ülkenin yerel dili Rumancadır fakat yaygın olarak Rusça kullanılmaktadır.
- beklenen: Gianarlo Fisichella arabasının kontrolünü kaybetti ve starttan çok kısa bir süre sonra yarışı bitirdi.
  çıktı:    Gianarlo Fisicella arabasının kontrolünü kaybetti ve starttan çok kısa bir süre sonra yarışı bitirdi.
