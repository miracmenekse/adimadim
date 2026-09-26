#!/usr/bin/env python3
"""kur.sh yardımcısı: ~/.config/adimadim/ayar.json'u oluşturur ya da eksik anahtarlarını tamamlar.

Mevcut değerlere dokunmaz (kullanıcının elle yaptığı ayarlar korunur).
'cihaz' boşsa OpenVINO'nun gördüğü cihazlara bakar: GPU varsa GPU, yoksa CPU.
NPU'yu kendiliğinden seçmez; yalnızca varsa haber verir.
Kullanım: ayar_kur.py <ayar.ornek.json> <hedef ayar.json>
"""
import json
import sys
from pathlib import Path


def cihazlari_bul() -> list:
    try:
        import openvino as ov
        return list(ov.Core().available_devices)
    except Exception as hata:  # OpenVINO kurulu değil ya da sürücü sorunu
        print(f"  OpenVINO cihazları okunamadı ({hata}).")
        return []


def main() -> int:
    ornek, hedef = Path(sys.argv[1]), Path(sys.argv[2])
    varsayilan = json.loads(ornek.read_text(encoding="utf-8"))
    ayar = {}
    if hedef.exists():
        try:
            ayar = json.loads(hedef.read_text(encoding="utf-8"))
        except ValueError as hata:
            print(f"  {hedef} bozuk JSON ({hata}). Düzelt ya da sil, sonra kur.sh'yi tekrar çalıştır.")
            return 1
    degisen = [k for k in varsayilan if k not in ayar]
    for anahtar in degisen:
        ayar[anahtar] = varsayilan[anahtar]

    cihazlar = cihazlari_bul()
    print(f"  OpenVINO'nun gördüğü cihazlar: {', '.join(cihazlar) or '-'}")
    if not ayar.get("cihaz"):
        ayar["cihaz"] = "GPU" if any(c.startswith("GPU") for c in cihazlar) else "CPU"
        degisen.append(f"cihaz={ayar['cihaz']}")
    print(f"  Kullanılacak cihaz: {ayar['cihaz']}")
    if "NPU" in cihazlar and ayar["cihaz"] != "NPU":
        print('  Not: NPU da var; denemek için ayar.json\'da "cihaz": "NPU" yapabilirsin.')

    if degisen or not hedef.exists():
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(json.dumps(ayar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  Eklenen/ayarlanan: {', '.join(degisen) or '-'}")
    else:
        print("  Ayar dosyası güncel; değişiklik yapılmadı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
