"""Renders the dashboard snapshot to a PNG and sets it as the Windows wallpaper.

Used by "app.py --wallpaper" (start_wallpaper.bat): instead of serving a
browser page, every refresh paints the same cards onto a screen-sized
image and applies it via SystemParametersInfo. The previously configured
wallpaper path is backed up once to data/original_wallpaper.txt so it can
be restored (Windows Settings > Personalisation > Background, or just set
any picture again).
"""

import ctypes
import winreg
from pathlib import Path

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


def _screen_size():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # physical pixels
    except Exception:
        pass
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


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


def render(snapshot, out_path: Path):
    width, height = _screen_size()
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
    """Render the snapshot and apply it as wallpaper.

    Alternates between two files - Windows sometimes ignores a wallpaper
    call when the path is identical to the current one.
    """
    _toggle[0] = not _toggle[0]
    path = _DATA_DIR / f"wallpaper_{'a' if _toggle[0] else 'b'}.png"
    render(snapshot, path)
    set_wallpaper(path)
