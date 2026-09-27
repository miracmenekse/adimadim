#!/usr/bin/env python3
"""Birden çok OpenVINO Whisper modelini aynı ses setinde karşılaştırır, Markdown tablo yazar.

    karsilastir.py --ses <klasör> <model_klasörü>...   (klasörde *.wav + aynı adlı .txt)
    karsilastir.py --fleurs 100 <model_klasörü>...     (FLEURS tr test; önbelleğe iner, repoya girmez)

Cihaz ayar.json'dan gelir (ana makinede GPU). Tablo testler/sonuclar/ altına yazılır.
"""
import argparse
import csv
import datetime
import io
import random
import re
import tarfile
import time
import wave
from pathlib import Path

import stt_olc

adimadim = stt_olc.adimadim
SONUCLAR = stt_olc.REPO / "testler" / "sonuclar"
FLEURS = Path.home() / ".cache" / "adimadim" / "fleurs"


def fleurs_hazirla(adet: int) -> Path:
    """FLEURS tr_tr test bölümünden sabit tohumla `adet` kayıt seçer (CC BY 4.0)."""
    hedef = FLEURS / f"test_{adet}"
    if len(list(hedef.glob("*.wav"))) >= adet:
        return hedef
    from faster_whisper import decode_audio
    from huggingface_hub import hf_hub_download
    tsv = hf_hub_download("google/fleurs", "data/tr_tr/test.tsv", repo_type="dataset")
    tar = hf_hub_download("google/fleurs", "data/tr_tr/audio/test.tar.gz", repo_type="dataset")
    satirlar = list(csv.reader(open(tsv, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    metinler = {s[1]: s[2] for s in satirlar}  # dosya adı -> ham (noktalamalı) metin
    secilen = set(random.Random(42).sample(sorted(metinler), adet))
    hedef.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar) as t:
        for uye in t:
            ad = Path(uye.name).name
            if ad in secilen:  # FLEURS 32-bit float; araç 16 kHz mono 16-bit bekler
                ses = decode_audio(io.BytesIO(t.extractfile(uye).read()), sampling_rate=16000)
                with wave.open(str(hedef / ad), "wb") as w:
                    w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000)
                    w.writeframes((ses.clip(-1, 1) * 32767).astype("<i2").tobytes())
                (hedef / ad).with_suffix(".txt").write_text(metinler[ad], encoding="utf-8")
    (hedef / "kimlikler.txt").write_text("\n".join(sorted(secilen)) + "\n", encoding="utf-8")
    return hedef


def orto_kelimeler(metin: str) -> list:
    """Ortografik WER için: büyük/küçük harf ve noktalama korunur."""
    return re.findall(r"\w+|[^\w\s]", metin)


def sure(wav: Path) -> float:
    with wave.open(str(wav), "rb") as w:
        return w.getnframes() / w.getframerate()


def olc(model: Path, kayitlar: list, ayar: dict) -> dict:
    basla = time.time()
    cevir = adimadim.openvino_cevirici({**ayar, "ov_model": str(model)}, str(ayar.get("cihaz") or "CPU").upper())
    yukleme = time.time() - basla
    hata = kelime = o_hata = o_kelime = 0
    islem = ses = 0.0
    ornekler = []
    for wav in kayitlar:
        beklenen = wav.with_suffix(".txt").read_text(encoding="utf-8").strip()
        basla = time.time()
        cikti = cevir(wav)
        islem += time.time() - basla
        ses += sure(wav)
        r, h = stt_olc.kelimeler(beklenen), stt_olc.kelimeler(cikti)
        hata, kelime = hata + stt_olc.mesafe(r, h), kelime + len(r)
        r, h = orto_kelimeler(beklenen), orto_kelimeler(cikti)
        o_hata, o_kelime = o_hata + stt_olc.mesafe(r, h), o_kelime + len(r)
        if len(ornekler) < 3:
            ornekler.append((beklenen, cikti))
    return {"model": model.name, "wer": 100 * hata / max(1, kelime), "orto": 100 * o_hata / max(1, o_kelime),
            "rtf": islem / max(ses, 1e-9), "yukleme": yukleme, "ornekler": ornekler}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("modeller", nargs="+", type=lambda s: Path(s).expanduser())
    p.add_argument("--ses", type=Path)
    p.add_argument("--fleurs", type=int)
    a = p.parse_args()
    klasor = fleurs_hazirla(a.fleurs) if a.fleurs else a.ses
    kayitlar = sorted(w for w in klasor.glob("*.wav") if w.with_suffix(".txt").exists())
    ayar = adimadim.ayarlari_oku()
    cihaz = str(ayar.get("cihaz") or "CPU").upper()
    satirlar = [f"# Karşılaştırma — {klasor.name}, {len(kayitlar)} kayıt, {cihaz}", "",
                "| Model | WER (normalize) | Ortografik WER | RTF | Yükleme (sn) |", "|---|---|---|---|---|"]
    ekler = []
    for model in a.modeller:
        s = olc(model, kayitlar, ayar)
        print(f"{s['model']}: WER %{s['wer']:.1f} | orto %{s['orto']:.1f} | RTF {s['rtf']:.2f} | yükleme {s['yukleme']:.1f} sn",
              flush=True)
        satirlar.append(f"| {s['model']} | %{s['wer']:.1f} | %{s['orto']:.1f} | {s['rtf']:.2f} | {s['yukleme']:.1f} |")
        ekler += ["", f"## {s['model']} — örnekler"] + [f"- beklenen: {b}\n  çıktı:    {c}" for b, c in s["ornekler"]]
    SONUCLAR.mkdir(exist_ok=True)
    cikti = SONUCLAR / f"karsilastirma_{datetime.date.today()}_{klasor.name}_{cihaz}.md"
    cikti.write_text("\n".join(satirlar + ekler) + "\n", encoding="utf-8")
    print(f"\nTablo: {cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
