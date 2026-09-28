#!/usr/bin/env python3
"""adımadım — ekrandan ekrana gezerek kullanım senaryosu / doküman çıkaran araç.

Ubuntu 22.04 (GNOME) için yazıldı. Her şey yerelde çalışır: ekran görüntüleri,
notlar ve ses kayıtları makineden hiçbir yere gönderilmez.

Komutlar
  adimadim basla "Akış adı" [--ses]  yeni doküman başlatır
                                      --ses: adımları sesle anlat (yerel Whisper)
  adimadim cek                       ekran görüntüsü al, yeni adım ekle  (Ctrl+Alt+S)
  adimadim not                       son adımın notunu yaz / düzenle     (Ctrl+Alt+N)
  adimadim geri                      son adımı sil
  adimadim durum                     açık dokümanı göster
  adimadim bitir                     bitir; .md ve .docx üret, klasörü aç
  adimadim word [klasör]             elle düzenlenen .md'den .docx'i yeniden üret
  adimadim yeniden [klasör]          bir dokümanın ses kayıtlarını baştan metne çevir
  adimadim cevir dosya.wav ...       ses dosyalarını metne çevirip ekrana yaz
  adimadim kisayol                   GNOME klavye kısayollarını tanımla
  adimadim arayuz                    düğmeli pencere (uygulama menüsünde: adımadım)

Ayarlar: ~/.config/adimadim/ayar.json (kur.sh oluşturur; varsayılanlar ayar.ornek.json'da)
  klasor          dokümanların kaydedileceği yer; boşsa Belgeler/adimadim
  ekran           "pencere" (aktif pencere) ya da "tam" (tüm ekran)
  stt             "openvino" (varsayılan) ya da "faster-whisper"
  cihaz           OpenVINO cihazı: "CPU", "GPU" ya da "NPU" (kur.sh ilk kurulumda algılar)
  ov_kaynak       dönüştürülecek Whisper modeli (ör. openai/whisper-medium)
  ov_model        dönüştürülmüş modelin klasörü (kur.sh yoksa oluşturur)
  whisper_modeli  OpenVINO çalışmazsa yedek faster-whisper modeli ("small" / "medium")
  dil             anlatım dili (varsayılan "tr")
  ipucu           terimleri Whisper'a ipucu olarak ver: "prompt" (initial_prompt), "hotwords" ya da "" (kapalı)
  duzeltme        duzeltmeler.txt (+ .local) kurallarını çıktıya uygula (true/false)
Word şablonu: ~/.config/adimadim/sablon.docx varsa Word çıktısı onun biçimini alır.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as dt
import fcntl
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

UYGULAMA = "adımadım"
REPO_DIZINI = Path(__file__).resolve().parent
AYAR_DIZINI = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "adimadim"
AYAR_DOSYASI = AYAR_DIZINI / "ayar.json"
AKTIF = AYAR_DIZINI / "aktif"  # açık oturumun klasörü
SON = AYAR_DIZINI / "son"  # en son biten oturumun klasörü
KILIT = AYAR_DIZINI / "kilit"
SABLON = AYAR_DIZINI / "sablon.docx"

KAYITCILAR = ("arecord", "parecord")
MEDYA = "org.gnome.settings-daemon.plugins.media-keys"
KISAYOL_KOKU = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
KISAYOLLAR = [  # (GNOME'daki adı, alt komut, tuş)
    ("adimadim cek", "cek", "<Control><Alt>s"),
    ("adimadim not", "not", "<Control><Alt>n"),
]


# --------------------------------------------------------------- genel yardımcılar

def bildir(mesaj: str) -> None:
    """Terminale yazar, masaüstü bildirimi gösterir (kısayolla çalışırken tek geri bildirim bu)."""
    with contextlib.suppress(OSError, ValueError):
        print(mesaj, flush=True)
    if shutil.which("notify-send"):
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run(["notify-send", "-a", UYGULAMA, "-h", "int:transient:1", UYGULAMA, mesaj],
                           capture_output=True, timeout=5)


def belgeler_dizini() -> Path:
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        r = subprocess.run(["xdg-user-dir", "DOCUMENTS"], capture_output=True, text=True, timeout=5)
        yol = r.stdout.strip()
        if r.returncode == 0 and yol and Path(yol) != Path.home():
            return Path(yol)
    return Path.home() / "Documents"


VARSAYILAN_AYAR = {  # asıl kaynak repodaki ayar.ornek.json; bu yalnızca o dosya yoksa kullanılır
    "klasor": "", "ekran": "pencere", "stt": "openvino", "cihaz": "",
    "ov_kaynak": "openai/whisper-medium", "ov_model": "~/modeller/whisper-medium-ov",
    "whisper_modeli": "small", "dil": "tr", "ipucu": "prompt", "duzeltme": True,
}


def ayarlari_oku() -> dict:
    """Varsayılanlar (ayar.ornek.json) + makinenin ayar.json'u. Boş değerler burada çözülür."""
    AYAR_DIZINI.mkdir(parents=True, exist_ok=True)
    ayar = dict(VARSAYILAN_AYAR)
    with contextlib.suppress(OSError, ValueError):
        ayar.update(json.loads((REPO_DIZINI / "ayar.ornek.json").read_text(encoding="utf-8")))
    if AYAR_DOSYASI.exists():
        try:
            ayar.update(json.loads(AYAR_DOSYASI.read_text(encoding="utf-8")))
        except (OSError, ValueError) as hata:
            bildir(f"ayar.json okunamadı ({hata}); varsayılanlar kullanılıyor.")
    else:
        AYAR_DOSYASI.write_text(json.dumps(ayar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Göreli yol ev dizinine göre: kısayol (GNOME) ile terminal farklı dizinlerden çalışır.
    klasor = Path(ayar.get("klasor") or belgeler_dizini() / "adimadim").expanduser()
    ayar["klasor"] = str(klasor if klasor.is_absolute() else Path.home() / klasor)
    ayar["cihaz"] = str(ayar.get("cihaz") or "CPU").upper()
    return ayar


@contextlib.contextmanager
def kilit():
    """İki kısayola art arda basılırsa oturum dosyası bozulmasın."""
    AYAR_DIZINI.mkdir(parents=True, exist_ok=True)
    with open(KILIT, "w", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def klasor_adi(metin: str) -> str:
    s = metin.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:50] or "dokuman"


def dosya_adi(metin: str) -> str:
    """Obsidian'ın ve dosya sisteminin sorun çıkarmayacağı, okunabilir bir ad."""
    ad = re.sub(r'[\\/:*?"<>|#^\[\]]+', " ", metin)
    return re.sub(r"\s+", " ", ad).strip(" .-")[:80] or "dokuman"


def klasoru_ac(yol: Path) -> None:
    if shutil.which("xdg-open"):
        with contextlib.suppress(OSError):
            subprocess.Popen(["xdg-open", str(yol)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)


# --------------------------------------------------------------- oturum ve doküman

def aktif_oturum() -> Path | None:
    try:
        metin = AKTIF.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return Path(metin) if metin and (Path(metin) / "oturum.json").exists() else None


def yukle(oturum: Path) -> dict:
    return json.loads((oturum / "oturum.json").read_text(encoding="utf-8"))


def atomik_yaz(yol: Path, metin: str) -> None:
    gecici = yol.with_name(yol.name + ".tmp")
    gecici.write_text(metin, encoding="utf-8")
    gecici.replace(yol)


def kaydet(oturum: Path, veri: dict) -> None:
    """Oturumu kaydeder, Markdown'ı yeniden yazar (Obsidian'da açıksa canlı güncellenir)."""
    atomik_yaz(oturum / "oturum.json", json.dumps(veri, ensure_ascii=False, indent=2))
    atomik_yaz(oturum / f"{veri['dosya']}.md", markdown(veri))


def markdown(veri: dict) -> str:
    satirlar = [f"# {veri['baslik']}", "",
                f"- **Tarih:** {veri['tarih']}",
                "- **Amaç:** …",
                "- **Aktör:** …",
                "- **Ön koşullar:** …",
                "- **Son koşullar:** …", "",
                "## Ana akış", ""]
    for no, adim in enumerate(veri["adimlar"], 1):
        satirlar += [f"### Adım {no}", "", f"![Adım {no}]({adim['gorsel']})", ""]
        paragraflar = [m.strip() for m in (adim.get("ses_metni"), adim.get("not")) if m and m.strip()]
        if not paragraflar:
            if adim.get("ses") and adim.get("ses_metni") is None:
                paragraflar = ["_Sesli anlatım kaydedildi; doküman bitirilince metne çevrilecek._"]
            else:
                paragraflar = ["_Açıklama eklenmedi._"]
        for paragraf in paragraflar:
            satirlar += [paragraf, ""]
    return "\n".join(satirlar)


def md_bul(oturum: Path) -> Path | None:
    with contextlib.suppress(OSError, ValueError, KeyError):
        md = oturum / f"{yukle(oturum)['dosya']}.md"
        if md.exists():
            return md
    adaylar = sorted(oturum.glob("*.md"))
    return adaylar[0] if adaylar else None


def gorselleri_geri_koy(md: Path) -> None:
    """Rovo'nun işlenmiş çıktısı kopyalanınca görsel bağlantıları ve ### başlıkları kaybolur.
    "Adım N" satırlarını başlık yapar, görseli eksikse altına ekler, "Preview unavailable" satırlarını atar."""
    metin = md.read_text(encoding="utf-8")
    satirlar_, degisti = [], False
    for satir in metin.splitlines():
        if satir.strip() == "Preview unavailable":
            degisti = True
            continue
        m = re.fullmatch(r"\s*(?:#+\s*)?Adım (\d+)\s*", satir)
        gorsel = f"gorseller/adim-{int(m.group(1)):02d}.png" if m else ""
        if m and gorsel not in metin and (md.parent / gorsel).exists():
            satirlar_ += [f"### Adım {m.group(1)}", "", f"![Adım {m.group(1)}]({gorsel})", ""]
            degisti = True
        else:
            satirlar_.append(satir)
    if degisti:
        md.write_text("\n".join(satirlar_) + "\n", encoding="utf-8")


def word_uret(oturum: Path) -> bool:
    md = md_bul(oturum)
    if md is None:
        bildir(f"Klasörde .md bulunamadı: {oturum}")
        return False
    if not shutil.which("pandoc"):
        bildir(f"Markdown hazır: {md}\nWord için: sudo apt install pandoc")
        return False
    gorselleri_geri_koy(md)
    docx = md.with_suffix(".docx")
    # hard_line_breaks: notlardaki satır sonları Word'de de korunsun (Obsidian'daki gibi)
    komut = ["pandoc", f"./{md.name}", "-f", "markdown-implicit_figures+hard_line_breaks",
             "-o", f"./{docx.name}"]
    if SABLON.exists():
        komut.append(f"--reference-doc={SABLON}")
    r = subprocess.run(komut, cwd=oturum, capture_output=True, text=True)
    if r.returncode != 0:
        bildir(f"Word üretilemedi: {r.stderr.strip()[:300]}")
        return False
    bildir(f"Hazır: {docx}")
    return True


# --------------------------------------------------------------- ekran, ses, pencere

def ekran_goruntusu(hedef: Path, kip: str) -> bool:
    """GNOME'da (X11 ve Wayland) gnome-screenshot; yoksa sırayla diğer araçlar."""
    def hazir() -> bool:
        return hedef.exists() and hedef.stat().st_size > 0

    def dene(komut: list[str], stdout_dosyaya: bool = False) -> bool:
        hedef.unlink(missing_ok=True)
        try:
            if stdout_dosyaya:
                with open(hedef, "wb") as f:
                    subprocess.run(komut, stdout=f, stderr=subprocess.DEVNULL, timeout=30)
            else:
                subprocess.run(komut, capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            pass
        return hazir()

    if shutil.which("gnome-screenshot"):
        if kip == "pencere" and dene(["gnome-screenshot", "-w", "-f", str(hedef)]):
            return True
        if dene(["gnome-screenshot", "-f", str(hedef)]):
            return True
    if shutil.which("flameshot") and dene(["flameshot", "full", "--raw"], stdout_dosyaya=True):
        return True
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "x11":  # Wayland'de bunlar siyah görüntü verir
        with contextlib.suppress(Exception):
            import mss  # isteğe bağlı: pip3 install --user mss
            hedef.unlink(missing_ok=True)
            with mss.mss() as ekran:
                ekran.shot(mon=-1, output=str(hedef))
            if hazir():
                return True
        if shutil.which("import") and dene(["import", "-window", "root", str(hedef)]):
            return True
    hedef.unlink(missing_ok=True)
    return False


def surec_calisiyor(pid: int | None) -> bool:
    """pid hâlâ bizim ses kaydedicimiz mi? (Bitmiş, zombi ya da başka bir süreçse hayır.)"""
    if not pid:
        return False
    try:
        komut = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    return any(ad.encode() in komut for ad in KAYITCILAR)


def kayit_baslat(dosya: Path) -> int | None:
    if shutil.which("arecord"):
        komut = ["arecord", "-q", "-f", "S16_LE", "-r", "16000", "-c", "1", "-t", "wav", str(dosya)]
    elif shutil.which("parecord"):
        komut = ["parecord", "--channels=1", "--rate=16000", "--format=s16le",
                 "--file-format=wav", str(dosya)]
    else:
        return None
    surec = subprocess.Popen(komut, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
    return surec.pid


def kayit_durdur(pid: int | None) -> None:
    if not surec_calisiyor(pid):
        return
    time.sleep(0.5)  # ses sunucusunun tamponundaki son kelime kaybolmasın
    with contextlib.suppress(OSError):
        os.kill(pid, signal.SIGINT)  # SIGINT'te WAV dosyası düzgün kapanır
    for _ in range(60):
        if not surec_calisiyor(pid):
            return
        time.sleep(0.05)
    with contextlib.suppress(OSError):
        os.kill(pid, signal.SIGTERM)


def zenity(*arglar: str, girdi: str = "") -> str | None:
    """Zenity penceresi açar; Tamam → çıktı, vazgeç/kapat → None."""
    if not shutil.which("zenity"):
        bildir("zenity bulunamadı: sudo apt install zenity")
        return None
    try:
        r = subprocess.run(["zenity", *arglar], input=girdi, capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.rstrip("\n") if r.returncode == 0 else None


def not_iste(baslik: str, mevcut: str = "", vazgec: str = "Vazgeç") -> str | None:
    return zenity("--text-info", "--editable", f"--title={baslik}", "--width=680", "--height=340",
                  "--ok-label=Kaydet", f"--cancel-label={vazgec}", girdi=mevcut)


def not_kaydet(oturum: Path, adim_id: str, metin: str) -> bool:
    with kilit():
        if not (oturum / "oturum.json").exists():
            return False
        veri = yukle(oturum)
        for adim in veri["adimlar"]:
            if adim["id"] == adim_id:
                adim["not"] = metin
                kaydet(oturum, veri)
                return True
    return False


def yaziya_dok(oturum: Path, veri: dict, ayar: dict) -> None:
    """Ses kayıtlarını yerel Whisper ile metne çevirir; her adımdan sonra kaydeder."""
    bekleyen = []
    for adim in veri["adimlar"]:
        if not adim.get("ses") or adim.get("ses_metni") is not None:
            continue
        dosya = oturum / adim["ses"]
        if dosya.exists():
            bekleyen.append((adim, dosya))
        else:
            adim["ses_metni"] = ""
    if not bekleyen:
        return
    bildir(f"{len(bekleyen)} anlatım metne çevriliyor… (model yükleniyor)")
    ad, cevir = cevirici_olustur(ayar)
    print(f"  Kullanılan: {ad}", flush=True)
    for adim, metin in zip((a for a, _ in bekleyen), adimlara_dagit(cevir, [d for _, d in bekleyen])):
        adim["ses_metni"] = metin
    kaydet(oturum, veri)


def wav_oku(dosya: Path):
    """16 kHz mono 16-bit WAV → float32 dizi. Başlıktaki uzunluğa bakılmaz (arecord bozuk bırakabiliyor)."""
    import wave
    import numpy as np
    with wave.open(str(dosya), "rb") as w:
        if w.getframerate() != 16000 or w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise ValueError(f"{dosya.name}: 16 kHz mono 16-bit bekleniyordu")
        ham = w.readframes(w.getnframes())
    return np.frombuffer(ham, dtype=np.int16).astype(np.float32) / 32768.0


def adimlara_dagit(cevir, dosyalar: list) -> list:
    """Adımların seslerini birleştirip tek seferde çevirir, cümleleri başladıkları adıma dağıtır.

    Kullanıcı konuşurken Ctrl+Alt+S'ye basınca cümle iki dosyaya bölünür; ayrı ayrı çevrilince
    sınırdaki kelimeler kaybolur ve kısa parçalarda model cümleyi atlar."""
    import numpy as np
    sesler = [wav_oku(d) for d in dosyalar]
    sinirlar = np.cumsum([0] + [len(x) for x in sesler]) / 16000
    metinler = [[] for _ in dosyalar]
    for bas, _son, metin in cevir.parcala(np.concatenate(sesler) if sesler else np.zeros(0, np.float32)):
        sira = min(int(np.searchsorted(sinirlar, bas, side="right")) - 1, len(dosyalar) - 1)
        metinler[max(sira, 0)].append(metin.strip())
    return [cevir.duzelt(" ".join(m).strip()) for m in metinler]


SOZLUK = REPO_DIZINI / "terim_sozlugu_ham_→_normalize.md"


def satirlar(*dosyalar: Path) -> list:
    """Dosyaların yorumsuz, boş olmayan satırları (olmayan dosya atlanır)."""
    sonuc = []
    for dosya in dosyalar:
        if dosya.exists():
            for satir in dosya.read_text(encoding="utf-8").splitlines():
                satir = satir.split("#", 1)[0].strip()
                if satir:
                    sonuc.append(satir)
    return sonuc


def terimleri_oku() -> list:
    """terimler.txt, terimler.local.txt ve (varsa) terim sözlüğünün normalize biçimleri."""
    sozluk = re.findall(r"^\s*normalize:\s*(.+?)\s*$", SOZLUK.read_text(encoding="utf-8"), re.M) if SOZLUK.exists() else []
    # Özel terimler önce: ipucu uzunsa kesilen genel terimler olsun.
    return list(dict.fromkeys(satirlar(AYAR_DIZINI / "terimler.local.txt") + sozluk + satirlar(REPO_DIZINI / "terimler.txt")))


def ipucu_metni() -> str:
    """Whisper'a verilecek ipucu. Uzun ifadeler atlanır; Whisper ipucunu ~224 token'da (~700 karakter) keser."""
    # Whisper ipucunun üslubunu taklit eder: yalnız liste verilirse cümle yerine liste yazar.
    # Bu yüzden ipucu doğal, noktalamalı bir anlatım cümlesiyle biter.
    son = " Şimdi bu ekranda ilgili butona tıklıyoruz, açılan sayfada bilgileri girip kaydediyoruz."
    metin = "Anlatımda geçen terimler:"
    for t in (t for t in terimleri_oku() if len(t.split()) <= 4):
        if len(metin) + len(t) + 2 + len(son) > 700:
            break
        metin += (" " if metin.endswith(":") else ", ") + t
    return metin + "." + son


def duzeltme_kurallari() -> list:
    """duzeltmeler.txt (+ .local): "yanlış → doğru" satırları; büyük/küçük harf duyarsız, tam kelime."""
    kurallar = []
    for satir in satirlar(REPO_DIZINI / "duzeltmeler.txt", AYAR_DIZINI / "duzeltmeler.local.txt"):
        if "→" in satir:
            yanlis, dogru = (x.strip() for x in satir.split("→", 1))
            # Türkçe ek korunur: "interaksiyonu" -> "interaction'u"
            kurallar.append((re.compile(rf"(?<!\w){re.escape(yanlis)}(\w*)", re.I),
                             lambda m, d=dogru: d + ("'" + m.group(1) if m.group(1) else "")))
    return kurallar


def cevirici_olustur(ayar: dict):
    """(açıklama, cevir) döndürür; ayarda duzeltme açıksa çıktıya duzeltmeler.txt kuralları uygulanır."""
    ad, parcala = _cevirici(ayar)
    kurallar = duzeltme_kurallari() if ayar.get("duzeltme", True) else []

    def duzelt(metin: str) -> str:
        for kalip, dogru in kurallar:
            metin = kalip.sub(dogru, metin)
        return metin

    def cevir(dosya: Path) -> str:
        return duzelt(" ".join(m.strip() for _, _, m in parcala(wav_oku(dosya))).strip())
    cevir.parcala, cevir.duzelt = parcala, duzelt
    return ad, cevir


def _cevirici(ayar: dict):
    """(açıklama, parcala) döndürür; parcala(ses) -> [(başlangıç sn, bitiş sn, metin)]. Tüm konuşma tanıma buradan geçer.

    Varsayılan OpenVINO: aynı model ve kod VM'de CPU'da, ana makinede GPU/NPU'da çalışır;
    böylece VM'deki ölçümler ana makineyi temsil eder. OpenVINO kurulamazsa faster-whisper'a düşer."""
    cihaz = str(ayar.get("cihaz") or "CPU").upper()
    if str(ayar.get("stt", "openvino")).lower() == "openvino":
        try:
            return f"OpenVINO / {cihaz}", openvino_cevirici(ayar, cihaz)
        except Exception as hata:  # kurulum, model ya da sürücü sorunu
            bildir(f"OpenVINO ({cihaz}) kullanılamadı: {hata}. faster-whisper (CPU) deneniyor.")
    return f"faster-whisper / CPU ({ayar.get('whisper_modeli', 'small')})", faster_whisper_cevirici(ayar)


def faster_whisper_cevirici(ayar: dict):
    from faster_whisper import WhisperModel
    model = WhisperModel(ayar.get("whisper_modeli", "small"), device="cpu", compute_type="int8")

    def parcala(ses) -> list:
        if ses.size == 0:
            return []
        parcalar, _ = model.transcribe(ses, language=ayar.get("dil", "tr"), vad_filter=True,
                                       initial_prompt=ipucu_metni() if ayar.get("ipucu") else None)
        return [(p.start, p.end, p.text) for p in parcalar]
    return parcala


def konusma_bolumleri(ses) -> list:
    """Silero VAD (faster-whisper ile gelir): konuşma bölümleri [(başlangıç, bitiş)] örnek olarak.
    VAD yoksa sesin tamamı tek bölümdür."""
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps
    except ImportError:
        return [(0, len(ses))]
    return [(b["start"], b["end"]) for b in
            get_speech_timestamps(ses, VadOptions(min_silence_duration_ms=2000, speech_pad_ms=400))]


def openvino_cevirici(ayar: dict, cihaz: str):
    """OpenVINO GenAI Whisper (CPU/GPU/NPU). Model kur.sh tarafından optimum-cli ile dönüştürülür."""
    import numpy as np
    import openvino_genai
    model_dizini = Path(str(ayar.get("ov_model", ""))).expanduser()
    if not (model_dizini / "openvino_encoder_model.xml").exists():
        raise FileNotFoundError(f"OpenVINO modeli bulunamadı: {model_dizini}")
    boru = openvino_genai.WhisperPipeline(str(model_dizini), cihaz)
    dil = f"<|{ayar.get('dil', 'tr')}|>"
    ek = {}
    if ayar.get("ipucu") == "prompt":
        ek["initial_prompt"] = ipucu_metni()
    elif ayar.get("ipucu") == "hotwords":
        ek["hotwords"] = ipucu_metni()

    def parcala(ses) -> list:
        if ses.size == 0 or float(np.abs(ses).max()) < 0.01:  # sessiz kayıtta model uydurmasın
            return []
        bolumler = konusma_bolumleri(ses)
        if not bolumler:  # gürültü var, konuşma yok: Whisper "Altyazı M.K." gibi metin uydurur
            return []
        kisa = np.concatenate([ses[b:e] for b, e in bolumler])
        sonuc = boru.generate(kisa.tolist(), language=dil, task="transcribe", return_timestamps=True, **ek)
        # VAD sessizlikleri çıkardı: zaman damgalarını orijinal sese geri taşı
        baslar = np.cumsum([0] + [e - b for b, e in bolumler[:-1]]) / 16000

        def asil(t: float) -> float:
            i = max(int(np.searchsorted(baslar, t, side="right")) - 1, 0)
            return bolumler[i][0] / 16000 + t - baslar[i]
        return [(asil(c.start_ts), asil(max(c.end_ts, c.start_ts)), c.text) for c in sonuc.chunks]
    return parcala


# --------------------------------------------------------------- komutlar

def cmd_basla(args, ayar) -> int:
    acik = aktif_oturum()
    if acik:
        bildir(f"Zaten açık bir doküman var: {acik.name}. Önce: adimadim bitir")
        return 1
    baslik = " ".join(args.baslik).strip()
    if not baslik:
        baslik = (zenity("--entry", "--title=Yeni doküman", "--text=Akışın adı:", "--width=420") or "").strip()
    if not baslik:
        bildir("Başlık girilmedi; iptal edildi.")
        return 1
    if args.ses:
        if not (importlib.util.find_spec("openvino_genai") or importlib.util.find_spec("faster_whisper")):
            bildir("Sesli mod için konuşma tanıma kurulu değil. Repoda ./kur.sh çalıştır.")
            return 1
        if not any(shutil.which(k) for k in KAYITCILAR):
            bildir("Ses kaydedici bulunamadı: sudo apt install alsa-utils")
            return 1
    simdi = dt.datetime.now()
    taban = Path(ayar["klasor"]).expanduser() / f"{simdi:%Y-%m-%d_%H%M}_{klasor_adi(baslik)}"
    oturum, sayac = taban, 2
    while (oturum / "oturum.json").exists():
        oturum, sayac = taban.with_name(f"{taban.name}-{sayac}"), sayac + 1
    (oturum / "gorseller").mkdir(parents=True, exist_ok=True)
    if args.ses:
        (oturum / "ses").mkdir(exist_ok=True)
    veri = {"baslik": baslik, "dosya": dosya_adi(baslik), "tarih": f"{simdi:%d.%m.%Y}",
            "mod": "ses" if args.ses else "yazi", "adimlar": [], "kayit_pid": None}
    with kilit():
        kaydet(oturum, veri)
        AKTIF.write_text(str(oturum), encoding="utf-8")
    nasil = "her ekranda Ctrl+Alt+S'ye bas ve anlat" if args.ses else "her ekranda Ctrl+Alt+S'ye bas, notunu yaz"
    bildir(f"Başladı: {baslik} — {nasil}.")
    print(f"Klasör: {oturum}")
    return 0


def cmd_cek(args, ayar) -> int:
    with kilit():
        oturum = aktif_oturum()
        if not oturum:
            bildir('Açık doküman yok. Önce: adimadim basla "Akış adı"')
            return 1
        veri = yukle(oturum)
        no = len(veri["adimlar"]) + 1
        adim = {"id": uuid.uuid4().hex[:8], "gorsel": f"gorseller/adim-{no:02d}.png",
                "ses": None, "ses_metni": None, "not": ""}
        if not ekran_goruntusu(oturum / adim["gorsel"], ayar.get("ekran", "pencere")):
            bildir("Ekran görüntüsü alınamadı. Kurulu mu: sudo apt install gnome-screenshot")
            return 1
        if veri["mod"] == "ses":
            kayit_durdur(veri.get("kayit_pid"))  # önceki adımın anlatımı burada biter
            adim["ses"] = f"ses/adim-{no:02d}.wav"
            veri["kayit_pid"] = kayit_baslat(oturum / adim["ses"])
        veri["adimlar"].append(adim)
        kaydet(oturum, veri)
    if veri["mod"] == "ses":
        bildir(f"Adım {no} — anlat 🎙️ (bitince sonraki ekranda Ctrl+Alt+S)")
        return 0
    metin = not_iste(f"Adım {no} — bu ekranda ne yapılıyor?", vazgec="Notsuz geç")
    if metin and metin.strip():
        not_kaydet(oturum, adim["id"], metin.strip())
    return 0


def cmd_not(args, ayar) -> int:
    oturum = aktif_oturum()
    if not oturum:
        bildir("Açık doküman yok.")
        return 1
    veri = yukle(oturum)
    if not veri["adimlar"]:
        bildir("Henüz adım yok. Önce Ctrl+Alt+S ile ekranı çek.")
        return 1
    no, adim = len(veri["adimlar"]), veri["adimlar"][-1]
    metin = not_iste(f"Adım {no} — notu yaz / düzenle", mevcut=adim.get("not", ""))
    if metin is None:
        return 0
    not_kaydet(oturum, adim["id"], metin.strip())
    bildir(f"Adım {no} notu kaydedildi.")
    return 0


def cmd_geri(args, ayar) -> int:
    with kilit():
        oturum = aktif_oturum()
        if not oturum:
            bildir("Açık doküman yok.")
            return 1
        veri = yukle(oturum)
        if not veri["adimlar"]:
            bildir("Silinecek adım yok.")
            return 1
        kayit_durdur(veri.get("kayit_pid"))  # süren kayıt silinen adıma aitti
        veri["kayit_pid"] = None
        adim = veri["adimlar"].pop()
        for anahtar in ("gorsel", "ses"):
            if adim.get(anahtar):
                (oturum / adim[anahtar]).unlink(missing_ok=True)
        kaydet(oturum, veri)
    bildir(f"Son adım silindi; {len(veri['adimlar'])} adım kaldı.")
    return 0


def cmd_durum(args, ayar) -> int:
    oturum = aktif_oturum()
    if not oturum:
        bildir("Açık doküman yok.")
        return 0
    veri = yukle(oturum)
    tur = "sesli" if veri["mod"] == "ses" else "yazılı"
    kayit = ", kayıt sürüyor 🎙️" if surec_calisiyor(veri.get("kayit_pid")) else ""
    bildir(f"{veri['baslik']}: {len(veri['adimlar'])} adım ({tur}{kayit})")
    print(f"Klasör: {oturum}")
    return 0


def cmd_bitir(args, ayar) -> int:
    with kilit():
        oturum = aktif_oturum()
        if not oturum:
            bildir("Açık doküman yok.")
            return 1
        veri = yukle(oturum)
        kayit_durdur(veri.get("kayit_pid"))
        veri["kayit_pid"] = None
        kaydet(oturum, veri)
        AKTIF.unlink(missing_ok=True)
        SON.write_text(str(oturum), encoding="utf-8")
    if veri["mod"] == "ses":
        try:
            yaziya_dok(oturum, veri, ayar)
        except Exception as hata:  # model indirilemedi vb. — doküman yine de üretilsin
            bildir(f"Ses metne çevrilemedi: {hata}")
    word_uret(oturum)
    klasoru_ac(oturum)
    return 0


def klasor_sec(klasor: str | None) -> Path | None:
    """Verilen klasör; verilmediyse en son biten doküman."""
    if klasor:
        return Path(klasor).expanduser().resolve()
    try:
        return Path(SON.read_text(encoding="utf-8").strip())
    except OSError:
        bildir("Klasör belirt: adimadim <komut> <doküman klasörü>")
        return None


def cmd_word(args, ayar) -> int:
    oturum = klasor_sec(args.klasor)
    return 0 if oturum and word_uret(oturum) else 1


def cmd_yeniden(args, ayar) -> int:
    """Bitmiş bir dokümanın ses kayıtlarını güncel model/ayarlarla baştan metne çevirir."""
    oturum = klasor_sec(args.klasor)
    if not oturum or not (oturum / "oturum.json").exists():
        bildir(f"Doküman bulunamadı: {oturum}")
        return 1
    if aktif_oturum() == oturum:
        bildir("Bu doküman hâlâ açık; önce: adimadim bitir")
        return 1
    veri = yukle(oturum)
    sesli = [a for a in veri["adimlar"] if a.get("ses")]
    if not sesli:
        bildir("Bu dokümanda ses kaydı yok.")
        return 1
    md = md_bul(oturum)
    if md:  # .md'de elle yapılan düzeltmeler kaybolmasın
        shutil.copy2(md, md.with_name(md.name + ".yedek"))
        print(f"Önceki metin yedeklendi: {md.name}.yedek")
    for adim in sesli:
        adim["ses_metni"] = None
    yaziya_dok(oturum, veri, ayar)
    word_uret(oturum)
    return 0


def cmd_cevir(args, ayar) -> int:
    dosyalar = [Path(d).expanduser() for d in args.dosyalar]
    eksik = [str(d) for d in dosyalar if not d.exists()]
    if eksik:
        bildir(f"Bulunamadı: {', '.join(eksik)}")
        return 1
    ad, cevir = cevirici_olustur(ayar)
    print(f"({ad})", file=sys.stderr)
    for dosya in dosyalar:
        metin = cevir(dosya)
        print(f"{dosya.name}: {metin}" if len(dosyalar) > 1 else metin, flush=True)
    return 0


def gsettings(*arglar: str) -> str:
    return subprocess.run(["gsettings", *arglar], capture_output=True, text=True, check=True).stdout.strip()


def gv_liste(metin: str) -> list[str]:
    metin = metin.strip()
    if metin.startswith("@as"):
        metin = metin[3:].strip()
    return [str(x) for x in ast.literal_eval(metin)] if metin else []


def gv_metin(metin: str) -> str:
    with contextlib.suppress(ValueError, SyntaxError):
        deger = ast.literal_eval(metin.strip())
        if isinstance(deger, str):
            return deger
    return metin.strip()


def gv_tirnakla(metin: str) -> str:
    return "'" + metin.replace("\\", "\\\\").replace("'", "\\'") + "'"


def cmd_kisayol(args, ayar) -> int:
    if not shutil.which("gsettings"):
        bildir("gsettings bulunamadı; kısayolları Ayarlar > Klavye > Özel Kısayollar'dan elle ekle.")
        return 1
    betik = Path(__file__).resolve()
    python = sys.executable or "python3"
    yollar = gv_liste(gsettings("get", MEDYA, "custom-keybindings"))
    adlara_gore = {gv_metin(gsettings("get", f"{MEDYA}.custom-keybinding:{y}", "name")): y for y in yollar}
    for ad, alt_komut, tus in KISAYOLLAR:
        yol = adlara_gore.get(ad)
        if yol is None:  # yoksa ilk boş customN yuvasını kullan; mevcut kısayollara dokunma
            sira = 0
            while f"{KISAYOL_KOKU}custom{sira}/" in yollar:
                sira += 1
            yol = f"{KISAYOL_KOKU}custom{sira}/"
            yollar.append(yol)
        sema = f"{MEDYA}.custom-keybinding:{yol}"
        gsettings("set", sema, "name", gv_tirnakla(ad))
        gsettings("set", sema, "command",
                  gv_tirnakla(f"{shlex.quote(python)} {shlex.quote(str(betik))} {alt_komut}"))
        gsettings("set", sema, "binding", gv_tirnakla(tus))
    gsettings("set", MEDYA, "custom-keybindings", "[" + ", ".join(gv_tirnakla(y) for y in yollar) + "]")
    bildir("Kısayollar hazır: Ctrl+Alt+S ekranı çeker, Ctrl+Alt+N son adımın notunu açar.")
    return 0


# --------------------------------------------------------------- giriş

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="adimadim",
                                 description="Ekrandan ekrana gezerek kullanım senaryosu / doküman çıkarır.")
    alt = ap.add_subparsers(dest="komut", required=True, metavar="komut")
    p = alt.add_parser("basla", help="yeni doküman başlat")
    p.add_argument("baslik", nargs="*", help="akışın adı")
    p.add_argument("--ses", action="store_true", help="adımları sesle anlat (yerel Whisper)")
    alt.add_parser("cek", help="ekran görüntüsü al, yeni adım ekle (Ctrl+Alt+S)")
    alt.add_parser("not", help="son adımın notunu yaz/düzenle (Ctrl+Alt+N)")
    alt.add_parser("geri", help="son adımı sil")
    alt.add_parser("durum", help="açık dokümanı göster")
    alt.add_parser("bitir", help="bitir; .md ve .docx üret")
    p = alt.add_parser("word", help="düzenlenmiş .md'den .docx'i yeniden üret")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("yeniden", help="bir dokümanın ses kayıtlarını baştan metne çevir")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("cevir", help="ses dosyalarını metne çevirip ekrana yaz")
    p.add_argument("dosyalar", nargs="+", help="16 kHz mono WAV dosyaları")
    alt.add_parser("kisayol", help="GNOME klavye kısayollarını tanımla")
    alt.add_parser("arayuz", help="düğmeli pencereyi aç")
    args = ap.parse_args(argv)
    komutlar = {"basla": cmd_basla, "cek": cmd_cek, "not": cmd_not, "geri": cmd_geri,
                "durum": cmd_durum, "bitir": cmd_bitir, "word": cmd_word, "yeniden": cmd_yeniden,
                "cevir": cmd_cevir, "kisayol": cmd_kisayol,
                "arayuz": lambda args, ayar: __import__("arayuz").main()}
    return komutlar[args.komut](args, ayarlari_oku())


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as hata:  # kısayolla çalışırken terminal yok; hatayı bildirim olarak göster
        bildir(f"Hata: {hata}")
        raise
