#!/usr/bin/env python3
"""Uçtan uca duman testi: gerçek ekran, mikrofon ve model OLMADAN aracın bütün akışını dener.

Sahte gnome-screenshot, zenity, arecord, gsettings, notify-send, xdg-open ve sahte
openvino_genai / faster_whisper modülleri kullanır. Geçici bir HOME'da çalışır; gerçek
ayarlarına, dokümanlarına ve kısayollarına dokunmaz. Yeni özellik = buraya yeni kontrol.
"""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARAC = REPO / "adimadim.py"
PY = sys.executable
BASARISIZ = []

# ------------------------------------------------------------------ sahte araçlar

SAHTE_ARACLAR = {
    "gnome-screenshot": r'''
import os, struct, sys, zlib
a = sys.argv[1:]
cikti = a[a.index("-f") + 1]
g, y = (800, 450) if "-w" in a else (960, 540)
satir = b"\x00" + bytes([40, 90, 160]) * g
def parca(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
png = (b"\x89PNG\r\n\x1a\n" + parca(b"IHDR", struct.pack(">IIBBBBB", g, y, 8, 2, 0, 0, 0))
       + parca(b"IDAT", zlib.compress(satir * y)) + parca(b"IEND", b""))
open(cikti, "wb").write(png)
open(os.environ["SAHTE_LOG"], "a").write("ekran " + " ".join(a) + "\n")
''',
    "zenity": r'''
import os, sys
girdi = sys.stdin.read()
open(os.environ["SAHTE_LOG"], "a").write("zenity " + " | ".join(sys.argv[1:]) + " | girdi=" + repr(girdi) + "\n")
rc = int(os.environ.get("ZENITY_RC", "0"))
if rc == 0:
    sys.stdout.write(os.environ.get("ZENITY_METIN", "") + "\n")
sys.exit(rc)
''',
    "notify-send": r'''
import os, sys
open(os.environ["SAHTE_LOG"], "a").write("bildirim " + " ".join(sys.argv[1:]) + "\n")
''',
    "xdg-open": r'''
import os, sys
open(os.environ["SAHTE_LOG"], "a").write("xdg-open " + " ".join(sys.argv[1:]) + "\n")
''',
    "xdg-user-dir": r'''
import os
print(os.path.join(os.environ["HOME"], "Belgeler"))
''',
    # SIGINT gelene kadar bekler, sonra 1 sn'lik sessiz OLMAYAN bir WAV yazar
    "arecord": r'''
import array, os, signal, struct, sys, time
yol = sys.argv[-1]
open(os.environ["SAHTE_LOG"], "a").write(f"kayit-basla {yol}\n")
def dur(*_):
    ornekler = array.array("h", [(8000 if (i // 20) % 2 else -8000) for i in range(16000)])
    veri = ornekler.tobytes()
    with open(yol, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(veri)) + b"WAVEfmt "
                + struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16)
                + b"data" + struct.pack("<I", len(veri)) + veri)
    open(os.environ["SAHTE_LOG"], "a").write(f"kayit-dur {yol}\n")
    sys.exit(0)
signal.signal(signal.SIGINT, dur)
signal.signal(signal.SIGTERM, dur)
while True:
    time.sleep(0.05)
''',
    "gsettings": r'''
import json, os, sys
yol = os.environ["SAHTE_GSETTINGS"]
depo = json.load(open(yol)) if os.path.exists(yol) else {}
komut, sema, anahtar = sys.argv[1:4]
k = sema + "::" + anahtar
if komut == "get":
    print(depo.get(k, "@as []" if anahtar == "custom-keybindings" else "''"))
elif komut == "set":
    depo[k] = sys.argv[4]
    json.dump(depo, open(yol, "w"), ensure_ascii=False, indent=1)
''',
}

SAHTE_MODULLER = {
    "openvino_genai/__init__.py": r'''
class _Parca:
    def __init__(self, bas, son, metin):
        self.start_ts, self.end_ts, self.text = bas, son, metin
class _Sonuc:
    def __init__(self, parcalar):
        self.chunks = parcalar
class WhisperPipeline:
    def __init__(self, model, cihaz):
        self.cihaz = cihaz
    def generate(self, ses, **ayar):  # sesin her saniyesi için bir parça: adımlara dağıtım sınanır
        ipucu = " ipuçlu" if ayar.get("initial_prompt", "").startswith("Anlatımda geçen terimler:") else ""
        return _Sonuc([_Parca(float(i), i + 1.0, f"sahte çeviri {self.cihaz} {ayar.get('language')} {i}. sn interaksiyonu{ipucu}")
                       for i in range(max(1, len(ses) // 16000))])
''',
    "faster_whisper/__init__.py": r'''
class _Parca:
    def __init__(self, bas, son, metin):
        self.start, self.end, self.text = bas, son, metin
class WhisperModel:
    def __init__(self, *a, **k):
        pass
    def transcribe(self, ses, **k):
        return iter([_Parca(0.0, 0.5, " sahte yedek"), _Parca(0.5, 1.0, " çeviri ")]), None
''',
}


# ------------------------------------------------------------------ yardımcılar

def kontrol(kosul: bool, aciklama: str) -> None:
    print(("  ✓ " if kosul else "  ✗ ") + aciklama)
    if not kosul:
        BASARISIZ.append(aciklama)


def ortam_kur(kok: Path) -> dict:
    sahte_bin, sahte_py = kok / "bin", kok / "py"
    for ad, kod in SAHTE_ARACLAR.items():
        dosya = sahte_bin / ad
        dosya.parent.mkdir(parents=True, exist_ok=True)
        dosya.write_text(f"#!{PY}\n{kod}", encoding="utf-8")
        dosya.chmod(0o755)
    for ad, kod in SAHTE_MODULLER.items():
        dosya = sahte_py / ad
        dosya.parent.mkdir(parents=True, exist_ok=True)
        dosya.write_text(kod, encoding="utf-8")
    model = kok / "model"
    model.mkdir()
    (model / "openvino_encoder_model.xml").write_text("<sahte/>")
    ayar_dizini = kok / "home" / ".config" / "adimadim"
    ayar_dizini.mkdir(parents=True)
    (ayar_dizini / "ayar.json").write_text(json.dumps({
        "klasor": str(kok / "dokumanlar"), "stt": "openvino", "cihaz": "CPU", "ov_model": str(model),
    }), encoding="utf-8")
    env = dict(os.environ)
    env.update({
        "HOME": str(kok / "home"), "XDG_CONFIG_HOME": str(kok / "home" / ".config"),
        "PATH": f"{sahte_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "PYTHONPATH": str(sahte_py), "XDG_SESSION_TYPE": "wayland",
        "SAHTE_LOG": str(kok / "log.txt"), "SAHTE_GSETTINGS": str(kok / "gsettings.json"),
    })
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    return env


def calistir(env: dict, *arglar: str, beklenen: int = 0, cwd=None, **ek) -> subprocess.CompletedProcess:
    r = subprocess.run([PY, str(ARAC), *arglar], env={**env, **ek}, capture_output=True,
                       text=True, timeout=120, cwd=cwd)
    if r.returncode != beklenen:
        print(f"    komut: adimadim {' '.join(arglar)} → çıkış {r.returncode} (beklenen {beklenen})")
        print("    " + (r.stdout + r.stderr).strip().replace("\n", "\n    "))
    return r


def son_oturum(env: dict) -> Path:
    return Path((Path(env["XDG_CONFIG_HOME"]) / "adimadim" / "son").read_text(encoding="utf-8").strip())


def kayitcilari_temizle(kok: Path) -> None:
    for pid_dizini in Path("/proc").iterdir():
        if pid_dizini.name.isdigit():
            try:
                komut = (pid_dizini / "cmdline").read_bytes()
            except OSError:
                continue
            if str(kok).encode() in komut and b"arecord" in komut:
                os.kill(int(pid_dizini.name), signal.SIGKILL)


# ------------------------------------------------------------------ senaryolar

def yazili_akis(env: dict) -> None:
    print("Yazılı notlarla akış")
    kontrol(calistir(env, "cek", beklenen=1).returncode == 1, "açık doküman yokken 'cek' reddediliyor")
    kontrol(calistir(env, "basla", "Fatura / İptal: #2 akışı").returncode == 0, "basla")
    kontrol(calistir(env, "basla", "İkinci", beklenen=1).returncode == 1, "ikinci 'basla' reddediliyor")
    calistir(env, "cek", ZENITY_METIN="Müşteri numarası girilir.\nAra'ya basılır.")
    calistir(env, "cek", ZENITY_RC="1")
    calistir(env, "not", ZENITY_METIN="İptal nedeni seçilir.")
    calistir(env, "cek", ZENITY_METIN="yanlış çekim")
    calistir(env, "geri")
    kontrol("2 adım" in calistir(env, "durum").stdout, "durum 2 adım gösteriyor")
    calistir(env, "bitir")
    oturum = son_oturum(env)
    md = oturum / "Fatura İptal 2 akışı.md"
    kontrol(md.exists(), "özel karakterli başlıktan güvenli dosya adı")
    metin = md.read_text(encoding="utf-8") if md.exists() else ""
    kontrol("Müşteri numarası girilir.\nAra'ya basılır." in metin, "çok satırlı not korunuyor")
    kontrol("İptal nedeni seçilir." in metin, "'not' ile düzenleme")
    kontrol("### Adım 3" not in metin and not (oturum / "gorseller/adim-03.png").exists(), "'geri' son adımı siliyor")
    kontrol("- **Amaç:** …" in metin, "kullanım senaryosu iskeleti")
    if subprocess.run(["which", "pandoc"], capture_output=True).returncode == 0:
        kontrol(md.with_suffix(".docx").exists(), "Word çıktısı")
    else:
        print("  - pandoc yok, Word kontrolü atlandı")


def sesli_akis(env: dict) -> None:
    print("Sesli anlatımla akış")
    kontrol(calistir(env, "basla", "Paket Değişikliği", "--ses").returncode == 0, "basla --ses")
    calistir(env, "cek")
    time.sleep(0.3)
    calistir(env, "cek")
    time.sleep(0.3)
    kontrol("kayıt sürüyor" in calistir(env, "durum").stdout, "kayıt sürüyor görünüyor")
    calistir(env, "geri")
    calistir(env, "cek")
    time.sleep(0.3)
    r = calistir(env, "bitir")
    oturum = son_oturum(env)
    metin = (oturum / "Paket Değişikliği.md").read_text(encoding="utf-8")
    kontrol(metin.count("sahte çeviri CPU <|tr|>") == 2, "iki adım OpenVINO (CPU) ile çevrildi")
    kontrol("OpenVINO / CPU" in r.stdout, "kullanılan motor çıktıda yazıyor")
    kontrol(sorted(p.name for p in (oturum / "ses").iterdir()) == ["adim-01.wav", "adim-02.wav"],
            "ses dosyaları doğru (silinen adımın kaydı yok)")
    r = calistir(env, "yeniden")
    kontrol(r.returncode == 0 and (oturum / "Paket Değişikliği.md.yedek").exists(), "yeniden: yedek alıp tekrar çevirdi")
    r = calistir(env, "cevir", str(oturum / "ses" / "adim-01.wav"))
    kontrol("sahte çeviri CPU" in r.stdout, "cevir komutu")
    md = oturum / "Paket Değişikliği.md"  # Rovo'nun işlenmiş çıktısı kopyalanmış gibi: bağlantı ve ### yok
    md.write_text("Paket Değişikliği\n\nAna akış\nAdım 1\nPreview unavailable\nKullanıcı tıklar.\n"
                  "Adım 2\nPreview unavailable\nSistem gösterir.\n", encoding="utf-8")
    calistir(env, "word", str(oturum))
    metin = md.read_text(encoding="utf-8")
    kontrol("### Adım 2\n\n![Adım 2](gorseller/adim-02.png)" in metin and "Preview unavailable" not in metin,
            "word: kopyalanan Rovo çıktısına görseller geri konuyor")


def har_girdisi(zaman: str, metot: str, url: str, yanit: str = "{}", tur: str = "application/json",
                istek: str | None = None, durum: int = 200) -> dict:
    """Firefox 157'nin HAR 1.2 girdisi biçiminde (başlıkta gizli jeton var: dokümana girmemeli)."""
    g = {"startedDateTime": zaman,
         "request": {"method": metot, "url": url, "httpVersion": "HTTP/2", "cookies": [], "queryString": [],
                     "headers": [{"name": "Authorization", "value": "Bearer GIZLI-JETON"},
                                 {"name": "Cookie", "value": "oturum=GIZLI-CEREZ"}]},
         "response": {"status": durum, "statusText": "", "headers": [], "cookies": [],
                      "content": {"mimeType": tur, "size": len(yanit), "text": yanit}}}
    if istek is not None:
        g["request"]["postData"] = {"mimeType": "application/json", "params": [], "text": istek}
    return g


def akis_girdisi(zaman: str, mevcut: str, degisim: bool, sonraki: str) -> dict:
    """İş akışı çağrısı: istekte mevcut durum + değişim bayrağı, yanıtta sonraki durum (uydurma kodlar)."""
    return har_girdisi(zaman, "POST", "https://x.test/api/is-akisi",
                       istek=json.dumps({"siparisNo": "1", "currentWorkFlowStateShortCode": mevcut,
                                         "workFlowStateChange": degisim}),
                       yanit=json.dumps({"messages": [], "nextWorkFlowStateShortCode": sonraki}))


# DBeaver çıktı biçimleri (aynı tablo): sırası karışık, başlıklı
KOMUT_SATIRLARI = [("sepetOzeti", "KaydetCommand", 0, 1, 20), ("sepetOzeti", "DogrulaCommand", 0, 1, 10),
                   ("sepetOzeti", "SepetGuncelleCommand", 0, 0, 10), ("urunAyari", "UrunYukleCommand", 1, 0, 10),
                   ("urunAyari", "UrunHesaplaCommand", 0, 0, 10)]
KOMUT_BASLIK = ["shrt_code", "state", "step", "cmd_def_id", "shrt_code", "bean_name", "is_pre", "is_post", "sort_id"]


def komut_tablosu(bicim: str, akis: str = "TEST_AKIS") -> str:
    satirlar = [[akis, d, "10", str(900 + i), k, k, str(pre), str(post), str(sira)]
                for i, (d, k, pre, post, sira) in enumerate(KOMUT_SATIRLARI)]
    if bicim == "csv":
        return "\n".join(",".join(f'"{x}"' for x in r) for r in [KOMUT_BASLIK] + satirlar) + "\n"
    if bicim == "txt":
        return "\n".join("|" + "|".join(x.ljust(22) for x in r) + "|"
                         for r in [KOMUT_BASLIK, ["-" * 22] * 9] + satirlar) + "\n"
    return "\n".join("\t".join(r) for r in satirlar)  # pano (Ctrl+C): başlıksız, sekme ayraçlı


def api_cagrilari(env: dict, kok: Path) -> None:
    print("API çağrıları (tarayıcının HAR kaydı)")
    calistir(env, "basla", "API akışı")
    for _ in range(3):
        calistir(env, "cek", ZENITY_RC="1")
    calistir(env, "bitir")
    oturum = son_oturum(env)
    veri = json.loads((oturum / "oturum.json").read_text(encoding="utf-8"))
    kontrol(all("zaman" in a for a in veri["adimlar"]) and "baslangic" in veri and "bitis" in veri,
            "adımlar çekim zamanını, oturum başla/bitir zamanını tutuyor")
    # Zamanları sabitle: başla 10:00, adımlar 10:01 / 10:02 / 10:03, bitir 10:04
    veri.update(baslangic="2026-10-06T10:00:00.000+03:00", bitis="2026-10-06T10:04:00.000+03:00")
    for no, adim in enumerate(veri["adimlar"], 1):
        adim["zaman"] = f"2026-10-06T10:0{no}:00.000+03:00"
    (oturum / "oturum.json").write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    girdiler = [
        har_girdisi("2026-10-06T09:59:00.000+03:00", "GET", "https://x.test/api/eski"),  # başlamadan önce
        har_girdisi("2026-10-06T10:00:30.000+03:00", "GET", "https://x.test/api/musteri/7?token=GIZLI-SORGU",
                    yanit='{"ad": "Ali", "password": "GIZLI-PAROLA"}'),
        har_girdisi("2026-10-06T10:00:31.000+03:00", "GET", "https://x.test/stil.css", tur="text/css"),
        har_girdisi("2026-10-06T07:01:30.000Z", "POST", "https://x.test/api/siparis", durum=201,  # Chrome: "Z"
                    istek='{"urun": "Fiber", "secret": "GIZLI-SIR"}', yanit='{"no": 9}'),
        har_girdisi("2026-10-06T10:01:31.000+03:00", "POST", "https://analytics.test/g/collect", tur="text/plain", yanit=""),
        har_girdisi("2026-10-06T10:01:32.000+03:00", "GET", "https://x.test/api/siparis/9",
                    yanit=json.dumps({"kalemler": [{"ad": f"kalem{i}"} for i in range(5)]})),
        har_girdisi("2026-10-06T10:01:33.000+03:00", "GET", "https://x.test/api/siparis/9"),  # yoklama tekrarı
        har_girdisi("2026-10-06T10:02:30.000+03:00", "GET", "https://x.test/soap/sorgu", tur="text/xml; charset=utf-8",
                    yanit="<r><sifreBilgisi>GIZLI-XML</sifreBilgisi><durum>Aktif</durum></r>"),
        akis_girdisi("2026-10-06T10:02:10.000+03:00", "sepetOzeti", False, "sepetOzeti"),
        akis_girdisi("2026-10-06T10:02:20.000+03:00", "sepetOzeti", True, "urunAyari"),
        akis_girdisi("2026-10-06T10:03:10.000+03:00", "bilinmeyenDurum", True, "sonDurum"),
        har_girdisi("2026-10-06T10:05:00.000+03:00", "GET", "https://x.test/api/sonra"),  # bitirdikten sonra
    ]
    har = kok / "akis.har"
    har.write_text(json.dumps({"log": {"version": "1.2", "creator": {"name": "Firefox", "version": "157.0"},
                                       "entries": girdiler}}), encoding="utf-8")
    kontrol(calistir(env, "api", str(har)).returncode == 0, "api komutu")
    calistir(env, "api", str(har))  # ikinci kez: satırlar çoğalmamalı
    md = oturum / "API akışı.md"
    metin = md.read_text(encoding="utf-8")
    adim = dict(zip(("1", "2", "3"), metin.split("### Adım ")[1:]))
    kontrol("| Ekrana gelen | GET | `/api/musteri/7?token=***` | 200 |" in adim.get("1", "")
            and "| Butonla giden | POST | `/api/siparis` | 201 |" in adim.get("1", ""),
            "GET sonraki ekrana, POST butona basılan ekrana (Adım 1)")
    kontrol(adim.get("2", "").count("| Ekrana gelen | GET | `/api/siparis/9` |") == 1, "aynı ekranda tekrarlanan çağrı tek satır")
    kontrol("… +4 öğe" in adim.get("2", ""), "uzun dizi kısaltıldı")
    kontrol("<sifreBilgisi>***</sifreBilgisi><durum>Aktif" in adim.get("3", "") and "~~~xml" in adim.get("3", ""),
            "XML gövdede gizli alan maskelendi")
    kontrol("GIZLI" not in metin, "jeton, çerez, parola, sır ve sorgudaki token dokümanda yok")
    kontrol(not any(x in metin for x in ("/api/eski", "/api/sonra", "stil.css", "collect")),
            "başla öncesi, bitir sonrası, css ve analitik çağrılar atıldı")
    kontrol("```" not in metin and md.with_name(md.name + ".yedek").exists(),
            "gövdeler ~~~ bloğunda (Rovo'nun ```markdown bloğunu bozmaz), önceki .md yedeklendi")
    kontrol(adim.get("2", "").count("| Butonla giden | POST | `/api/is-akisi` |") == 2,
            "aynı uca farklı gövdeyle giden iki çağrı ayrı satır")

    print("Çalışan komutlar (komut tablosu)")
    for bicim in ("csv", "txt", "pano"):
        tablo = kok / f"komutlar.{bicim}"
        tablo.write_text(komut_tablosu(bicim), encoding="utf-8")
        kontrol(calistir(env, "komutlar", str(tablo)).returncode == 0, f"komutlar: DBeaver {bicim} biçimi okunuyor")
    metin = md.read_text(encoding="utf-8")
    adim = dict(zip(("1", "2", "3"), metin.split("### Adım ")[1:]))
    kontrol("sepetOzeti (durum değişmedi)\n\n| Durum | Ne zaman | Sıra | Komut |\n|---|---|---|---|\n"
            "| sepetOzeti | durum içi | 10 | SepetGuncelleCommand |\n\n" in adim.get("2", ""),
            "durum değişmeyince: mevcut durumun durum içi komutları")
    kontrol("sepetOzeti → urunAyari\n\n| Durum | Ne zaman | Sıra | Komut |\n|---|---|---|---|\n"
            "| sepetOzeti | çıkışta (post) | 10 | DogrulaCommand |\n"
            "| sepetOzeti | çıkışta (post) | 20 | KaydetCommand |\n"
            "| urunAyari | girişte (pre) | 10 | UrunYukleCommand |\n\n" in adim.get("2", ""),
            "durum değişince: mevcut durumun post'u sort_id sırasıyla, sonra sonrakinin pre'si")
    kontrol("UrunHesaplaCommand" not in metin, "çağrılmayan durumun komutları yazılmıyor")
    kontrol("bilinmeyenDurum → sonDurum" in adim.get("3", "") and "kayıt yok" in adim.get("3", ""),
            "tabloda olmayan durum açıkça belirtiliyor")
    calistir(env, "api", str(har))
    kontrol("Çalışan komutlar" in md.read_text(encoding="utf-8"), "HAR yeniden eklenince komut tablosu korunuyor")
    karisik = kok / "iki-akis.csv"
    karisik.write_text(komut_tablosu("csv") + komut_tablosu("csv", "BASKA_AKIS").split("\n", 1)[1], encoding="utf-8")
    r = calistir(env, "komutlar", str(karisik), beklenen=1)
    kontrol(r.returncode == 1 and "birden çok akış" in r.stdout, "birden çok akış içeren tablo reddediliyor")

    bos = kok / "analitik.har"  # kullanıcının ilk denemesindeki gibi yalnızca analitik çağrılar
    bos.write_text(json.dumps({"log": {"entries": [girdiler[4]]}}), encoding="utf-8")
    r = calistir(env, "api", str(bos), beklenen=1)
    kontrol(r.returncode == 1 and "API çağrısı yok" in r.stdout, "API çağrısı olmayan HAR açıklamayla reddediliyor")


def yedek_motor(env: dict, kok: Path) -> None:
    print("OpenVINO çalışmazsa yedek motor")
    yedek_ayar = kok / "yedek-ayar"
    (yedek_ayar / "adimadim").mkdir(parents=True)
    (yedek_ayar / "adimadim" / "ayar.json").write_text(json.dumps({"cihaz": "GPU", "ov_model": "/yok"}))
    ses = next((kok / "dokumanlar").glob("*/ses/adim-01.wav"))
    r = calistir(env, "cevir", str(ses), XDG_CONFIG_HOME=str(yedek_ayar))
    kontrol("sahte yedek çeviri" in r.stdout and "faster-whisper" in r.stderr, "faster-whisper'a düştü")


def ipucu_ve_duzeltme(env: dict, kok: Path) -> None:
    print("Terim ipucu ve düzeltme kuralları")
    dizin = kok / "ipucu-ayar" / "adimadim"
    dizin.mkdir(parents=True)
    ayar = json.loads((kok / "home" / ".config" / "adimadim" / "ayar.json").read_text())
    (dizin / "ayar.json").write_text(json.dumps({**ayar, "ipucu": "prompt"}))
    (dizin / "duzeltmeler.local.txt").write_text("sahte çeviri → düzeltilmiş çeviri\n", encoding="utf-8")
    ses = next((kok / "dokumanlar").glob("*/ses/adim-01.wav"))
    r = calistir(env, "cevir", str(ses), XDG_CONFIG_HOME=str(dizin.parent))
    kontrol("ipuçlu" in r.stdout, "ipucu=prompt: terimler Whisper'a veriliyor")
    kontrol("düzeltilmiş çeviri" in r.stdout and "interaction'u" in r.stdout,
            "düzeltmeler.txt + .local uygulanıyor, Türkçe ek korunuyor")


def goreli_klasor(env: dict, kok: Path) -> None:
    print("Göreli doküman klasörü (kısayol terminalden farklı dizinde çalışır)")
    dizin = kok / "goreli-ayar" / "adimadim"
    dizin.mkdir(parents=True)
    ayar = json.loads((kok / "home" / ".config" / "adimadim" / "ayar.json").read_text())
    (dizin / "ayar.json").write_text(json.dumps({**ayar, "klasor": "goreli-belgeler"}))
    terminal, kisayol = kok / "terminal", kok / "home"
    terminal.mkdir()
    ek = {"XDG_CONFIG_HOME": str(dizin.parent)}
    calistir(env, "basla", "Göreli", cwd=terminal, **ek)
    kontrol(calistir(env, "cek", cwd=kisayol, **ek).returncode == 0, "başka dizinden 'cek' açık dokümanı buluyor")
    kontrol((kok / "home" / "goreli-belgeler").is_dir(), "göreli klasör ev dizinine göre")
    calistir(env, "bitir", cwd=terminal, **ek)


def kisayollar(env: dict, kok: Path) -> None:
    print("GNOME kısayolları")
    kok_yol = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
    (kok / "gsettings.json").write_text(json.dumps({
        "org.gnome.settings-daemon.plugins.media-keys::custom-keybindings": f"['{kok_yol}custom0/']",
        f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{kok_yol}custom0/::name": "'Terminal'",
    }))
    calistir(env, "kisayol")
    calistir(env, "kisayol")  # ikinci kez: kopya oluşturmamalı
    depo = json.loads((kok / "gsettings.json").read_text())
    liste = depo["org.gnome.settings-daemon.plugins.media-keys::custom-keybindings"]
    yuvalar = re.findall(r"/custom(\d+)/", liste)
    kontrol(yuvalar == ["0", "1", "2"], "mevcut kısayol korundu, iki yeni eklendi, tekrar yok")
    komut = depo.get(f"org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:{kok_yol}custom1/::command", "")
    kontrol(str(ARAC) in komut and komut.rstrip("'").endswith(" cek"), "Ctrl+Alt+S bu repodaki aracı çağırıyor")


def arayuz(env: dict) -> None:
    print("Düğmeli pencere")
    betik = """
import json, os, sys, tkinter as tk
sys.path.insert(0, sys.argv[1])
import arayuz as u
assert "Ctrl+Alt+S" in u.ipucu({"adimlar": []}, False)
if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    print("ekran yok, pencere atlandı"); sys.exit(0)
kok = tk.Tk(); kok.withdraw(); kok.deiconify = lambda: None  # test sırasında pencere görünmesin
p = u.Pencere(kok)
def bekle(*komut):
    p.calistir(*komut); p.surec.wait(); p.guncelle(tekrar=False); kok.update()
assert p.ekran == "basla", p.ekran
p.baslik.set("Pencere testi"); p.mod.set("yazi"); p.basla(); p.surec.wait(); p.guncelle(tekrar=False)
assert p.ekran == "kayit" and "Adım 0" in p.kayit_baslik["text"], p.kayit_baslik["text"]
bekle("cek")
assert "Adım 1" in p.kayit_baslik["text"] and len(p.resimler) == 1 and p.resimler[0], "çekilen ekran önizlemede"
gorsel = u.a.aktif_oturum() / "gorseller/adim-01.png"
from PIL import Image
g0 = Image.open(gorsel).size
d = u.Duzenleyici(kok, gorsel); d.withdraw()
d.isaretler = [("kutu", (10, 10, 100, 60), "", []), ("ok", (200, 200, 120, 120), "", []),
               ("yazi", (30, 30), "Buraya tıkla", []), ("kirp", (0, 0, 400, 300), "", [])]
d.kaydet()
assert Image.open(gorsel).size == (400, 300) and (gorsel.parent / ".orijinal/adim-01.png").exists(), "kırp + işaretle, orijinal saklandı"
assert Image.open(gorsel).getpixel((50, 10))[0] > 200, "kırmızı kutu çizildi"
p.guncelle(tekrar=False)
bekle("bitir")
assert p.ekran == "bitis" and u.a.aktif_oturum() is None, "Bitir → bitiş ekranı"
assert "Adım 1" in p.onizleme.get("1.0", "end") and p.onizleme.image_names(), "doküman önizlemesi görselli"
assert "Hazır" in u.son_satir(), u.son_satir()
md = u.a.md_bul(p.bitmis)
p.md_kopyala(); assert kok.clipboard_get() == md.read_text(encoding="utf-8"), "MD'yi kopyala"
p.rovo.insert("1.0", "```markdown\\n# Resmî\\n\\nAdım 1\\n\\nKullanıcı ekranı açar.\\n```")
p.rovo_uygula(); p.surec.wait(); p.guncelle(tekrar=False)
yeni = md.read_text(encoding="utf-8")
assert "```" not in yeni and "Kullanıcı ekranı açar." in yeni and "![Adım 1](gorseller/adim-01.png)" in yeni, yeni
assert md.with_name(md.name + ".yedek").exists() and "Kullanıcı ekranı açar." in p.onizleme.get("1.0", "end"), "Rovo alanı .md + Word"
veri = json.loads((p.bitmis / "oturum.json").read_text(encoding="utf-8"))
har = p.bitmis / "test.har"
har.write_text(json.dumps({"log": {"entries": [{"startedDateTime": veri["adimlar"][0]["zaman"],
    "request": {"method": "POST", "url": "https://x.test/api/is-akisi", "headers": [], "postData": {"mimeType": "application/json",
                "text": '{"currentWorkFlowStateShortCode": "sepetOzeti", "workFlowStateChange": true}'}},
    "response": {"status": 200, "content": {"mimeType": "application/json", "text": '{"nextWorkFlowStateShortCode": "urunAyari"}'}}}]}}))
u.filedialog.askopenfilename = lambda **k: str(har)
p.api_ekle(); p.surec.wait(); p.guncelle(tekrar=False)
assert "API çağrıları" in p.onizleme.get("1.0", "end"), "API ekle (HAR) → önizlemede"
kok.clipboard_clear(); kok.clipboard_append("TEST_AKIS\\tsepetOzeti\\t10\\t1\\tKaydetCommand\\tKaydetCommand\\t0\\t1\\t10\\n")
p.komutlar_yukle(); p.surec.wait(); p.guncelle(tekrar=False)
assert "KaydetCommand" in p.onizleme.get("1.0", "end"), "Komut tablosu (panodan) → önizlemede"
p.yeni(); assert p.ekran == "basla"
kok.destroy(); print("pencere tamam")
"""
    r = subprocess.run([PY, "-c", betik, str(REPO)], env={**env, "ZENITY_METIN": "Pencereden not."},
                       capture_output=True, text=True, timeout=120)
    kontrol(r.returncode == 0, "arayüz: başla → önizleme → kırp/işaretle → bitir → kopyala → Rovo alanı → API ekle → komut tablosu"
            + ("" if r.returncode == 0 else f" ({r.stderr.strip()[-400:]})"))
    print("    " + r.stdout.strip())


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adimadim-test-") as gecici:
        kok = Path(gecici)
        env = ortam_kur(kok)
        try:
            yazili_akis(env)
            sesli_akis(env)
            api_cagrilari(env, kok)
            yedek_motor(env, kok)
            ipucu_ve_duzeltme(env, kok)
            goreli_klasor(env, kok)
            kisayollar(env, kok)
            arayuz(env)
        finally:
            kayitcilari_temizle(kok)
    if BASARISIZ:
        print(f"✗ {len(BASARISIZ)} kontrol başarısız")
        return 1
    print("✓ uçtan uca akış tamam")
    return 0


if __name__ == "__main__":
    sys.exit(main())
