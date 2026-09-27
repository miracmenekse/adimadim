# Karşılaştırma — test_100, 100 kayıt, CPU

| Model | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |
|---|---|---|---|---|
| whisper-medium-ov | %12.5 | %19.1 | 0.59 | 1.9 |
| distil-large-v3-tr-ov | %17.5 | %24.1 | 0.78 | 1.1 |
| whisper-small-tr-2-ov | %25.8 | %42.7 | 0.15 | 1.0 |

## whisper-medium-ov — örnekler
- beklenen: Apia, Samoa'nın başkentidir. Şehir Upolu adasındadır ve 40.000'in biraz altında bir nüfusa sahiptir.
  çıktı:    Apia, Samoan'ın başkaldidir. Şehir Upol Adası'ndadır ve 40.000'in biraz altında bir nüfusa sahiptir.
- beklenen: Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
  çıktı:    Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
- beklenen: Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.
  çıktı:    Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.

## distil-large-v3-tr-ov — örnekler
- beklenen: Apia, Samoa'nın başkentidir. Şehir Upolu adasındadır ve 40.000'in biraz altında bir nüfusa sahiptir.
  çıktı:    Apia, Samuva'nın başkendidir. Şiir, Upol adasındadır ve 40 binin biraz altında bir nüfusa sahiptir.
- beklenen: Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
  çıktı:    Sonrasında fotoğrafçular tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
- beklenen: Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.
  çıktı:    Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlenci ikramları olur.

## whisper-small-tr-2-ov — örnekler
- beklenen: Apia, Samoa'nın başkentidir. Şehir Upolu adasındadır ve 40.000'in biraz altında bir nüfusa sahiptir.
  çıktı:    apia samovanın başkendidir şiir upol adasındadır ve kırk binin biraz altında bir nüfosa sahiptir
- beklenen: Sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti. Mendoza vuruldu.
  çıktı:    sonrasında fotoğrafçılar tuvalete gitmesi gereken yaşlı bir kadının yerine geçti mendoza uğruldu
- beklenen: Misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek, içecek ve eğlence ikramları olur.
  çıktı:    misafirleri iyi bir ruh halinde tutmak ve hoşnut etmek için genellikle özel olarak hazırlanan yiyecek içecek ve eğlence ikramları olur
