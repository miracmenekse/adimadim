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
import os, sys, tkinter as tk
sys.path.insert(0, sys.argv[1])
import arayuz as u
assert "Ctrl+Alt+S" in u.ipucu({"adimlar": []}, False)
if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    print("ekran yok, pencere atlandı"); sys.exit(0)
kok = tk.Tk(); p = u.Pencere(kok)
def bekle(*komut):
    p.calistir(*komut); p.surec.wait(); p.guncelle(tekrar=False); kok.update()
assert p.ekran == "basla", p.ekran
p.baslik.set("Pencere testi"); p.mod.set("yazi"); p.basla(); p.surec.wait(); p.guncelle(tekrar=False)
assert p.ekran == "kayit" and "Adım 0" in p.kayit_baslik["text"], p.kayit_baslik["text"]
bekle("cek")
assert "Adım 1" in p.kayit_baslik["text"] and len(p.resimler) == 1 and p.resimler[0], "çekilen ekran önizlemede"
bekle("bitir")
assert p.ekran == "bitis" and u.a.aktif_oturum() is None, "Bitir → bitiş ekranı"
assert "Adım 1" in p.onizleme.get("1.0", "end") and p.onizleme.image_names(), "doküman önizlemesi görselli"
assert "Hazır" in u.son_satir(), u.son_satir()
p.yeni(); assert p.ekran == "basla"
kok.destroy(); print("pencere tamam")
"""
    r = subprocess.run([PY, "-c", betik, str(REPO)], env={**env, "ZENITY_METIN": "Pencereden not."},
                       capture_output=True, text=True, timeout=120)
    kontrol(r.returncode == 0, "arayüz: başla → önizlemeli kayıt → bitir → bitiş önizlemesi"
            + ("" if r.returncode == 0 else f" ({r.stderr.strip()[-400:]})"))
    print("    " + r.stdout.strip())


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="adimadim-test-") as gecici:
        kok = Path(gecici)
        env = ortam_kur(kok)
        try:
            yazili_akis(env)
            sesli_akis(env)
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
