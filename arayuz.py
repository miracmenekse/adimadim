"""adımadım penceresi: komutları düğmelerle çalıştırır, terminal gerekmez.

Üç ekran: Başla → Kayıt (çekilen ekranların önizlemesi) → Bitiş (dokümanın önizlemesi).
Her düğme `adimadim.py <komut>`u ayrı süreçte çalıştırır (kilit, not penceresi, çeviri aynı kalır);
pencere oturum.json'a bakıp durumu gösterir. Süren işlem varsa bekleme çubuğu görünür.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import math
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog, ttk

import adimadim as a

GUNLUK = a.AYAR_DIZINI / "arayuz.log"  # son komutun çıktısı; sorun olursa buna bakılır
BEKLEME = {  # komut → beklerken gösterilecek açıklama
    "basla": "Doküman açılıyor",
    "cek": "Ekran çekiliyor",
    "not": "Not penceresi açık",
    "geri": "Son adım siliniyor",
    "bitir": "Doküman hazırlanıyor (sesli modda anlatımlar metne çevriliyor, birkaç dakika sürebilir)",
    "word": "Word dosyası yeniden üretiliyor",
    "yeniden": "Ses kayıtları baştan metne çevriliyor (birkaç dakika sürebilir)",
    "api": "API çağrıları adımlara ekleniyor",
    "komutlar": "Komut tablosu yükleniyor",
}


def son_satir() -> str:
    """Günlükteki son anlamlı satır (uyarılar atlanır)."""
    try:
        satirlar = GUNLUK.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return next((s.strip() for s in reversed(satirlar) if s.strip() and "Warning" not in s), "")[:200]


def ipucu(veri: dict, kayit: bool) -> str:
    """Kayıt ekranında o anki duruma göre ne yapılacağı."""
    if not veri["adimlar"]:
        return "Adım 0: belgeleyeceğin ilk ekrana geç ve Ctrl+Alt+S'ye bas (ya da 'Ekranı çek')."
    if kayit:
        return "Görsele tıkla: kırp / işaretle. Anlatman kaydediliyor. Cümleni bitir, sonraki ekrana geç, Ctrl+Alt+S. Son ekrandan sonra 'Bitir'."
    return "Sonraki ekrana geç, Ctrl+Alt+S. Hepsi bitince 'Bitir'."


def mtime(yol: Path) -> float:
    try:
        return yol.stat().st_mtime
    except OSError:
        return 0.0


def kucult(yol: Path, genislik: int) -> tk.PhotoImage | None:
    """PNG'yi yaklaşık `genislik` piksele küçültür (Tk yalnızca tam sayı oranla küçültür)."""
    try:
        resim = tk.PhotoImage(file=str(yol))
    except tk.TclError:
        return None
    oran = max(1, -(-resim.width() // genislik))
    return resim.subsample(oran) if oran > 1 else resim


YAZI_TIPI = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # fonts-dejavu-core (kur.sh)
KIRMIZI = "#e53935"


def isaretleri_uygula(yol: Path, isaretler: list) -> None:
    """İşaretleri (görselin kendi piksel koordinatlarında) çizer, kırpma varsa en son kırpar.
    İlk düzenlemede orijinal görsel gorseller/.orijinal/ altına saklanır."""
    from PIL import Image, ImageDraw, ImageFont
    yedek = yol.parent / ".orijinal" / yol.name
    if not yedek.exists():
        yedek.parent.mkdir(exist_ok=True)
        shutil.copy2(yol, yedek)
    resim = Image.open(yol).convert("RGB")
    ciz = ImageDraw.Draw(resim)
    kalin = max(3, resim.width // 400)
    try:
        yazi_tipi = ImageFont.truetype(YAZI_TIPI, max(18, resim.height // 35))
    except OSError:
        yazi_tipi = ImageFont.load_default()
    kirp = None
    for tur, k, metin in isaretler:
        if tur == "kirp":
            kirp = (min(k[0], k[2]), min(k[1], k[3]), max(k[0], k[2]), max(k[1], k[3]))
        elif tur == "kutu":
            ciz.rectangle((min(k[0], k[2]), min(k[1], k[3]), max(k[0], k[2]), max(k[1], k[3])),
                          outline=KIRMIZI, width=kalin)
        elif tur == "ok":
            ciz.line(k, fill=KIRMIZI, width=kalin)
            aci, boy = math.atan2(k[3] - k[1], k[2] - k[0]), kalin * 6
            ciz.polygon([(k[2], k[3])] + [(k[2] - boy * math.cos(aci + d), k[3] - boy * math.sin(aci + d))
                                           for d in (0.45, -0.45)], fill=KIRMIZI)
        elif tur == "yazi":
            ciz.text((k[0], k[1]), metin, fill=KIRMIZI, font=yazi_tipi, stroke_width=2, stroke_fill="white")
    if kirp and kirp[2] - kirp[0] > 5 and kirp[3] - kirp[1] > 5:
        resim = resim.crop(kirp)
    resim.save(yol)


class Duzenleyici(tk.Toplevel):
    """Görseli kırpma ve işaretleme penceresi (kutu, ok, yazı). Kaydet görseli yerinde değiştirir."""

    def __init__(self, ust, yol: Path, arac: str = "kutu", bitince=None):
        from PIL import Image, ImageTk
        super().__init__(ust)
        self.yol, self.bitince, self.isaretler, self.cizim = yol, bitince, [], None
        self.title(f"Kırp / işaretle: {yol.name}")
        self.attributes("-topmost", True)
        resim = Image.open(yol)
        self.oran = min(1.0, self.winfo_screenwidth() * 0.9 / resim.width,
                        self.winfo_screenheight() * 0.75 / resim.height)
        self.foto = ImageTk.PhotoImage(resim.resize((int(resim.width * self.oran), int(resim.height * self.oran))))
        ust_cubuk = ttk.Frame(self, padding=4)
        ust_cubuk.pack(fill="x")
        self.arac = tk.StringVar(value=arac)
        for metin, deger in (("Kırp", "kirp"), ("Kutu", "kutu"), ("Ok", "ok"), ("Yazı", "yazi")):
            ttk.Radiobutton(ust_cubuk, text=metin, variable=self.arac, value=deger).pack(side="left", padx=4)
        ttk.Button(ust_cubuk, text="Kaydet", command=self.kaydet).pack(side="right", padx=2)
        ttk.Button(ust_cubuk, text="Vazgeç", command=self.destroy).pack(side="right", padx=2)
        ttk.Button(ust_cubuk, text="Geri al", command=self.geri_al).pack(side="right", padx=2)
        ttk.Label(self, text="Kırp/Kutu/Ok: sürükle · Yazı: tıkla, yazını gir · Kaydet'e basınca görsel değişir "
                             "(orijinali gorseller/.orijinal/ altında saklanır)", foreground="#666").pack(anchor="w", padx=6)
        self.tuval = tk.Canvas(self, width=self.foto.width(), height=self.foto.height(), cursor="crosshair",
                               highlightthickness=0)
        self.tuval.pack(padx=6, pady=6)
        self.tuval.create_image(0, 0, image=self.foto, anchor="nw")
        self.tuval.bind("<ButtonPress-1>", self.bas)
        self.tuval.bind("<B1-Motion>", self.surukle)
        self.tuval.bind("<ButtonRelease-1>", self.birak)
        self.bind("<Control-z>", lambda _: self.geri_al())
        self.bind("<Return>", lambda _: self.kaydet())
        self.bind("<Escape>", lambda _: self.destroy())

    def gercek(self, *k: float) -> tuple:
        return tuple(round(v / self.oran) for v in k)

    def bas(self, olay) -> None:
        tur = self.arac.get()
        if tur == "yazi":
            metin = simpledialog.askstring("Yazı", "Görsele yazılacak metin:", parent=self)
            if metin:
                oge = self.tuval.create_text(olay.x, olay.y, text=metin, anchor="nw", fill=KIRMIZI,
                                             font=("", 14, "bold"))
                self.isaretler.append(("yazi", self.gercek(olay.x, olay.y), metin, [oge]))
            return
        if tur == "ok":
            oge = self.tuval.create_line(olay.x, olay.y, olay.x, olay.y, fill=KIRMIZI, width=3, arrow="last")
        else:
            oge = self.tuval.create_rectangle(olay.x, olay.y, olay.x, olay.y, width=2 if tur == "kirp" else 3,
                                              outline="#1e88e5" if tur == "kirp" else KIRMIZI,
                                              dash=(6, 4) if tur == "kirp" else None)
        self.cizim = (tur, olay.x, olay.y, oge)

    def surukle(self, olay) -> None:
        if self.cizim:
            _, x, y, oge = self.cizim
            self.tuval.coords(oge, x, y, olay.x, olay.y)

    def birak(self, olay) -> None:
        if not self.cizim:
            return
        tur, x, y, oge = self.cizim
        self.cizim = None
        if abs(olay.x - x) < 5 and abs(olay.y - y) < 5:  # tıklama, çizim değil
            self.tuval.delete(oge)
            return
        if tur == "kirp":  # tek kırpma alanı: öncekini kaldır
            for eski in [i for i in self.isaretler if i[0] == "kirp"]:
                self.isaretler.remove(eski)
                self.tuval.delete(*eski[3])
        self.isaretler.append((tur, self.gercek(x, y, olay.x, olay.y), "", [oge]))

    def geri_al(self) -> None:
        if self.isaretler:
            self.tuval.delete(*self.isaretler.pop()[3])

    def kaydet(self) -> None:
        if self.isaretler:
            isaretleri_uygula(self.yol, [i[:3] for i in self.isaretler])
        self.destroy()
        if self.bitince:
            self.bitince()


def dugmeler(ust, satirlar) -> None:
    """Düğme sırası; her düğmenin altında ne işe yaradığı."""
    for sira, (metin, komut, aciklama) in enumerate(satirlar):
        ttk.Button(ust, text=metin, command=komut).grid(row=0, column=sira, sticky="we", padx=2)
        ttk.Label(ust, text=aciklama, foreground="#666", font=("", 8)).grid(row=1, column=sira, padx=2)


class Pencere:
    def __init__(self, kok: tk.Tk):
        self.kok, self.surec, self.calisan, self.bas_zamani = kok, None, None, 0.0
        self.bitmis: Path | None = None  # bitiş ekranında gösterilen doküman
        self.resimler, self.onizlenen, self.md_imza, self.ekran, self.sonra = [], None, None, None, None
        kok.title(a.UYGULAMA)
        c = ttk.Frame(kok, padding=10)
        c.pack(fill="both", expand=True)
        c.columnconfigure(0, weight=1)
        c.rowconfigure(1, weight=1)

        # --- Başla ekranı
        self.basla_f = f = ttk.Frame(c)
        ttk.Label(f, text="Yeni dokümanın adı", font=("", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        self.baslik = tk.StringVar()
        giris = ttk.Entry(f, textvariable=self.baslik, width=50)
        giris.grid(row=1, column=0, columnspan=3, sticky="we", pady=4)
        giris.bind("<Return>", lambda _: self.basla())
        self.mod = tk.StringVar(value="ses")
        ttk.Radiobutton(f, text="Sesli anlatım (konuşarak)", variable=self.mod, value="ses").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(f, text="Yazılı not (her ekranda yazarak)", variable=self.mod, value="yazi").grid(row=2, column=1, sticky="w")
        ttk.Button(f, text="Başla", command=self.basla).grid(row=2, column=2, sticky="e", padx=(10, 0))

        # --- Kayıt ekranı: başlık, çekilen ekranların şeridi, düğmeler
        self.kayit_f = f = ttk.Frame(c)
        f.columnconfigure(0, weight=1)
        self.kayit_baslik = ttk.Label(f, font=("", 11, "bold"))
        self.kayit_baslik.grid(row=0, column=0, sticky="w")
        self.kayit_isaret = tk.Label(f, text="● KAYIT", fg="#c62828", font=("", 10, "bold"))
        self.tuval = tk.Canvas(f, height=150, width=640, highlightthickness=0)
        kaydir = ttk.Scrollbar(f, orient="horizontal", command=self.tuval.xview)
        self.tuval.configure(xscrollcommand=kaydir.set)
        self.serit = ttk.Frame(self.tuval)
        self.tuval.create_window(0, 0, window=self.serit, anchor="nw")
        self.serit.bind("<Configure>", lambda _: self.tuval.configure(scrollregion=self.tuval.bbox("all")))
        self.tuval.grid(row=1, column=0, columnspan=2, sticky="we", pady=4)
        kaydir.grid(row=2, column=0, columnspan=2, sticky="we")
        d = ttk.Frame(f)
        d.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        dugmeler(d, (("Ekranı çek", self.cek, "Ctrl+Alt+S ile aynı"),
                     ("Bölge çek", lambda: self.cek(bolge=True), "Alanı seç, işaretle"),
                     ("Son adıma not yaz", lambda: self.calistir("not"), "Son ekrana yazılı açıklama ekler"),
                     ("Son adımı sil", lambda: self.calistir("geri"), "Yanlış çekilen son ekranı siler"),
                     ("Bitir", lambda: self.calistir("bitir"), "Dokümanı üretir")))

        # --- Bitiş ekranı: dokümanın önizlemesi ve sonrası
        self.bitis_f = f = ttk.Frame(c)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        self.bitis_baslik = ttk.Label(f, font=("", 11, "bold"))
        self.bitis_baslik.grid(row=0, column=0, sticky="w")
        self.onizleme = tk.Text(f, width=80, height=18, wrap="word", relief="flat", padx=8, pady=8,
                                font=("", 10))
        self.onizleme.tag_configure("baslik", font=("", 12, "bold"), spacing1=8)
        yukari = ttk.Scrollbar(f, command=self.onizleme.yview)
        self.onizleme.configure(yscrollcommand=yukari.set)
        self.onizleme.grid(row=1, column=0, sticky="nsew", pady=4)
        yukari.grid(row=1, column=1, sticky="ns")
        r = ttk.Frame(f)
        r.grid(row=3, column=0, columnspan=2, sticky="we", pady=(6, 0))
        r.columnconfigure(0, weight=1)
        ttk.Label(r, text="Rovo çıktısını buraya yapıştır (Ctrl+V): .md ve Word kendiliğinden güncellenir",
                  font=("", 9, "bold")).grid(row=0, column=0, sticky="w")
        self.rovo = tk.Text(r, height=4, wrap="word", font=("", 9))
        self.rovo.grid(row=1, column=0, sticky="we")
        self.rovo.bind("<<Paste>>", lambda _: self.kok.after(100, self.rovo_uygula))
        ttk.Button(r, text="Uygula", command=self.rovo_uygula).grid(row=1, column=1, sticky="ns", padx=(4, 0))
        d = ttk.Frame(f)
        d.grid(row=2, column=0, columnspan=2, sticky="w")
        dugmeler(d, (("MD'yi kopyala", self.md_kopyala, "Rovo'ya yapıştırmak için"),
                     ("Word'ü aç", lambda: self.ac(".docx"), "Hazır Word dosyası"),
                     ("Klasörü aç", lambda: self.ac(""), "Görseller, sesler, .md"),
                     ("Word'ü yenile", lambda: self.calistir("word", str(self.bitmis)), ".md'yi elle düzelttiysen"),
                     ("Sesi baştan çevir", lambda: self.calistir("yeniden", str(self.bitmis)), "Metni sesten yeniden yazar"),
                     ("API ekle (HAR)", self.api_ekle, "Tarayıcının Ağ kaydı"),
                     ("Komut tablosu", self.komutlar_yukle, "Panodan ya da CSV/TXT"),
                     ("Yeni doküman", self.yeni, "")))

        # --- Her ekranda: bekleme çubuğu ve ipucu
        self.bekle_f = f = ttk.Frame(c)
        self.bekle_cubuk = ttk.Progressbar(f, mode="indeterminate", length=160)
        self.bekle_cubuk.grid(row=0, column=0, padx=(0, 8))
        self.bekle_yazi = ttk.Label(f, font=("", 10, "bold"), foreground="#1565c0", wraplength=560)
        self.bekle_yazi.grid(row=0, column=1, sticky="w")
        self.bekle_ayrinti = ttk.Label(f, foreground="#666", wraplength=740)
        self.bekle_ayrinti.grid(row=1, column=0, columnspan=2, sticky="w")
        self.ipucu = ttk.Label(c, foreground="#555", wraplength=740)
        self.ipucu.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.guncelle()

    # ------------------------------------------------------------ işlemler
    def calistir(self, *komut: str) -> None:
        if self.surec:
            return
        self.calisan, self.bas_zamani = komut[0], time.time()
        # Çıktı dosyaya: boru dolarsa (model yüklenirken uzun çıktı) komut da pencere de takılırdı.
        with open(GUNLUK, "w", encoding="utf-8") as g:
            self.surec = subprocess.Popen([sys.executable, str(a.REPO_DIZINI / "adimadim.py"), *komut],
                                          stdout=g, stderr=subprocess.STDOUT,
                                          env={**os.environ, "ADIMADIM_ARAYUZ": "1"})
        self.bekle_cubuk.start(15)
        self.guncelle(tekrar=False)

    def basla(self) -> None:
        baslik = self.baslik.get().strip()
        if not baslik:
            self.ipucu["text"] = "Önce dokümanın adını yaz."
            return
        self.bitmis = None
        self.calistir("basla", baslik, *(["--ses"] if self.mod.get() == "ses" else []))

    def cek(self, bolge: bool = False) -> None:
        if self.surec:
            return
        self.kok.withdraw()  # "pencere" kipinde arayüzün kendisi çekilmesin: odak önceki pencereye döner
        if bolge:  # tüm ekranı çek, sonra düzenleyicide kırp
            self.sonra = lambda: self.duzenle(-1, "kirp")
        self.kok.after(400, lambda: self.calistir("cek", *(["--tam"] if bolge else [])))

    def duzenle(self, sira: int, arac: str = "kutu") -> None:
        oturum = a.aktif_oturum()
        adimlar = a.yukle(oturum)["adimlar"] if oturum else []
        if adimlar and not self.surec:
            Duzenleyici(self.kok, oturum / adimlar[sira]["gorsel"], arac, bitince=lambda: self.guncelle(tekrar=False))

    def md_kopyala(self) -> None:
        md = a.md_bul(self.bitmis) if self.bitmis else None
        if md:
            self.kok.clipboard_clear()
            self.kok.clipboard_append(md.read_text(encoding="utf-8"))
            self.ipucu["text"] = "Kopyalandı. Rovo'ya yapıştır, çıktısını aşağıdaki alana yapıştır."

    def rovo_uygula(self) -> None:
        """Rovo çıktısını .md'ye yazar (öncekini .md.yedek'e alır), sonra Word'ü yeniler."""
        metin = self.rovo.get("1.0", "end").strip()
        metin = re.sub(r"^```[a-z]*\n|\n```$", "", metin).strip()  # Rovo tek kod bloğu döndürür
        md = a.md_bul(self.bitmis) if self.bitmis else None
        if not metin or not md or self.surec:
            return
        shutil.copy2(md, md.with_name(md.name + ".yedek"))
        md.write_text(metin + "\n", encoding="utf-8")
        self.rovo.delete("1.0", "end")
        self.calistir("word", str(self.bitmis))

    def api_ekle(self) -> None:
        har = filedialog.askopenfilename(parent=self.kok, title="Ağ sekmesinden kaydedilen HAR dosyası",
                                         initialdir=a.belgeler_dizini("DOWNLOAD"),
                                         filetypes=[("HAR", "*.har"), ("Tümü", "*")])
        if har and self.bitmis:
            self.calistir("api", har, str(self.bitmis))

    def komutlar_yukle(self) -> None:
        """Komut tablosu: panoda tablo varsa (DBeaver'da Ctrl+A, Ctrl+C) o, yoksa dışa aktarılmış dosya."""
        if not self.bitmis or self.surec:
            return
        try:
            metin = self.kok.clipboard_get()
        except tk.TclError:  # pano boş
            metin = ""
        if a.komut_tablosu_oku(metin)[1]:
            dosya = self.bitmis / "komut_tablosu.txt"
            dosya.write_text(metin, encoding="utf-8")
        else:
            dosya = filedialog.askopenfilename(parent=self.kok, title="Komut tablosu (DBeaver çıktısı)",
                                               filetypes=[("CSV, TXT, Markdown", "*.csv *.txt *.md"), ("Tümü", "*")])
            if not dosya:
                return
        self.calistir("komutlar", str(dosya), str(self.bitmis))

    def ac(self, uzanti: str) -> None:
        md = a.md_bul(self.bitmis) if self.bitmis else None
        hedef = md.with_suffix(uzanti) if md and uzanti else self.bitmis
        if hedef and hedef.exists():
            a.klasoru_ac(hedef)
        else:
            self.ipucu["text"] = f"Bulunamadı: {hedef}"

    def yeni(self) -> None:
        self.bitmis = None
        self.baslik.set("")
        self.guncelle(tekrar=False)

    def islem_bitti(self) -> None:
        komut = self.calisan
        self.surec = self.calisan = None
        self.bekle_cubuk.stop()
        self.kok.deiconify()
        if self.sonra:
            self.sonra, sonra = None, self.sonra
            sonra()
        self.md_imza = None  # word/yeniden .md'yi değiştirmiş olabilir
        if komut == "bitir":
            son = a.klasor_sec(None)
            self.bitmis = son if son and son.exists() else None

    # ------------------------------------------------------------ ekranlar
    def goster(self, ad: str) -> None:
        if self.ekran == ad:
            return
        for f in (self.basla_f, self.kayit_f, self.bitis_f):
            f.grid_remove()
        {"basla": self.basla_f, "kayit": self.kayit_f, "bitis": self.bitis_f}[ad].grid(row=1, column=0, sticky="nsew")
        self.kok.attributes("-topmost", ad == "kayit")  # kayıtta hep üstte, diğerlerinde normal pencere
        self.ekran = ad

    def seridi_yenile(self, oturum: Path, veri: dict) -> None:
        imza = (oturum, tuple((x["gorsel"], bool(x.get("not")), mtime(oturum / x["gorsel"])) for x in veri["adimlar"]))
        if imza == self.onizlenen:  # yalnızca adım değişince görseller yeniden yüklenir
            return
        self.onizlenen = imza
        for w in self.serit.winfo_children():
            w.destroy()
        self.resimler = []
        for no, adim in enumerate(veri["adimlar"], 1):
            resim = kucult(oturum / adim["gorsel"], 200)
            self.resimler.append(resim)
            kutu = ttk.Frame(self.serit, padding=3)
            kutu.pack(side="left")
            gorsel = ttk.Label(kutu, image=resim or "", text="" if resim else "(görsel yok)", cursor="hand2")
            gorsel.pack()
            gorsel.bind("<Button-1>", lambda _, i=no - 1: self.duzenle(i))
            ek = " · not var" if adim.get("not") else (" · ses" if adim.get("ses") else "")
            ttk.Label(kutu, text=f"Adım {no}{ek}", font=("", 9)).pack()
        self.kok.update_idletasks()
        self.tuval.xview_moveto(1.0)  # en son çekilen görünsün

    def onizlemeyi_yenile(self) -> None:
        md = a.md_bul(self.bitmis)
        imza = (md, md.stat().st_mtime) if md else None
        if imza == self.md_imza:
            return
        self.md_imza = imza
        t = self.onizleme
        t.configure(state="normal")
        t.delete("1.0", "end")
        self.resimler = []
        if not md:
            t.insert("end", "Bu klasörde .md dosyası yok.")
        else:
            for satir in md.read_text(encoding="utf-8").splitlines():
                gorsel = re.search(r"!\[[^\]]*\]\(([^)]+)\)", satir)
                resim = kucult(md.parent / gorsel.group(1), 520) if gorsel else None
                if resim:
                    self.resimler.append(resim)
                    t.image_create("end", image=resim)
                    t.insert("end", "\n")
                elif satir.startswith("#"):
                    t.insert("end", satir.lstrip("#").strip() + "\n", "baslik")
                else:
                    t.insert("end", re.sub(r"^(\s*)- ", r"\1• ", satir.replace("**", "")) + "\n")
        t.configure(state="disabled")

    def guncelle(self, tekrar: bool = True) -> None:
        if self.surec and self.surec.poll() is not None:
            self.islem_bitti()
        oturum = a.aktif_oturum()
        veri = a.yukle(oturum) if oturum else None
        if veri:
            self.goster("kayit")
            kayit = a.surec_calisiyor(veri.get("kayit_pid"))
            tur = "sesli" if veri["mod"] == "ses" else "yazılı"
            self.kayit_baslik["text"] = f"{veri['baslik']} ({tur}) · Adım {len(veri['adimlar'])}"
            if kayit:
                self.kayit_isaret.grid(row=0, column=1, sticky="e")
            else:
                self.kayit_isaret.grid_remove()
            self.seridi_yenile(oturum, veri)
            self.ipucu["text"] = ipucu(veri, kayit)
        elif self.bitmis:
            self.goster("bitis")
            self.bitis_baslik["text"] = f"Doküman hazır: {self.bitmis.name}"
            self.onizlemeyi_yenile()
            self.ipucu["text"] = ("API çağrıları gerekiyorsa önce 'API ekle (HAR)', sonra komut tablosunu kopyalayıp 'Komut tablosu'. "
                                  "Rovo ile resmîleştirmek için: 1) MD'yi kopyala  2) Rovo'ya yapıştır  "
                                  "3) Rovo'nun çıktısını alttaki alana yapıştır. Sonra Word'ü aç ve kontrol et.")
        else:
            self.goster("basla")
            self.ipucu["text"] = ("Adını yaz, sesli ya da yazılı seç, Başla'ya bas. API çağrıları da gerekiyorsa "
                                  "önce tarayıcıda F12 → Ağ sekmesini aç (dişli → Kayıtları sürdür).")
        if self.surec:
            gecen = int(time.time() - self.bas_zamani)
            self.bekle_yazi["text"] = f"Lütfen bekle: {BEKLEME.get(self.calisan, self.calisan)}… ({gecen} sn)"
            self.bekle_ayrinti["text"] = son_satir()
            self.bekle_f.grid(row=2, column=0, sticky="we", pady=(6, 0))
        else:
            self.bekle_f.grid_remove()
        self.kok.configure(cursor="watch" if self.surec else "")
        if tekrar:
            self.kok.after(500, self.guncelle)  # ponytail: oturum.json'u yoklar; olay tabanlıya gerek yok


def main() -> int:
    kok = tk.Tk()
    Pencere(kok)
    kok.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
