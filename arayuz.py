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
import tkinter as tk
from pathlib import Path
from tkinter import ttk

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
        return "Anlatman kaydediliyor. Cümleni bitir, sonraki ekrana geç, Ctrl+Alt+S. Son ekrandan sonra 'Bitir'."
    return "Sonraki ekrana geç, Ctrl+Alt+S. Hepsi bitince 'Bitir'."


def kucult(yol: Path, genislik: int) -> tk.PhotoImage | None:
    """PNG'yi yaklaşık `genislik` piksele küçültür (Tk yalnızca tam sayı oranla küçültür)."""
    try:
        resim = tk.PhotoImage(file=str(yol))
    except tk.TclError:
        return None
    oran = max(1, -(-resim.width() // genislik))
    return resim.subsample(oran) if oran > 1 else resim


def dugmeler(ust, satirlar) -> None:
    """Düğme sırası; her düğmenin altında ne işe yaradığı."""
    for sira, (metin, komut, aciklama) in enumerate(satirlar):
        ttk.Button(ust, text=metin, command=komut).grid(row=0, column=sira, sticky="we", padx=2)
        ttk.Label(ust, text=aciklama, foreground="#666", font=("", 8)).grid(row=1, column=sira, padx=2)


class Pencere:
    def __init__(self, kok: tk.Tk):
        self.kok, self.surec, self.calisan, self.bas_zamani = kok, None, None, 0.0
        self.bitmis: Path | None = None  # bitiş ekranında gösterilen doküman
        self.resimler, self.onizlenen, self.md_imza, self.ekran = [], None, None, None
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
                     ("Son adıma not yaz", lambda: self.calistir("not"), "Son ekrana yazılı açıklama ekler"),
                     ("Son adımı sil", lambda: self.calistir("geri"), "Yanlış çekilen son ekranı siler"),
                     ("Bitir", lambda: self.calistir("bitir"), "Dokümanı üretir")))

        # --- Bitiş ekranı: dokümanın önizlemesi ve sonrası
        self.bitis_f = f = ttk.Frame(c)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        self.bitis_baslik = ttk.Label(f, font=("", 11, "bold"))
        self.bitis_baslik.grid(row=0, column=0, sticky="w")
        self.onizleme = tk.Text(f, width=80, height=24, wrap="word", relief="flat", padx=8, pady=8,
                                font=("", 10))
        self.onizleme.tag_configure("baslik", font=("", 12, "bold"), spacing1=8)
        yukari = ttk.Scrollbar(f, command=self.onizleme.yview)
        self.onizleme.configure(yscrollcommand=yukari.set)
        self.onizleme.grid(row=1, column=0, sticky="nsew", pady=4)
        yukari.grid(row=1, column=1, sticky="ns")
        d = ttk.Frame(f)
        d.grid(row=2, column=0, columnspan=2, sticky="w")
        dugmeler(d, (("Word'ü aç", lambda: self.ac(".docx"), "Hazır Word dosyası"),
                     ("Klasörü aç", lambda: self.ac(""), "Görseller, sesler, .md"),
                     ("Word'ü yenile", lambda: self.calistir("word", str(self.bitmis)), ".md'yi elle düzelttiysen"),
                     ("Sesi baştan çevir", lambda: self.calistir("yeniden", str(self.bitmis)), "Metni sesten yeniden yazar"),
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

    def cek(self) -> None:
        if self.surec:
            return
        self.kok.withdraw()  # "pencere" kipinde arayüzün kendisi çekilmesin: odak önceki pencereye döner
        self.kok.after(400, lambda: self.calistir("cek"))

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
        imza = (oturum, tuple((x["gorsel"], bool(x.get("not"))) for x in veri["adimlar"]))
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
            ttk.Label(kutu, image=resim or "", text="" if resim else "(görsel yok)").pack()
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
                    t.insert("end", satir.replace("**", "") + "\n")
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
            self.ipucu["text"] = "Word'ü açıp kontrol et. .md'yi elle düzelttiysen 'Word'ü yenile'."
        else:
            self.goster("basla")
            self.ipucu["text"] = "Adını yaz, sesli ya da yazılı seç, Başla'ya bas."
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
