#!/usr/bin/env python3
"""Windows genel kısayolları: Ctrl+Alt+S ekranı çeker, Ctrl+Alt+N notu açar.

adimadim.py `kisayol` komutuyla (ve Startup .cmd ile) ayrık başlatılır; tek örnek
çalışır. Yalnız Windows'ta kullanılır (pynput gerekir).
"""
from __future__ import annotations

import contextlib
import os
import subprocess
import sys
from pathlib import Path

REPO_DIZINI = Path(__file__).resolve().parent
PID_DOSYASI = (Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
               / "adimadim" / "kisayol.pid")
KISAYOLLAR = {"<ctrl>+<alt>+s": "cek", "<ctrl>+<alt>+n": "not"}
AYRIK = (getattr(subprocess, "CREATE_NO_WINDOW", 0)
         | getattr(subprocess, "DETACHED_PROCESS", 0))


def pythonw() -> str:
    """sys.executable yanındaki pythonw.exe; yoksa sys.executable."""
    aday = Path(sys.executable or "pythonw.exe").with_name("pythonw.exe")
    return str(aday if aday.is_file() else sys.executable)


def komut(alt: str) -> list[str]:
    """Kısayolun çalıştıracağı komut: [pythonw, adimadim.py, alt komut]."""
    return [pythonw(), str(REPO_DIZINI / "adimadim.py"), alt]


def _calistir(alt: str) -> None:
    subprocess.Popen(komut(alt), creationflags=AYRIK, cwd=REPO_DIZINI)


def _canli(pid: int | None) -> bool:
    """pid yaşıyor ve görüntü adında "python" geçiyor mu?"""
    if not pid:
        return False
    try:
        import platform_win
        return platform_win.surec_calisiyor(pid)
    except Exception:
        return False


def _pid_oku() -> int | None:
    try:
        return int(PID_DOSYASI.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _yaz(mesaj: str) -> None:
    """Konsol yoksa ya da kodlamıyorsa sessizce geç (pythonw'da stdout None)."""
    try:
        print(mesaj, flush=True)
    except (AttributeError, OSError, UnicodeEncodeError):
        with contextlib.suppress(Exception):
            sys.stdout.buffer.write(mesaj.encode("utf-8") + b"\n")
            sys.stdout.buffer.flush()


def main() -> int:
    if _canli(_pid_oku()):
        _yaz("zaten çalışıyor")
        return 0
    PID_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    PID_DOSYASI.write_text(str(os.getpid()), encoding="utf-8")
    from pynput.keyboard import GlobalHotKeys
    tuslar = {tus: (lambda alt=alt: _calistir(alt)) for tus, alt in KISAYOLLAR.items()}
    with GlobalHotKeys(tuslar) as dinleyici:
        dinleyici.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
