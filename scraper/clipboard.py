"""Cross-platform clipboard copy with graceful fallbacks.

Tries, in order:
1. pyperclip (if installed - `pip install pyperclip`)
2. Windows PowerShell Set-Clipboard
3. Termux `termux-clipboard-set` (needs `pkg install termux-api`)
4. Linux xclip / xsel / wl-copy

Returns the backend name on success, or None if every mechanism failed
(the CLI then tells the user to copy the value manually).
"""
import shutil
import subprocess
import sys

_BACKEND_CACHE = None


def _try_pyperclip(text):
    try:
        import pyperclip

        pyperclip.copy(text)
        return "pyperclip"
    except Exception:
        return None


def _try_powershell(text):
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Set-Clipboard", "-Value", text],
            check=True, capture_output=True, timeout=15,
        )
        return "powershell-clipboard"
    except Exception:
        return None


def _try_windows_clip(text):
    """Pipes UTF-8 bytes into clip.exe (best effort for ASCII values)."""
    try:
        subprocess.run(["clip"], input=text.encode("utf-8"),
                       check=True, timeout=15)
        return "clip.exe"
    except Exception:
        return None


def _try_termux(text):
    if shutil.which("termux-clipboard-set") is None:
        return None
    try:
        subprocess.run(["termux-clipboard-set"], input=text.encode("utf-8"),
                       check=True, timeout=15)
        return "termux"
    except Exception:
        return None


def _try_linux(text):
    for cmd_args in (
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--input", "--clipboard"],
        ["wl-copy"],
    ):
        if shutil.which(cmd_args[0]) is None:
            continue
        try:
            subprocess.run(cmd_args, input=text.encode("utf-8"),
                           check=True, timeout=15)
            return cmd_args[0]
        except Exception:
            continue
    return None


def copy_text(text):
    """Copy to clipboard. Returns backend name or None."""
    global _BACKEND_CACHE

    if _BACKEND_CACHE == "none":
        return None

    for step in (
        _try_pyperclip,
        _try_powershell,
        _try_windows_clip,
        _try_termux,
        _try_linux,
    ):
        backend = step(text)
        if backend:
            _BACKEND_CACHE = backend
            return backend
    _BACKEND_CACHE = "none"
    return None


def backend_name():
    return _BACKEND_CACHE or "unknown"
