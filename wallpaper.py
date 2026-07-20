"""Renders the dashboard snapshot to a PNG and sets it as the Windows wallpaper.

Used by "app.py --wallpaper" (start_wallpaper.bat): instead of serving a
browser page, every refresh paints the same cards onto a screen-sized
image and applies it as the desktop background.

config.WALLPAPER_MONITOR selects the target: "left"/"right" set only that
monitor via the IDesktopWallpaper COM interface (the other monitor keeps
its own wallpaper); "all" (or COM failure) falls back to
SystemParametersInfo, which covers every monitor.

The previously configured wallpaper path is backed up once to
data/original_wallpaper.txt so it can be restored (Windows Settings >
Personalisation > Background, or just set any picture again).
"""

import ctypes
import winreg
from ctypes import POINTER, c_uint, wintypes
from pathlib import Path

import comtypes
from PIL import Image, ImageDraw, ImageFont

import config

_DATA_DIR = Path(__file__).resolve().parent / "data"
_BACKUP_FILE = _DATA_DIR / "original_wallpaper.txt"

# same palette as templates/index.html
_BG = "#0f1419"
_CARD = "#171e26"
_BORDER = "#232d38"
_TEXT = "#dbe4ee"
_MUTED = "#7a8894"
_ACCENT = "#4da3ff"
_POS = "#35c07e"
_NEG = "#e5605e"
_STALE = "#d9a23c"
_CLS_COLORS = {"pos": _POS, "neg": _NEG, "flat": _MUTED}


def _set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # physical pixels
    except Exception:
        pass


def _screen_size():
    _set_dpi_aware()
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


class IDesktopWallpaper(comtypes.IUnknown):
    """Minimal IDesktopWallpaper vtable (methods must stay in this order)."""

    _iid_ = comtypes.GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")
    _methods_ = [
        comtypes.COMMETHOD([], comtypes.HRESULT, "SetWallpaper",
                           (["in"], wintypes.LPCWSTR, "monitorID"),
                           (["in"], wintypes.LPCWSTR, "wallpaper")),
        comtypes.COMMETHOD([], comtypes.HRESULT, "GetWallpaper",
                           (["in"], wintypes.LPCWSTR, "monitorID"),
                           (["out"], POINTER(wintypes.LPWSTR), "wallpaper")),
        comtypes.COMMETHOD([], comtypes.HRESULT, "GetMonitorDevicePathAt",
                           (["in"], c_uint, "monitorIndex"),
                           (["out"], POINTER(wintypes.LPWSTR), "monitorID")),
        comtypes.COMMETHOD([], comtypes.HRESULT, "GetMonitorDevicePathCount",
                           (["out"], POINTER(c_uint), "count")),
        comtypes.COMMETHOD([], comtypes.HRESULT, "GetMonitorRECT",
                           (["in"], wintypes.LPCWSTR, "monitorID"),
                           (["out"], POINTER(wintypes.RECT), "displayRect")),
    ]


_CLSID_DESKTOP_WALLPAPER = comtypes.GUID("{C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD}")


def _pick_monitor():
    """Returns (monitor_id, (width, height)) of the configured monitor, or
    None when WALLPAPER_MONITOR is "all" / COM is unavailable."""
    side = getattr(config, "WALLPAPER_MONITOR", "all").lower()
    if side not in ("left", "right"):
        return None
    try:
        comtypes.CoInitialize()
        dw = comtypes.CoCreateInstance(
            _CLSID_DESKTOP_WALLPAPER, interface=IDesktopWallpaper
        )
        monitors = []
        for i in range(dw.GetMonitorDevicePathCount()):
            monitor_id = dw.GetMonitorDevicePathAt(i)
            try:
                rect = dw.GetMonitorRECT(monitor_id)
            except Exception:
                continue  # stale entry for a disconnected monitor
            monitors.append((monitor_id, rect))
        if not monitors:
            return None
        pick = min if side == "left" else max
        monitor_id, rect = pick(monitors, key=lambda m: m[1].left)
        return monitor_id, (rect.right - rect.left, rect.bottom - rect.top)
    except Exception:
        return None


def _set_monitor_wallpaper(monitor_id: str, path: Path) -> bool:
    try:
        comtypes.CoInitialize()
        dw = comtypes.CoCreateInstance(
            _CLSID_DESKTOP_WALLPAPER, interface=IDesktopWallpaper
        )
        dw.SetWallpaper(monitor_id, str(path))
        return True
    except Exception:
        return False


def _font(size, bold=False):
    for name in (["seguisb.ttf", "segoeuib.ttf"] if bold else ["segoeui.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _draw_card(d, x, y, w, class_name, rows, s, fonts):
    pad = int(14 * s)
    row_h = int(23 * s)
    title_h = int(30 * s)
    h = title_h + len(rows) * row_h + 2 * pad
    d.rounded_rectangle([x, y, x + w, y + h], radius=int(10 * s),
                        fill=_CARD, outline=_BORDER, width=max(1, int(s)))
    d.text((x + pad, y + pad), class_name, font=fonts["title"], fill=_ACCENT)
    # right edges of the three numeric columns
    x_val, x_1d, x_ytd = x + w * 0.58, x + w * 0.79, x + w - pad
    ty = y + pad + title_h
    for r in rows:
        d.text((x + pad, ty), r["name"], font=fonts["row"], fill=_TEXT)
        name_w = d.textlength(r["name"], font=fonts["row"])
        d.text((x + pad + name_w + int(6 * s), ty + int(2 * s)),
               r["ccy"], font=fonts["small"], fill=_MUTED)
        val_color = _STALE if r.get("asof") else _TEXT
        for text, right_x, color in [
            (r["value"], x_val, val_color),
            (r["chg_1d"]["text"], x_1d, _CLS_COLORS.get(r["chg_1d"]["cls"], _MUTED)),
            (r["chg_ytd"]["text"], x_ytd, _CLS_COLORS.get(r["chg_ytd"]["cls"], _MUTED)),
        ]:
            d.text((right_x - d.textlength(text, font=fonts["row"]), ty),
                   text, font=fonts["row"], fill=color)
        ty += row_h
    return h


def render(snapshot, out_path: Path, size=None):
    _set_dpi_aware()
    width, height = size if size else _screen_size()
    s = width / 1920
    img = Image.new("RGB", (width, height), _BG)
    d = ImageDraw.Draw(img)
    fonts = {
        "header": _font(int(30 * s), bold=True),
        "title": _font(int(17 * s), bold=True),
        "row": _font(int(14 * s)),
        "small": _font(int(11 * s)),
    }
    margin, gap = int(40 * s), int(16 * s)

    d.text((margin, margin), "Market Overview", font=fonts["header"], fill=_TEXT)
    sub = (f"data as of {snapshot['updated']}  ·  refresh every "
           f"{config.REFRESH_MINUTES} min  ·  orange value = stale (as-of date)")
    d.text((width - margin - d.textlength(sub, font=fonts["small"]), margin + int(14 * s)),
           sub, font=fonts["small"], fill=_MUTED)

    columns = 4
    col_w = (width - 2 * margin - (columns - 1) * gap) // columns
    col_y = [margin + int(56 * s)] * columns
    for class_name, rows in snapshot["classes"].items():
        col = min(range(columns), key=lambda i: col_y[i])
        x = margin + col * (col_w + gap)
        card_h = _draw_card(d, x, col_y[col], col_w, class_name, rows, s, fonts)
        col_y[col] += card_h + gap

    out_path.parent.mkdir(exist_ok=True)
    img.save(out_path)


def _backup_original():
    if _BACKUP_FILE.exists():
        return
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            current = winreg.QueryValueEx(key, "Wallpaper")[0]
        _DATA_DIR.mkdir(exist_ok=True)
        _BACKUP_FILE.write_text(current, encoding="utf-8")
    except Exception:
        pass


def set_wallpaper(path: Path):
    _backup_original()
    SPI_SETDESKWALLPAPER, SPIF_UPDATE_AND_SEND = 20, 3
    ok = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, str(path), SPIF_UPDATE_AND_SEND
    )
    if not ok:
        raise OSError("SystemParametersInfoW failed to set the wallpaper")


_toggle = [False]


def update(snapshot):
    """Render the snapshot and apply it as wallpaper on the configured
    monitor(s).

    Alternates between two files - Windows sometimes ignores a wallpaper
    call when the path is identical to the current one.
    """
    _toggle[0] = not _toggle[0]
    path = _DATA_DIR / f"wallpaper_{'a' if _toggle[0] else 'b'}.png"
    target = _pick_monitor()
    if target:
        monitor_id, size = target
        render(snapshot, path, size=size)
        _backup_original()
        if _set_monitor_wallpaper(monitor_id, path):
            return
    # "all" configured, or the per-monitor COM route failed
    render(snapshot, path)
    set_wallpaper(path)
