"""adımadım penceresi: komutları düğmelerle çalıştırır, terminal gerekmez.

Her düğme `adimadim.py <komut>`u ayrı süreçte çalıştırır (kilit, not penceresi, çeviri aynı kalır);
pencere yalnızca oturum.json'a bakıp durumu ve ipucunu gösterir.
"""
from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import ttk

import adimadim as a


def ipucu(veri: dict | None, kayit: bool, calisan: str | None) -> str:
    """O anki duruma göre tek satırlık kullanım ipucu."""
    if calisan == "bitir":
        return "Doküman hazırlanıyor; sesli modda çeviri birkaç dakika sürebilir."
    if calisan:
        return f"'{calisan}' çalışıyor…"
    if not veri:
        return "Akışın adını yaz, Sesli ya da Yazılı başla."
    if not veri["adimlar"]:
        return "Anlatacağın ilk ekrana geç, Ctrl+Alt+S'ye (ya da Ekranı çek'e) bas."
    if kayit:
        return "Kayıt sürüyor: cümleni bitir, sonraki ekranda Ctrl+Alt+S. Son ekrandan sonra Bitir."
    return "Sonraki ekranda Ctrl+Alt+S. Notu düzeltmek için Not, yanlış çekim için Geri."


class Pencere:
    def __init__(self, kok: tk.Tk):
        self.kok, self.surec, self.calisan, self.cikti = kok, None, None, ""
        kok.title(a.UYGULAMA)
        kok.attributes("-topmost", True)
        kok.resizable(False, False)
        c = ttk.Frame(kok, padding=8)
        c.pack(fill="both")
        c.columnconfigure(0, weight=1)

        self.baslik = tk.StringVar()
        self.ust = ttk.Frame(c)
        ttk.Entry(self.ust, textvariable=self.baslik, width=28).pack(side="left", padx=(0, 4))
        ttk.Button(self.ust, text="🎙️ Sesli başla", command=lambda: self.basla(True)).pack(side="left")
        ttk.Button(self.ust, text="✍️ Yazılı başla", command=lambda: self.basla(False)).pack(side="left")

        self.orta = ttk.Frame(c)
        for metin, komut in (("📷 Ekranı çek", self.cek), ("📝 Not", lambda: self.calistir("not")),
                             ("↩️ Geri", lambda: self.calistir("geri")), ("✅ Bitir", lambda: self.calistir("bitir"))):
            ttk.Button(self.orta, text=metin, command=komut).pack(side="left")

        self.alt = ttk.Frame(c)
        for metin, komut in (("📄 Word'ü yenile", "word"), ("🔁 Sesi yeniden çevir", "yeniden")):
            ttk.Button(self.alt, text=metin, command=lambda k=komut: self.calistir(k)).pack(side="left")
        ttk.Button(self.alt, text="📂 Klasör", command=self.klasor).pack(side="left")

        self.durum = ttk.Label(c, font=("", 10, "bold"))
        self.ipucu = ttk.Label(c, wraplength=420, foreground="#555")
        for sira, w in enumerate((self.ust, self.orta, self.alt, self.durum, self.ipucu)):
            w.grid(row=sira, column=0, sticky="w", pady=(4 if sira == 3 else 0, 0))
        self.guncelle()

    def calistir(self, *komut: str) -> None:
        if self.surec:
            return
        self.calisan = komut[0]
        self.surec = subprocess.Popen([sys.executable, str(a.REPO_DIZINI / "adimadim.py"), *komut],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def basla(self, ses: bool) -> None:
        baslik = self.baslik.get().strip()
        if baslik:
            self.calistir("basla", baslik, *(["--ses"] if ses else []))

    def cek(self) -> None:
        if self.surec:
            return
        self.kok.withdraw()  # "pencere" kipinde arayüzün kendisi çekilmesin: odak önceki pencereye döner
        self.kok.after(400, lambda: self.calistir("cek"))

    def klasor(self) -> None:
        oturum = a.aktif_oturum() or a.klasor_sec(None)
        if oturum:
            a.klasoru_ac(oturum)

    def guncelle(self) -> None:
        if self.surec and self.surec.poll() is not None:
            satirlar = [s for s in self.surec.stdout.read().splitlines() if s.strip()]
            self.cikti = satirlar[-1] if satirlar else ""
            self.surec = self.calisan = None
            self.kok.deiconify()
        oturum = a.aktif_oturum()
        veri = a.yukle(oturum) if oturum else None
        kayit = bool(veri) and a.surec_calisiyor(veri.get("kayit_pid"))
        (self.ust.grid_remove if veri else self.ust.grid)()
        (self.orta.grid if veri else self.orta.grid_remove)()
        if veri:
            self.durum["text"] = f"{veri['baslik']}: {len(veri['adimlar'])} adım" + (" · 🔴 kayıt" if kayit else "")
        else:
            self.durum["text"] = self.cikti or "Açık doküman yok."
        self.ipucu["text"] = ipucu(veri, kayit, self.calisan) + (f"\n{self.cikti}" if veri and self.cikti else "")
        self.kok.after(700, self.guncelle)  # ponytail: oturum.json'u yoklar; olay tabanlıya gerek yok


def main() -> int:
    kok = tk.Tk()
    Pencere(kok)
    kok.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
