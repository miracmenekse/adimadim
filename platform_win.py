#!/usr/bin/env python3
"""Windows platform katmanı: ekran görüntüsü, ses kaydı, pencere ve bildirim.

adimadim.py bu dosyayı yalnız Windows'ta içe aktarır; Linux'ta kullanılmaz.
Kayıt alt süreci `python platform_win.py kaydet <wav>` ile başlatılır.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import sys
import tempfile
import wave
from pathlib import Path

DWMWA_EXTENDED_FRAME_BOUNDS = 9
STILL_ACTIVE = 259


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def _dpi_farkinda() -> None:
    """Ekran koordinatları fiziksel piksel olsun (ölçekleme görüntüyü kaydırmasın)."""
    with contextlib.suppress(Exception):
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    with contextlib.suppress(Exception):
        ctypes.windll.user32.SetProcessDPIAware()


def _pencere_alani() -> dict | None:
    """Öndeki pencerenin DWM çerçeve sınırları; başarısızsa None."""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return None
    alan = _RECT()
    sonuc = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(alan), ctypes.sizeof(alan))
    if sonuc != 0 and not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(alan)):
        return None
    genislik, yukseklik = alan.right - alan.left, alan.bottom - alan.top
    if genislik <= 0 or yukseklik <= 0:
        return None
    return {"left": alan.left, "top": alan.top, "width": genislik, "height": yukseklik}


def ekran(hedef: Path, kip: str) -> bool:
    """Ekran görüntüsünü PNG olarak yazar. kip: "pencere" ya da "tam"."""
    _dpi_farkinda()
    try:
        import mss
        import mss.tools
    except ImportError:
        return False
    hedef.parent.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(Exception):
        with mss.mss() as ekran_:
            alan = _pencere_alani() if kip == "pencere" else None
            alan = alan or ekran_.monitors[0]
            goruntu = ekran_.grab(alan)
            mss.tools.to_png(goruntu.rgb, goruntu.size, output=str(hedef))
    return hedef.exists() and hedef.stat().st_size > 0


def bildirim(mesaj: str) -> None:
    """Kısa sistem sesi; pencere açmaz ve bloklamaz. Metin zaten terminale yazıldı."""
    with contextlib.suppress(Exception):
        ctypes.windll.user32.MessageBeep(0x40)


def surec_calisiyor(pid: int | None) -> bool:
    """pid yaşıyor ve görüntü adında "python" geçiyor mu?"""
    if not pid:
        return False
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    surec = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
    if not surec:
        return False
    try:
        kod = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(surec, ctypes.byref(kod)) or kod.value != STILL_ACTIVE:
            return False
        boyut = ctypes.c_ulong(1024)
        ad = ctypes.create_unicode_buffer(boyut.value)
        if not kernel32.QueryFullProcessImageNameW(surec, 0, ad, ctypes.byref(boyut)):
            return False
        return "python" in ad.value.lower()
    finally:
        kernel32.CloseHandle(surec)


def sonlandir(pid: int | None) -> None:
    """Kayıt süreci dur dosyasına bakmadıysa zorla kapat."""
    if not pid:
        return
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    surec = kernel32.OpenProcess(0x0001, False, int(pid))  # PROCESS_TERMINATE
    if not surec:
        return
    try:
        kernel32.TerminateProcess(surec, 1)
    finally:
        kernel32.CloseHandle(surec)


def giris_cihazi(sd, mikrofon: str) -> int | None:
    """Adında `mikrofon` parçası geçen ilk giriş cihazının numarası; boşsa ya da yoksa None (varsayılan)."""
    parca = (mikrofon or "").strip().lower()
    if not parca:
        return None
    with contextlib.suppress(Exception):
        for no, cihaz in enumerate(sd.query_devices()):
            if cihaz.get("max_input_channels", 0) > 0 and parca in str(cihaz.get("name", "")).lower():
                return no
    return None


def kaydet(dosya: Path, mikrofon: str = "") -> int:
    """16 kHz mono int16 WAV kaydeder; dur dosyası belirince düzgün kapatıp çıkar.

    mikrofon doluysa adında bu parça geçen giriş cihazı kullanılır; bulunamaz ya da 16 kHz açılamazsa
    sistem varsayılan girişine düşülür.
    """
    try:
        import sounddevice as sd
    except ImportError:
        return 1
    cihaz = giris_cihazi(sd, mikrofon)
    if cihaz is not None:
        try:
            sd.check_input_settings(device=cihaz, samplerate=16000, channels=1, dtype="int16")
        except Exception:
            cihaz = None
    dur = Path(tempfile.gettempdir()) / f"adimadim-kayit-{os.getpid()}.dur"
    dur.unlink(missing_ok=True)
    try:
        with wave.open(str(dosya), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            with sd.InputStream(device=cihaz, samplerate=16000, channels=1, dtype="int16") as akis:
                while not dur.exists():
                    veri, _ = akis.read(1024)
                    w.writeframes(veri.tobytes())
    except Exception:
        return 1
    finally:
        dur.unlink(missing_ok=True)
    return 0


def metin_iste(baslik: str, mevcut: str = "", coklu: bool = True,
               tamam: str = "Kaydet", vazgec: str = "Vazgeç") -> str | None:
    """Zenity yerine tkinter penceresi; hep üstte, Ctrl+Enter Tamam, Esc vazgeç."""
    import tkinter as tk
    from tkinter import scrolledtext

    sonuc: dict[str, str | None] = {"metin": None}
    kok = tk.Tk()
    kok.title(baslik)
    kok.attributes("-topmost", True)
    kok.geometry("680x340" if coklu else "420x120")
    if coklu:
        kutu = scrolledtext.ScrolledText(kok, wrap="word")
        kutu.insert("1.0", mevcut)
    else:
        kutu = tk.Entry(kok)
        kutu.insert(0, mevcut)
    # Düğmeler önce ve altta yerleşir: yoksa metin kutusu tüm pencereyi kaplayıp onları dışarı iter.
    dugmeler = tk.Frame(kok)
    dugmeler.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
    tk.Label(dugmeler, text="Ctrl+Enter: kaydet · Esc: vazgeç" if coklu else "Enter: kaydet · Esc: vazgeç",
             fg="#666").pack(side="left")
    tk.Button(dugmeler, text=tamam, width=10, default="active",
              command=lambda: al()).pack(side="right", padx=(4, 0))
    tk.Button(dugmeler, text=vazgec, width=10, command=lambda: bitir(None)).pack(side="right", padx=4)
    kutu.pack(fill="both", expand=True, padx=8, pady=8)
    kutu.focus_set()

    def bitir(metin: str | None) -> None:
        sonuc["metin"] = metin
        kok.destroy()

    def al() -> None:
        bitir(kutu.get("1.0", "end-1c") if coklu else kutu.get())

    def tus(olay) -> str | None:
        if olay.keysym == "Escape":
            bitir(None)
            return "break"
        if olay.keysym == "Return" and (not coklu or olay.state & 0x0004):
            al()
            return "break"
        return None

    kok.bind("<Key>", tus)
    kok.protocol("WM_DELETE_WINDOW", lambda: bitir(None))
    kok.mainloop()
    return sonuc["metin"]


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "kaydet":
        sys.exit(kaydet(Path(sys.argv[2]), sys.argv[3] if len(sys.argv) >= 4 else ""))
    sys.exit(1)
