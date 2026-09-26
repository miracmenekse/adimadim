#!/usr/bin/env python3
"""Konuşma tanıma doğruluk ölçümü (gerçek model, bu makinenin ayar.json'u ile).

testler/ses/*.wav dosyalarını çevirir ve aynı adlı .txt'deki beklenen metinle karşılaştırır:
  - WER: kelime hata oranı (düşük = iyi)
  - Terim isabeti: terimler.txt (+ varsa ~/.config/adimadim/terimler.local.txt) içindeki
    terimlerden beklenen metinde geçenlerin kaçı çıktıda da doğru yazılmış
Her iyileştirmeden önce ve sonra çalıştır; sonucu CHANGELOG'a yaz.
"""
import importlib.util
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SES = REPO / "testler" / "ses"

_spec = importlib.util.spec_from_file_location("adimadim", REPO / "adimadim.py")
adimadim = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adimadim)


def kucult(metin: str) -> str:
    """Karşılaştırma için sadeleştirir. ı/i ayrımı yok sayılır: "SIM", "sim" ve "sım" aynı sayılsın."""
    return metin.replace("İ", "i").lower().replace("ı", "i")


def kelimeler(metin: str) -> list:
    return re.findall(r"[0-9a-zçğıöşüâîû]+", kucult(metin))


def mesafe(a: list, b: list) -> int:
    """Kelime düzeyinde Levenshtein uzaklığı."""
    onceki = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        simdiki = [i]
        for j, y in enumerate(b, 1):
            simdiki.append(min(onceki[j] + 1, simdiki[j - 1] + 1, onceki[j - 1] + (x != y)))
        onceki = simdiki
    return onceki[-1]


def terimleri_oku() -> list:
    dosyalar = [REPO / "terimler.txt", adimadim.AYAR_DIZINI / "terimler.local.txt"]
    terimler = []
    for dosya in dosyalar:
        if dosya.exists():
            for satir in dosya.read_text(encoding="utf-8").splitlines():
                satir = satir.split("#", 1)[0].strip()
                if satir:
                    terimler.append(satir)
    return terimler


def gecer(terim: str, metin: str) -> bool:
    """Terim metinde geçiyor mu? Türkçe ekler serbest: "fatura döngüsü" ~ "fatura döngüsünü"."""
    t, m = kelimeler(terim), kelimeler(metin)
    return bool(t) and any(all(m[i + k].startswith(t[k]) for k in range(len(t)))
                           for i in range(len(m) - len(t) + 1))


def main() -> int:
    kayitlar = sorted(SES.glob("*.wav"))
    if not kayitlar:
        print("testler/ses/ içinde kayıt yok.")
        return 0
    ayar = adimadim.ayarlari_oku()
    ad, cevir = adimadim.cevirici_olustur(ayar)
    terimler = terimleri_oku()
    print(f"Motor: {ad} | model: {ayar.get('ov_model') if 'OpenVINO' in ad else ayar.get('whisper_modeli')}")
    toplam_hata = toplam_kelime = terim_sayisi = terim_dogru = 0
    toplam_sure = 0.0
    for wav in kayitlar:
        txt = wav.with_suffix(".txt")
        if not txt.exists():
            print(f"- {wav.name}: beklenen metin ({txt.name}) yok, atlandı")
            continue
        beklenen = txt.read_text(encoding="utf-8").strip()
        basla = time.time()
        cikti = cevir(wav)
        sure = time.time() - basla
        ref, hip = kelimeler(beklenen), kelimeler(cikti)
        hata = mesafe(ref, hip)
        gecenler = [t for t in terimler if gecer(t, beklenen)]
        kacanlar = [t for t in gecenler if not gecer(t, cikti)]
        toplam_hata += hata
        toplam_kelime += len(ref)
        terim_sayisi += len(gecenler)
        terim_dogru += len(gecenler) - len(kacanlar)
        toplam_sure += sure
        print(f"\n{wav.name}: WER %{100 * hata / max(1, len(ref)):.0f} | {sure:.1f} sn")
        print(f"  beklenen: {beklenen}")
        print(f"  çıktı:    {cikti}")
        if kacanlar:
            print(f"  kaçan terimler: {', '.join(kacanlar)}")
    if toplam_kelime:
        print(f"\nTOPLAM  WER %{100 * toplam_hata / toplam_kelime:.1f}"
              f" | terim isabeti {terim_dogru}/{terim_sayisi}"
              f" | süre {toplam_sure:.1f} sn ({ad})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
