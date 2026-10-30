#!/usr/bin/env python3
"""adımadım — ekrandan ekrana gezerek kullanım senaryosu / doküman çıkaran araç.

Ubuntu 22.04 (GNOME) için yazıldı. Her şey yerelde çalışır: ekran görüntüleri,
notlar ve ses kayıtları makineden hiçbir yere gönderilmez.

Komutlar
  adimadim basla "Akış adı" [--ses]  yeni doküman başlatır
                                      --ses: adımları sesle anlat (yerel Whisper)
  adimadim cek [--tam]               ekran görüntüsü al, yeni adım ekle  (Ctrl+Alt+S)
  adimadim not                       son adımın notunu yaz / düzenle     (Ctrl+Alt+N)
  adimadim geri                      son adımı sil
  adimadim durum                     açık dokümanı göster
  adimadim bitir                     bitir; .md ve .docx üret, klasörü aç
  adimadim word [klasör]             elle düzenlenen .md'den .docx'i yeniden üret
  adimadim yeniden [klasör]          bir dokümanın ses kayıtlarını baştan metne çevir
  adimadim api dosya.har [klasör]    tarayıcının Ağ sekmesinden kaydedilen API çağrılarını adımlara ekle
  adimadim komutlar tablo.txt [klasör]  durumlarda çalışan komutların tablosunu yükle (iş akışı çağrılarının altına)
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
  api_filtre      yalnızca URL'sinde bu parçalardan biri geçen API çağrıları (ör. ["/api/"]); boşsa JSON/XML olanlar
  api_gizle       istek/yanıt gövdesi ve sorguda adında bunlar geçen alanlar *** yazılır
  mikrofon        kayıt kaynağının adında geçen parça (ör. "bluez_input"); boşsa sistem varsayılanı (arecord)
  mikrofon_profil kulaklığın mikrofon profili (ör. "headset-head-unit-msbc"); yalnız sesli oturum boyunca
                  geçilir, bitince eski profile döner; boşsa profile dokunulmaz
  son_ekran_durumu son ekranın iş akışı durumu (ör. "orderSubmit"); bu duruma geçilirken ekran
                  biter, sonraki durumlar arka plandadır (ekran adımı değildir); boşsa sınır yok
  sabit_gecisler  HAR'sız da bilinen sabit iş akışı geçişleri: uc'ünde geçen parça →
                  [mevcut durum, sonraki durum] (ör. "customerOrder/initialize":
                  ["orderInitialize", "cartSummary"]); bu parça geçen yazan çağrı o geçişi
                  yapmış sayılır, akış kayda yazılmaz; eski dokümanlar HAR'sız çalışır
Word şablonu: ~/.config/adimadim/sablon.docx varsa Word çıktısı onun biçimini alır.
"""

from __future__ import annotations

import argparse
import ast
import base64
import bisect
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
from urllib.parse import urlsplit

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


def belgeler_dizini(tur: str = "DOCUMENTS") -> Path:
    """xdg kullanıcı dizini (DOWNLOAD: İndirilenler); bulunamazsa ~/Documents ya da ev dizini."""
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        r = subprocess.run(["xdg-user-dir", tur], capture_output=True, text=True, timeout=5)
        yol = r.stdout.strip()
        if r.returncode == 0 and yol and Path(yol) != Path.home():
            return Path(yol)
    return Path.home() / "Documents" if tur == "DOCUMENTS" else Path.home()


VARSAYILAN_AYAR = {  # asıl kaynak repodaki ayar.ornek.json; bu yalnızca o dosya yoksa kullanılır
    "klasor": "", "ekran": "pencere", "stt": "openvino", "cihaz": "",
    "ov_kaynak": "openai/whisper-medium", "ov_model": "~/modeller/whisper-medium-ov",
    "whisper_modeli": "small", "dil": "tr", "ipucu": "prompt", "duzeltme": True,
    "api_filtre": [], "api_gizle": ["password", "parola", "sifre", "token", "secret"],
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
    def adim_blok(no: int, adim: dict) -> list:  # bir adımın bütün satırları (başlık → komutlar)
        blok = [f"### Adım {no}", "", f"![Adım {no}]({adim['gorsel']})", ""]
        metin = (adim.get("metin") or "").strip()
        if metin:  # Rovo ya da elle düzeltilmiş anlatım; ses_metni/not yerine
            blok += [metin, ""]
        else:
            paragraflar = [m.strip() for m in (adim.get("ses_metni"), adim.get("not")) if m and m.strip()]
            if not paragraflar:
                if adim.get("ses") and adim.get("ses_metni") is None:
                    paragraflar = ["_Sesli anlatım kaydedildi; doküman bitirilince metne çevrilecek._"]
                else:
                    paragraflar = ["_Açıklama eklenmedi._"]
            for paragraf in paragraflar:
                blok += [paragraf, ""]
        if adim.get("api"):
            blok += ["#### API çağrıları", "", "| Yön | Metot | Uç nokta | Durum |", "|---|---|---|---|"]
            blok += [f"| {c['yon']} | {c['metot']} | `{c['uc']}` | {c['durum']} |" for c in adim["api"]]
            blok.append("")
            for c in adim["api"]:
                for ad, govde_ in (("İstek", c["istek"]), ("Yanıt", c["yanit"])):
                    if govde_:  # ~~~: Rovo çıktıyı ```markdown bloğunda verir, ``` o bloğu erken kapatırdı
                        dil = "json" if govde_[0] in "{[" else "xml" if govde_[0] == "<" else ""
                        blok += [f"{ad}: `{c['metot']} {c['uc']}`", "", f"~~~{dil}", govde_, "~~~", ""]
        akisli = [(c, akis) for c in adim.get("api") or [] if (akis := cagri_akisi(c, ayar))]
        if akisli and veri.get("komutlar"):
            blok += ["#### Çalışan komutlar", ""]
            for c, akis in akisli:
                gecis = (f"{akis['mevcut']} → {akis['sonraki'] or '?'}" if akis["degisim"]
                         else f"{akis['mevcut']} (durum değişmedi)")
                blok += [f"`{c['metot']} {c['uc']}` · {gecis}", ""]
                komutlar = calisan_komutlar(veri["komutlar"], akis)
                if komutlar:
                    blok += ["| Durum | Ne zaman | Sıra | Komut |", "|---|---|---|---|"]
                    blok += [f"| {k['durum']} | {ASAMA[k['asama']]} | {k['sira']} | {k['komut']} |" for k in komutlar]
                else:
                    blok.append("_Komut tablosunda bu çağrı için kayıt yok._")
                blok.append("")
        return blok

    ust = veri.get("ust") or {}  # yeniden üretimde .md'deki düzeltilmiş üst alan değerleri
    satirlar = [f"# {veri['baslik']}", "",
                f"- **Tarih:** {veri['tarih']}",
                f"- **Amaç:** {ust.get('Amaç') or '…'}",
                f"- **Aktör:** {ust.get('Aktör') or '…'}",
                f"- **Ön koşullar:** {ust.get('Ön koşullar') or '…'}",
                f"- **Son koşullar:** {ust.get('Son koşullar') or '…'}", ""]
    ayar = ayarlari_oku()
    adimlar = veri["adimlar"]
    durums = adim_durumlari(adimlar, ayar) if any(a.get("api") for a in adimlar) else []
    if any(durums):  # API'li dokümanda akış state'e göre gruplanır; adım sırası (kronoloji) korunur
        onceki = ""  # bir önceki ekran durumunun kodu; ilk durumda önceki yok
        i = 0
        while i < len(adimlar):
            durum = durums[i]
            j = i
            while j < len(adimlar) and durums[j] == durum:  # ardışık aynı durumlu adımlar tek grup
                j += 1
            if durum:
                satirlar += ["## Durum: " + (f"{durum} ({onceki} → {durum})" if onceki else durum), ""]
                onceki = durum
            else:
                satirlar += ["## Başlamadan önce", ""]
            for no in range(i + 1, j + 1):
                satirlar += adim_blok(no, adimlar[no - 1])
            i = j
    else:  # akış kanmayan (ya da API'siz) doküman: çıktı bugünküyle birebir
        satirlar += ["## Ana akış", ""]
        for no, adim in enumerate(adimlar, 1):
            satirlar += adim_blok(no, adim)
    # Ekran sınırının (son_ekran_durumu) tablodaki son satırından sonra ilk görülen durumlar:
    # son ekrandan sonra arka planda çalışmaya başlayan işler (CSV satır sırası = akış sırası)
    tablo = veri.get("komutlar") or []
    onlu = ["pre", "ic", "post"]  # ASAMA etiketlerinin görünme sırası: pre, during, post
    sinir = ayar.get("son_ekran_durumu") or ""
    sinir_son = -1
    for i, k in enumerate(tablo):
        if k["durum"] == sinir:
            sinir_son = i
    arka = []
    if sinir and sinir_son >= 0:  # sınır boş ya da tabloda yoksa bölüm yok
        for i, k in enumerate(tablo):
            d = k["durum"]
            if i > sinir_son and d not in arka and not any(c["durum"] == d for c in tablo[:sinir_son + 1]):
                arka.append(d)
    if arka:
        satirlar += ["## Arka planda çalışan durumlar", ""]
        for d in arka:
            satirlar += [f"### {d}", "", "| Ne zaman | Sıra | Komut |", "|---|---|---|"]
            secili = sorted((k for k in tablo if k["durum"] == d),
                            key=lambda k: (onlu.index(k["asama"]), k["sira"]))
            satirlar += [f"| {ASAMA[k['asama']]} | {k['sira']} | {k['komut']} |" for k in secili]
            satirlar.append("")
    return "\n".join(satirlar)


def son_dokumanlar(ayar: dict, adet: int = 10) -> list[Path]:
    """Belgeler klasöründeki son dokümanlar: oturum.json'u olan, açık olmayan klasörler; yeni önce; bozuk json atlanır."""
    acik = aktif_oturum()
    doklar = []
    for dosya in Path(ayar.get("klasor") or "").expanduser().glob("*/oturum.json"):
        oturum = dosya.parent
        if oturum == acik or not dosya.is_file():
            continue
        try:
            veri = json.loads(dosya.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # bozuk json: listede gösterilmez
        if not isinstance(veri, dict):
            continue
        doklar.append(oturum)
    yeni_once = sorted(doklar, key=lambda d: d.joinpath("oturum.json").stat().st_mtime, reverse=True)
    return yeni_once[:max(0, adet)]


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


YER_TUTUCULAR = ("_Açıklama eklenmedi._",  # metni olmayan adımların yer tutucuları: boş sayılır
                 "_Sesli anlatım kaydedildi; doküman bitirilince metne çevrilecek._")


def anlatim_ayikla(md_metni: str) -> dict[int, str]:
    """`### Adım N` başlıklarının altındaki anlatım metni: {adım numarası: metin}.

    Görsel satırı, API bölümü (`####` ve sonrası) ve ~~~ içi gövdeler sayılmaz;
    yer tutucular boş sayılır. Boş satırlar paragraf ayraçı olarak korunur."""
    adimlar, no, kod, ham = {}, None, False, []

    def kapat() -> None:  # son adımın birikmiş satırlarını metne çevirir
        if no is not None:
            paragraflar = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(ham)) if p.strip()]
            adimlar[no] = "\n\n".join(p for p in paragraflar if p not in YER_TUTUCULAR)

    for satir in md_metni.splitlines():
        if satir.startswith("~~~"):  # API gövdesi Rovo'nun ```markdown bloğunu erken kapatmasın diye ~~~ içinde
            kod = not kod
            continue
        if kod:
            continue
        if satir.strip().startswith("#"):  # başlık: ya yeni adım ya da anlatımın sonu
            m = re.fullmatch(r"### Adım (\d+)", satir.strip())
            kapat()
            no, ham = (int(m.group(1)), []) if m else (None, [])
            continue
        if no is None or satir.startswith("!["):  # üst alanlar ve görsel satırı sayılmaz
            continue
        ham.append(satir)  # boş satır da saklanır: paragraf ayracı
    kapat()
    return adimlar


def anlatim_bol(metin: str) -> tuple[dict[int, str], dict[str, str], set[int]]:
    """Rovo yanıtını böler: (gövdesi dolu adımlar, dolu üst alanlar, görülen Adım numaraları).

    Baş/son ``` çiti atılır; yalnız tam satır "Adım N" (başında # olabilir) başlıktır; Adım
    olmayan her başlık (grup başlığı, arka plan bölümü, "#### API çağrıları" gibi) gövdeyi
    bitirir ve kendisi yazılmaz; görsel satırı (![](... ya da tam olarak "Görsel: <tek
    sözcük>") ve "Çalışan komut:" şeridi yok sayılır; ilk Adım başlığından öncekiler üst
    alanlardır (Amaç, Aktör, Ön koşullar, Son koşullar); "…" ve boş değer yok sayılır."""
    satirlar = metin.splitlines()
    while satirlar and not satirlar[0].strip():
        satirlar.pop(0)
    while satirlar and not satirlar[-1].strip():
        satirlar.pop()
    if satirlar and satirlar[0].lstrip().startswith("```"):  # "```markdown" gibi açılış çiti
        satirlar.pop(0)
        if satirlar and satirlar[-1].strip() == "```":
            satirlar.pop()
    ham, ust, no = {}, {}, None
    for satir in satirlar:
        k = satir.strip()
        m = re.fullmatch(r"(?:#+\s*)?Adım (\d+)", k)
        if m:
            no = int(m.group(1))
            ham.setdefault(no, [])
            continue
        if k.startswith("#"):
            no = None  # Adım olmayan her başlık gövdeyi bitirir; sonraki Adım başlığına kadar yazılmaz
            continue
        if no is None:  # ilk Adım başlığından öncekiler üst alanlardır
            alan = re.fullmatch(r"- \*\*(Amaç|Aktör|Ön koşullar|Son koşullar):\*\*\s*(.*)", k)
            if alan and alan.group(2).strip() not in ("", "…"):
                ust[alan.group(1)] = alan.group(2).strip()
            continue
        if k.startswith("![") or re.fullmatch(r"Görsel: \S+", k) or k.startswith("Çalışan komut:"):
            continue  # görsel satırı ve kopyadaki komut şeridi anlatıma yazılmaz
        ham[no].append(k)
    govde = {}
    for n, liste in ham.items():
        paragraflar = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(liste)) if p.strip()]
        if paragraflar:
            govde[n] = "\n\n".join(paragraflar)
    return govde, ust, set(ham)


def anlatim_uygula(oturum: Path, metin: str) -> tuple[list[int], list[int]]:
    """Rovo'nun yalnız anlatım yanıtını .md'ye işler; (güncellenen adımlar, yanıtta olup dokümanda olmayanlar).

    Yalnız eşleşen adımın anlatımı `.md`'de değişir (görsel satırı, API bölümleri, durum grupları
    ve arka plan bölümü aynen kalır); gövdesi boş adım değişmez; üst alanlar yanıtta doluysa
    güncellenir. Önce `.md.yedek` alınır.
    Yanıtta hiç "Adım N" başlığı yoksa ValueError: dosyaya hiç yazılmaz."""
    md = md_bul(oturum)
    if md is None:
        raise ValueError(f"Dokümanda .md bulunamadı: {oturum}")
    govde, ust, basliklar = anlatim_bol(metin)
    if not basliklar:
        raise ValueError("Rovo yanıtında 'Adım N' başlığı yok; doküman değişmedi.")
    satirlar = md.read_text(encoding="utf-8").splitlines()
    mevcut = set(anlatim_ayikla("\n".join(satirlar)))
    degisti = False
    for i, satir in enumerate(satirlar):  # üst alanlar: her biri tek satır, satır sayısı değişmez
        if satir.startswith("## "):
            break
        alan = re.fullmatch(r"- \*\*(Amaç|Aktör|Ön koşullar|Son koşullar):\*\*\s*(.*)", satir.strip())
        if alan and alan.group(1) in ust:
            satirlar[i] = f"- **{alan.group(1)}:** {ust[alan.group(1)]}"
            degisti = True
    # .md'deki Adım başlıkları (~~~ içindeki metin sayılmaz)
    kod, adim_satirlari = False, []
    for i, satir in enumerate(satirlar):
        if satir.startswith("~~~"):
            kod = not kod
        elif not kod and (m := re.fullmatch(r"(?:#+\s*)?Adım (\d+)", satir.strip())):
            adim_satirlari.append((i, int(m.group(1))))
    degisiklikler = []  # (başlangıç, bitiş, yeni satırlar): soldan sağa değiştirince kayardı, tersten uygulanır
    for a, (i, no) in enumerate(adim_satirlari):
        if no not in govde or no not in mevcut:
            continue
        j = adim_satirlari[a + 1][0] if a + 1 < len(adim_satirlari) else len(satirlar)
        basla = next((k for k in range(i + 1, j) if satirlar[k].strip().startswith("![")), i + 1) + 1
        while basla < j and not satirlar[basla].strip():  # görsel satırının altındaki boşlukları at
            basla += 1
        son = next((k for k in range(basla, j) if satirlar[k].strip().startswith("#")), j)
        while son > basla and not satirlar[son - 1].strip():  # sondaki boş satırlar ayraca dönüşür
            son -= 1
        degisiklikler.append((basla, son, govde[no].split("\n") + [""]))
    for basla, son, yeni in reversed(degisiklikler):
        satirlar[basla:son] = yeni
        degisti = True
    if degisti:
        shutil.copy2(md, md.with_name(md.name + ".yedek"))
        atomik_yaz(md, "\n".join(satirlar) + "\n")
    return sorted(n for n in govde if n in mevcut), sorted(n for n in basliklar if n not in mevcut)


def gorsel_adlari(md_metni: str) -> dict[int, str]:
    """`### Adım N` başlığının bir altındaki görsel bağlantısından dosya adı: {adım: ad} (yolsuz)."""
    adlar, no = {}, None
    for satir in md_metni.splitlines():
        if m := re.fullmatch(r"### Adım (\d+)", satir.strip()):
            no = int(m.group(1))
        elif no is not None and satir.strip():
            if g := re.fullmatch(r"!\[[^\]]*\]\(([^)]+)\)", satir.strip()):
                adlar[no] = g.group(1).split("/")[-1]
            no = None  # görsel satırı başlığın hemen altındadır; başka satır aramayı durdurur
    return adlar


def calisan_komut_satirlari(md_metni: str) -> dict[int, list[str]]:
    """`#### Çalışan komutlar` bölgesindeki tablo satırları: {adım: [komut şeridi, ...]}.

    Şerit: `Çalışan komut: <geçiş satırı> · <durum> · <ne zaman> · <sıra> · <komut>`; geçiş satırı
    çağrı satırının `·` sonrası metnidir. "kayıt yok" çağrısı şerit üretmez; ~~~ gövdeleri sayılmaz."""
    komutlar, kod, no, gecis, bolumde = {}, False, None, "", False
    for satir in md_metni.splitlines():
        if satir.startswith("~~~"):
            kod = not kod
            continue
        if kod:
            continue
        k = satir.strip()
        if k.startswith("#"):
            gecis = ""
            if m := re.fullmatch(r"### Adım (\d+)", k):
                no, bolumde = int(m.group(1)), False
            elif k == "#### Çalışan komutlar":
                bolumde = True  # adım sürer; tablo satırları bu bölgede toplanır
            elif not k.startswith("####"):
                no, bolumde = None, False  # ## ya da # başlığı adım bölgesini bitirir
            else:
                bolumde = False  # "#### API çağrıları" gibi: adım sürer, bölge kapalı
            continue
        if no is None or not bolumde:
            continue
        if g := re.fullmatch(r"`[^`]+` · (.+)", k):
            gecis = g.group(1).strip()
        elif gecis and k.startswith("|") and not k.startswith("|---"):
            hucre = [h.strip() for h in k.strip("|").split("|")]
            if len(hucre) == 4 and hucre[0] != "Durum":  # tablo başlık satırı atlanır
                komutlar.setdefault(no, []).append(f"Çalışan komut: {gecis} · " + " · ".join(hucre))
    return komutlar


def anlatim_kopyasi(md_metni: str) -> str:
    """Rovo'ya verilecek yalnız anlatım: üst alan satırları + durum başlıkları adım sırasında aynen
    + her adımın başlığı, görsel adı, metni ve çalışan komut şeritleri + arka planda çalışan
    durumlar bölümü aynen. API çağrıları ve gövdeler kopyaya girmez; akışsız doküman düz kalır."""
    satirlar = md_metni.splitlines()
    ust = []
    for satir in satirlar:
        if satir.strip().startswith("## ") or re.fullmatch(r"### Adım (\d+)", satir.strip()):
            break  # "Ana akış" başlığı ve adımlar ayrı yazılır
        if not ust and not satir.strip():  # ilk başlıktan önceki boş satırları at
            continue
        ust.append(satir)
    metin = "\n".join(ust).rstrip()
    gorseller = gorsel_adlari(md_metni)
    anlatimlar = anlatim_ayikla(md_metni)
    komutlar = calisan_komut_satirlari(md_metni)
    kod, arka = False, ""  # ~~~ gövdeleri atlanır; arka plan bölümü sonda aynen eklenir
    for i, satir in enumerate(satirlar):
        if satir.startswith("~~~"):
            kod = not kod
            continue
        if kod:
            continue
        k = satir.strip()
        if k == "## Arka planda çalışan durumlar":
            arka = "\n".join(satirlar[i:]).rstrip()  # bölüm .md'deki haliyle
            break
        if k == "## Başlamadan önce" or k.startswith("## Durum: "):
            metin += f"\n\n{k}"  # grup başlığı adım sırasında aynen yazılır
        elif m := re.fullmatch(r"### Adım (\d+)", k):
            no = int(m.group(1))
            metin += f"\n\n### Adım {no}"
            if ad := gorseller.get(no):  # Rovo görseli göremese bile dosya adıyla yanlış görsele gitmesin
                metin += f"\nGörsel: {ad}"
            if anlatim := anlatimlar.get(no):
                metin += f"\n\n{anlatim}"
            if seritler := komutlar.get(no):  # kılavuz agent'ı komutu kopyadan alır
                metin += "\n\n" + "\n".join(seritler)
    if arka:
        metin += f"\n\n{arka}"
    return metin + "\n"


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
    # kod_satirlari.lua: kod satırı başına ayrı paragraf; yoksa büyük API gövdesi tek paragraf olup Word/LibreOffice açamıyor
    komut = ["pandoc", f"./{md.name}", "-f", "markdown-implicit_figures+hard_line_breaks",
             f"--lua-filter={REPO_DIZINI / 'kod_satirlari.lua'}", "-o", f"./{docx.name}"]
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
        if kip == "pencere" and dene(["gnome-screenshot", "-w", "-p", "-f", str(hedef)]):
            return True
        if dene(["gnome-screenshot", "-p", "-f", str(hedef)]):
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


def pactl(*arglar: str) -> str | None:
    """pactl çıktısı; çalışmazsa ya da hata verirse None."""
    try:
        r = subprocess.run(["pactl", *arglar], env={**os.environ, "LC_ALL": "C"}, capture_output=True,
                           text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def kart_bul(profil: str) -> tuple[str, str] | None:
    """(kart adı, aktif profil): profil listesinde `profil` geçen ilk kart."""
    for blok in (pactl("list", "cards") or "").split("Card #")[1:]:
        ad = re.search(r"^\s*Name:\s*(\S+)", blok, re.M)
        aktif = re.search(r"^\s*Active Profile:\s*(\S+)", blok, re.M)
        if ad and aktif and re.search(rf"^\s+{re.escape(profil)}:", blok, re.M):
            return ad.group(1), aktif.group(1)
    return None


def kaynak_bul(parca: str) -> str | None:
    """Adında `parca` geçen ilk giriş kaynağı; monitör (.monitor) asla seçilmez."""
    for satir in (pactl("list", "short", "sources") or "").splitlines():
        a = satir.split("\t")
        if len(a) > 1 and parca in a[1] and not a[1].endswith(".monitor"):
            return a[1]
    return None


def mikrofon_hazirla(veri: dict, ayar: dict) -> bool:
    """Kulaklığı mikrofon profiline geçirir (eski profil veri["kulaklik"]'e, yalnız ilk seferde) ve kaynağı bekler."""
    profil = ayar.get("mikrofon_profil")
    if not profil:
        return True
    kart = kart_bul(profil)
    if kart is None:
        return False
    ad, aktif = kart
    gecis = aktif != profil
    if gecis:
        veri.setdefault("kulaklik", {"kart": ad, "profil": aktif})
        if pactl("set-card-profile", ad, profil) is None:
            return False
    if ayar.get("mikrofon"):
        for _ in range(30):  # en fazla ~3 sn
            if kaynak_bul(ayar["mikrofon"]):
                break
            time.sleep(0.1)
        else:
            return False
    if gecis:
        time.sleep(1)  # kaynak göründükten sonra kısa bekleme: sinyal oturmadan kayıt başlamasın
    return True


def mikrofon_birak(veri: dict) -> None:
    """Oturum bitince kulaklığı eski profiline döndürür."""
    kulaklik = veri.pop("kulaklik", None)
    if kulaklik and pactl("set-card-profile", kulaklik["kart"], kulaklik["profil"]) is None:
        bildir(f"Kulaklık profili {kulaklik['profil']} olarak geri alınamadı; ses ayarlarından elle geri alın.")


def kayit_baslat(dosya: Path, ayar: dict) -> int | None:
    if ayar.get("mikrofon"):  # arecord'a düşülmez: varsayılan giriş monitör olabilir
        kaynak = kaynak_bul(ayar["mikrofon"])
        if not kaynak or not shutil.which("parecord"):
            return None
        komut = ["parecord", f"--device={kaynak}", "--channels=1", "--rate=16000", "--format=s16le",
                 "--file-format=wav", str(dosya)]
    elif shutil.which("arecord"):
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


# --------------------------------------------------------------- API çağrıları (HAR)

YAZAN_METOTLAR = ("POST", "PUT", "PATCH", "DELETE")  # butonla veri gönderir; diğerleri ekrana veri getirir


def zaman_damgasi() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def zaman_oku(metin: str) -> dt.datetime:
    """HAR (Firefox "+03:00", Chrome "Z") ve oturum zamanları. Python 3.10 "Z"yi ve 3/6 dışı kesir hanesini okumaz."""
    metin = re.sub(r"\.(\d+)", lambda m: "." + m.group(1)[:6].ljust(6, "0"), metin.replace("Z", "+00:00"))
    return dt.datetime.fromisoformat(metin).astimezone()


def gizle_metin(metin: str, kalip: re.Pattern) -> str:
    """JSON olmayan gövde ve sorgu: <...password...>değer ve password=değer biçimlerinde değer *** olur."""
    k = kalip.pattern
    metin = re.sub(rf"(<[\w:.-]*(?:{k})[\w:.-]*[^>]*>)[^<]*", r"\1***", metin, flags=re.I)
    return re.sub(rf"((?:{k})[\w.-]*=)[^&\s]*", r"\1***", metin, flags=re.I)


def gizle_json(deger, kalip: re.Pattern):
    """JSON: adında api_gizle'deki parçalardan biri geçen alanlar *** (iç içe)."""
    if isinstance(deger, dict):
        return {k: "***" if kalip.search(k) else gizle_json(v, kalip) for k, v in deger.items()}
    if isinstance(deger, list):
        return [gizle_json(v, kalip) for v in deger]
    return deger


def govde(metin: str, kalip: re.Pattern) -> str:
    """İstek/yanıt gövdesi dokümana kısaltılmadan: önce gizlenir, JSON düzgün yazılır."""
    if not metin.strip():
        return ""
    try:
        return json.dumps(gizle_json(json.loads(metin), kalip), ensure_ascii=False, indent=2)
    except ValueError:
        return gizle_metin(metin.strip(), kalip)


def api_turu(mime: str) -> bool:
    return bool(re.search(r"json|xml", mime, re.I)) and not re.search(r"html|svg", mime, re.I)


def api_ekle(veri: dict, girdiler: list, ayar: dict) -> int:
    """HAR girdilerini adımlara dağıtır (adim["api"]); eklenen çağrı sayısını döndürür.

    Adım N ile N+1'in çekimi arasındaki GET'in getirdiği veri N+1'in ekranında görünür; POST/PUT/…
    N'deki butonla gider. basla–bitir dışındaki çağrılar (Ağ sekmesinin eski kaydı) atılır.
    İstek/yanıt başlıkları (Authorization, Cookie…) dokümana hiç yazılmaz."""
    adimlar = veri["adimlar"]
    zamanlar = [zaman_oku(a["zaman"]) for a in adimlar]
    bas, son = zaman_oku(veri["baslangic"]), zaman_oku(veri["bitis"])
    filtre = ayar.get("api_filtre") or []
    kalip = re.compile("|".join(map(re.escape, ayar.get("api_gizle") or [])) or "(?!)", re.I)
    for adim in adimlar:
        adim["api"] = []
    gorulen, sayi = set(), 0
    for zaman, g in sorted(((zaman_oku(g["startedDateTime"]), g) for g in girdiler), key=lambda x: x[0]):
        istek, yanit = g["request"], g["response"]
        gonderilen, icerik = istek.get("postData") or {}, yanit.get("content") or {}
        if filtre:
            uygun = any(p in istek["url"] for p in filtre)
        else:
            uygun = api_turu(gonderilen.get("mimeType", "")) or api_turu(icerik.get("mimeType", ""))
        if not uygun or not yanit.get("status") or not bas <= zaman <= son:  # status 0: iptal/engellenmiş
            continue
        metot, k = istek["method"].upper(), bisect.bisect_right(zamanlar, zaman)
        yazan = metot in YAZAN_METOTLAR
        sira = min(max(k - 1, 0) if yazan else k, len(adimlar) - 1)
        url = urlsplit(istek["url"])
        uc = gizle_metin(url.path + (f"?{url.query}" if url.query else ""), kalip).replace("|", "%7C")
        istek_metni = gonderilen.get("text") or ""
        if (sira, metot, uc, istek_metni) in gorulen:  # aynı ekranda tekrarlanan çağrı (yoklama vb.) tek satır
            continue
        gorulen.add((sira, metot, uc, istek_metni))
        yanit_metni = icerik.get("text") or ""
        if icerik.get("encoding") == "base64":
            yanit_metni = base64.b64decode(yanit_metni).decode("utf-8", "replace")
        adimlar[sira]["api"].append({
            "yon": "Butonla giden" if yazan else "Ekrana gelen", "metot": metot, "uc": uc,
            "durum": yanit["status"], "istek": govde(istek_metni, kalip),
            "yanit": govde(yanit_metni, kalip), "akis": is_akisi(istek_metni, yanit_metni)})
        sayi += 1
    return sayi


# İş akışı çağrısı: istekte mevcut durum ve değişim bayrağı, yanıtta sonraki durum
AKIS_ALANLARI = ("currentWorkFlowStateShortCode", "workFlowStateChange", "nextWorkFlowStateShortCode")
ASAMA = {"pre": "girişte (pre)", "ic": "durum içi (during)", "post": "çıkışta (post)"}


def is_akisi(istek: str, yanit: str) -> dict | None:
    try:
        i, y = json.loads(istek), json.loads(yanit or "{}")
    except ValueError:
        return None
    if not isinstance(i, dict) or AKIS_ALANLARI[0] not in i:
        return None
    return {"mevcut": i[AKIS_ALANLARI[0]], "degisim": bool(i.get(AKIS_ALANLARI[1])),
            "sonraki": y.get(AKIS_ALANLARI[2]) if isinstance(y, dict) else None}


def cagri_akisi(c: dict, ayar: dict) -> dict | None:
    """Çağrının iş akışı geçişi: kayda yazılan `akis` varsa o; yoksa sabit geçişten çıkarılır.

    `sabit_gecisler`'de sorgusuz uc'ünde parçası geçen yazan çağrı, [mevcut, sonraki]
    elemanlı o geçişi yapmış sayılır: {"mevcut", "degisim": True, "sonraki", "sabit": True}.
    Sonuç kayda yazılmaz; eski dokümanlar HAR'sız çalışır."""
    if c.get("akis"):
        return c["akis"]
    if not ayar.get("sabit_gecisler") or c["metot"] not in YAZAN_METOTLAR:
        return None
    sorgusuz = c["uc"].split("?", 1)[0]
    for parca, gecis in ayar["sabit_gecisler"].items():
        if parca in sorgusuz:
            return {"mevcut": gecis[0], "degisim": True, "sonraki": gecis[1], "sabit": True}
    return None


def komut_tablosu_oku(metin: str) -> tuple:
    """Veritabanı aracının çıktısı → (akışlar, satırlar). DBeaver: Ctrl+C (sekme), CSV, TXT ve Markdown (|);
    başlık ve ayraç satırları atlanır. İlk iki sütun akış ve durum; son dördü bean_name, is_pre, is_post, sort_id."""
    akislar, tablo = set(), []
    for satir in metin.splitlines():
        a = [x for x in re.split(r'[\s|,;"]+', satir) if x]
        if len(a) < 6 or not a[-1].isdigit():
            continue
        pre, post = (x.lower() in ("1", "true") for x in a[-3:-1])
        akislar.add(a[0])
        tablo.append({"durum": a[1], "asama": "pre" if pre else "post" if post else "ic",
                      "sira": int(a[-1]), "komut": a[-4]})
    return akislar, tablo


def calisan_komutlar(tablo: list, akis: dict) -> list:
    """Durum değişiyorsa mevcut durumun post'u, sonra sonraki durumun pre'si (sonraki duruma girerken);
    değişmiyorsa mevcut durumun during komutları (pre/post olmayan: durum atlamadan yapılan işlemler,
    ör. ekrandaki güncelleme çağrıları; asenkron durumlar da böyle tetiklenir). Grup içinde sort_id sırası."""
    secim = [(akis["mevcut"], "post"), (akis["sonraki"], "pre")] if akis["degisim"] else [(akis["mevcut"], "ic")]
    return [k for durum, asama in secim
            for k in sorted((k for k in tablo if k["durum"] == durum and k["asama"] == asama), key=lambda k: k["sira"])]


def adim_durumlari(adimlar: list, ayar: dict) -> list:
    """Adımların iş akışı durumu (workflow state); baştan tek ileri geçişle hesaplanır.

    Adımın durumu gerçek akışının (HAR'da iş akışı alanlarıyla kaydedilen) `mevcut`udur;
    akışı olmayan adım süren durumu taşır, başta durum yoktur (None). Sabit çağrı
    (initialize/submit gibi uçlarıyla bilinen geçiş) adımın durumunu değiştirmez, sonrasını
    taşır: çağrının `mevcut`u son ekran durumundaysa `mevcut` sürer (ekran sınırı), değilse
    `sonraki`ye geçilir. Gerçek geçiş `degisim` + `sonraki` ile sonraki adımları taşır; süren
    durum son ekran durumundayken durum değişmez (arka planda çalışan durumlar)."""
    sinir = ayar.get("son_ekran_durumu") or ""
    durums = []
    durum = None
    for adim in adimlar:
        akislari = [k for c in (adim.get("api") or []) if (k := cagri_akisi(c, ayar))]
        if gercek := next((k for k in akislari if not k.get("sabit")), None):
            durum = gercek["mevcut"]  # adımın durumu kendi gerçek akışının mevcutu önceliklidir
        durums.append(durum)
        for k in akislari:  # geçişler adım sonunda değerlendirilir, sonraki adımları taşır
            if k.get("sabit"):
                durum = k["mevcut"] if (sinir and k["mevcut"] == sinir) else k["sonraki"]
            elif k["degisim"] and k["sonraki"] and not (sinir and durum == sinir):
                durum = k["sonraki"]
    return durums


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
    veri = {"baslik": baslik, "dosya": dosya_adi(baslik), "tarih": f"{simdi:%d.%m.%Y}",
            "mod": "ses" if args.ses else "yazi", "adimlar": [], "kayit_pid": None,
            "baslangic": zaman_damgasi()}
    if args.ses and ayar.get("mikrofon"):  # klasör açılmadan önce: hata varsa oturum oluşmaz
        if not shutil.which("parecord"):
            bildir("Mikrofon ayarı için parecord gerekli: sudo apt install pulseaudio-utils")
            return 1
        if not (mikrofon_hazirla(veri, ayar) and kaynak_bul(ayar["mikrofon"])):
            mikrofon_birak(veri)
            bildir(f"Mikrofon ({ayar['mikrofon']}) hazırlanamadı; kulaklık bağlı mı? Oturum başlatılmadı.")
            return 1
    (oturum / "gorseller").mkdir(parents=True, exist_ok=True)
    if args.ses:
        (oturum / "ses").mkdir(exist_ok=True)
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
                "ses": None, "ses_metni": None, "not": "", "zaman": zaman_damgasi()}  # zaman: API çağrılarını eşler
        if not ekran_goruntusu(oturum / adim["gorsel"], "tam" if args.tam else ayar.get("ekran", "pencere")):
            bildir("Ekran görüntüsü alınamadı. Kurulu mu: sudo apt install gnome-screenshot")
            return 1
        sessiz = False
        if veri["mod"] == "ses":
            kayit_durdur(veri.get("kayit_pid"))  # önceki adımın anlatımı burada biter
            adim["ses"] = f"ses/adim-{no:02d}.wav"
            hazir = mikrofon_hazirla(veri, ayar)  # Bluetooth düşüp geri geldiyse yeniden alır
            veri["kayit_pid"] = kayit_baslat(oturum / adim["ses"], ayar) if hazir else None
            if veri["kayit_pid"] is None:
                adim["ses"], sessiz = None, True
        veri["adimlar"].append(adim)
        kaydet(oturum, veri)
    if veri["mod"] == "ses":
        if sessiz:
            bildir(f"Mikrofon bulunamadı, bu adımın sesi kaydedilmedi (adım {no}).")
        else:
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
        mikrofon_birak(veri)
        veri["kayit_pid"], veri["bitis"] = None, zaman_damgasi()
        kaydet(oturum, veri)
        AKTIF.unlink(missing_ok=True)
        SON.write_text(str(oturum), encoding="utf-8")
    if veri["mod"] == "ses":
        try:
            yaziya_dok(oturum, veri, ayar)
        except Exception as hata:  # model indirilemedi vb. — doküman yine de üretilsin
            bildir(f"Ses metne çevrilemedi: {hata}")
    word_uret(oturum)
    if not os.environ.get("ADIMADIM_ARAYUZ"):  # pencere kendi bitiş ekranını gösterir
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
    for adim in veri["adimlar"]:
        adim.pop("metin", None)  # eski .md düzeltmesi değil, yeni çeviri yazılmalı
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


def cmd_api(args, ayar) -> int:
    """Tarayıcının Ağ sekmesinden kaydedilen HAR'daki API çağrılarını bitmiş dokümanın adımlarına ekler."""
    oturum, veri = bitmis_dokuman(args.klasor)
    if not oturum:
        return 1
    if not veri["adimlar"] or not veri.get("bitis") or any("zaman" not in a for a in veri["adimlar"]):
        bildir("Bu dokümanda çekim zamanları yok (v0.8.0'dan önce kaydedilmiş); API çağrıları eklenemez.")
        return 1
    try:
        sayi = api_ekle(veri, json.loads(Path(args.har).expanduser().read_text(encoding="utf-8"))["log"]["entries"], ayar)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as hata:
        bildir(f"HAR okunamadı: {hata}")
        return 1
    if not sayi:
        bildir("HAR'da bu dokümanın başla–bitir aralığında API çağrısı yok. Ağ sekmesi ilk ekrandan önce açık "
               "olmalı; yalnızca JSON/XML çağrılar alınır (bkz. api_filtre ayarı).")
        return 1
    yeniden_yaz(oturum, veri)
    bildir(f"{sayi} API çağrısı adımlara eklendi.")
    return 0


def cmd_komutlar(args, ayar) -> int:
    """Durumlarda çalışan komutların tablosunu yükler; iş akışı çağrılarının altında gösterilir."""
    oturum, veri = bitmis_dokuman(args.klasor)
    if not oturum:
        return 1
    try:
        akislar, tablo = komut_tablosu_oku(Path(args.tablo).expanduser().read_text(encoding="utf-8-sig"))
    except OSError as hata:
        bildir(f"Komut tablosu okunamadı: {hata}")
        return 1
    if not tablo:
        bildir("Komut tablosunda satır yok. Sütunlar: akış, durum, …, bean_name, is_pre, is_post, sort_id "
               "(DBeaver: Ctrl+C ya da CSV/TXT dışa aktarma).")
        return 1
    if len(akislar) > 1:
        bildir(f"Tabloda birden çok akış var ({', '.join(sorted(akislar))}); yalnızca bu dokümanın akışını yükle.")
        return 1
    veri["komutlar"] = tablo
    yeniden_yaz(oturum, veri)
    cagri = sum(1 for a in veri["adimlar"] for c in a.get("api") or [] if c.get("akis"))
    bildir(f"Komut tablosu yüklendi: {len(tablo)} komut, {cagri} iş akışı çağrısı."
           + ("" if cagri else " Komutlar iş akışı çağrılarının altına yazılır: önce 'API ekle (HAR)'."))
    return 0


def bitmis_dokuman(klasor: str | None) -> tuple:
    """(oturum, veri); doküman yoksa ya da hâlâ açıksa bildirip (None, None)."""
    oturum = klasor_sec(klasor)
    if not oturum or not (oturum / "oturum.json").exists():
        bildir(f"Doküman bulunamadı: {oturum}")
        return None, None
    if aktif_oturum() == oturum:
        bildir("Bu doküman hâlâ açık; önce: adimadim bitir")
        return None, None
    return oturum, yukle(oturum)


def yeniden_yaz(oturum: Path, veri: dict) -> None:
    """Bitmiş dokümanın .md'sini oturum.json'dan (öncekini .md.yedek'e alarak) ve Word'ü yeniden üretir.

    Üretimden önce .md'deki anlatım adim["metin"]'e, dolu üst alanlar veri["ust"]'e alınır:
    Rovo ve elle yapılan düzeltmeler API ekle/komut tablosu sonrasındaki üretimde kaybolmaz."""
    md = md_bul(oturum)
    if md:  # .md'de elle yapılan düzeltmeler kaybolmasın
        onceki = md.read_text(encoding="utf-8")
        anlatim = anlatim_ayikla(onceki)
        for no, adim in enumerate(veri["adimlar"], 1):
            if anlatim.get(no):
                adim["metin"] = anlatim[no]
        ust = {}
        for satir in onceki.splitlines():
            if satir.startswith("## "):
                break  # "## Ana akış"a kadarki üst alan satırları
            m = re.fullmatch(r"- \*\*(Amaç|Aktör|Ön koşullar|Son koşullar):\*\*\s*(.*)", satir.strip())
            if m and m.group(2).strip() not in ("", "…"):
                ust[m.group(1)] = m.group(2).strip()
        if ust:
            veri["ust"] = ust
        shutil.copy2(md, md.with_name(md.name + ".yedek"))
        print(f"Önceki metin yedeklendi: {md.name}.yedek")
    kaydet(oturum, veri)
    word_uret(oturum)


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
    p = alt.add_parser("cek", help="ekran görüntüsü al, yeni adım ekle (Ctrl+Alt+S)")
    p.add_argument("--tam", action="store_true", help="ayardan bağımsız tüm ekranı çek (bölge seçimi için)")
    alt.add_parser("not", help="son adımın notunu yaz/düzenle (Ctrl+Alt+N)")
    alt.add_parser("geri", help="son adımı sil")
    alt.add_parser("durum", help="açık dokümanı göster")
    alt.add_parser("bitir", help="bitir; .md ve .docx üret")
    p = alt.add_parser("word", help="düzenlenmiş .md'den .docx'i yeniden üret")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("yeniden", help="bir dokümanın ses kayıtlarını baştan metne çevir")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("api", help="tarayıcının Ağ sekmesinden kaydedilen API çağrılarını (HAR) adımlara ekle")
    p.add_argument("har", help="Firefox: F12 → Ağ → sağ tık → Tümünü HAR olarak kaydet")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("komutlar", help="durumlarda çalışan komutların tablosunu yükle (iş akışı çağrılarının altına)")
    p.add_argument("tablo", help="DBeaver çıktısı: CSV, TXT, Markdown ya da kopyalanan (sekme ayraçlı) metin")
    p.add_argument("klasor", nargs="?", help="doküman klasörü (varsayılan: en son biten)")
    p = alt.add_parser("cevir", help="ses dosyalarını metne çevirip ekrana yaz")
    p.add_argument("dosyalar", nargs="+", help="16 kHz mono WAV dosyaları")
    alt.add_parser("kisayol", help="GNOME klavye kısayollarını tanımla")
    alt.add_parser("arayuz", help="düğmeli pencereyi aç")
    args = ap.parse_args(argv)
    komutlar = {"basla": cmd_basla, "cek": cmd_cek, "not": cmd_not, "geri": cmd_geri,
                "durum": cmd_durum, "bitir": cmd_bitir, "word": cmd_word, "yeniden": cmd_yeniden, "api": cmd_api, "komutlar": cmd_komutlar,
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
