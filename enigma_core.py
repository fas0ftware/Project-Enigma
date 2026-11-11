"""Project Enigma core: QR payloads (text, URL, Wi-Fi, contact, e-mail, SMS, phone, location)
and rendering to PNG/SVG with colours and an optional centre logo. No GUI code here."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

import qrcode
from PIL import Image, ImageColor
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

__version__ = "2.0.0"

ERROR_LEVELS = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
MAX_DATA = 2000  # characters; QR version 40 holds ~2.9 kB at level L, much less at H


# --- payloads ---------------------------------------------------------------------

def _escape_mecard(value: str) -> str:
    """Wi-Fi / MECARD fields escape \\ ; , : and " with a backslash."""
    return re.sub(r'([\\;,:"])', r"\\\1", value)


def wifi_payload(ssid: str, password: str = "", security: str = "WPA", hidden: bool = False) -> str:  # empty default = open network  # nosec B107
    security = security.upper()
    if security not in ("WPA", "WEP", "NOPASS"):
        raise ValueError("security must be WPA, WEP or nopass")
    if not ssid:
        raise ValueError("SSID is required")
    if security != "NOPASS" and not password:
        raise ValueError("a password is required for WPA/WEP networks")
    parts = [f"T:{'nopass' if security == 'NOPASS' else security}", f"S:{_escape_mecard(ssid)}"]
    if security != "NOPASS":
        parts.append(f"P:{_escape_mecard(password)}")
    if hidden:
        parts.append("H:true")
    return "WIFI:" + ";".join(parts) + ";;"


def _vcard_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def vcard_payload(name: str, phone: str = "", email: str = "", org: str = "", url: str = "") -> str:
    if not name.strip():
        raise ValueError("a name is required")
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{_vcard_escape(name.strip())}"]
    if org:
        lines.append(f"ORG:{_vcard_escape(org)}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{normalize_phone(phone)}")
    if email:
        lines.append(f"EMAIL:{validate_email(email)}")
    if url:
        lines.append(f"URL:{validate_url(url)}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r"[\s().-]", "", phone)
    if not re.fullmatch(r"\+?\d{5,15}", cleaned):
        raise ValueError(f"not a phone number: {phone!r}")
    return cleaned


def validate_email(email: str) -> str:
    email = email.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError(f"not an e-mail address: {email!r}")
    return email


def validate_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url, re.I):
        raise ValueError("URLs must start with http:// or https://")
    return url


def email_payload(to: str, subject: str = "", body: str = "") -> str:
    from urllib.parse import quote

    query = "&".join(f"{k}={quote(v)}" for k, v in (("subject", subject), ("body", body)) if v)
    return f"mailto:{validate_email(to)}" + (f"?{query}" if query else "")


def sms_payload(phone: str, message: str = "") -> str:
    return f"SMSTO:{normalize_phone(phone)}:{message}"


def phone_payload(phone: str) -> str:
    return f"tel:{normalize_phone(phone)}"


def geo_payload(lat: float, lon: float) -> str:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("latitude must be -90..90 and longitude -180..180")
    return f"geo:{lat:.6f},{lon:.6f}"


# --- colours ------------------------------------------------------------------------------

def parse_color(value: str) -> tuple[int, int, int]:
    try:
        rgb = ImageColor.getrgb(value)
    except ValueError:
        raise ValueError(f"unknown colour {value!r} (use a name like 'navy' or #RRGGBB)")
    return rgb[:3]


def _luminance(rgb) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg) -> float:
    """WCAG contrast ratio 1..21. QR scanners need dark modules on a light background."""
    a, b = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# --- rendering ---------------------------------------------------------------------------

@dataclass
class Style:
    fg: str = "black"
    bg: str = "white"
    error: str = "M"
    box_size: int = 10
    border: int = 4
    logo: str | None = None   # path to an image placed in the centre (forces error level H)
    logo_ratio: float = 0.22  # logo width relative to the code


def check_style(style: Style) -> list[str]:
    """Problems that would make the code unreadable (empty list = fine)."""
    problems = []
    fg, bg = parse_color(style.fg), parse_color(style.bg)
    if contrast_ratio(fg, bg) < 3:
        problems.append("colours have too little contrast for scanners (need at least 3:1)")
    if _luminance(fg) > _luminance(bg):
        problems.append("the foreground must be darker than the background (many scanners fail on inverted codes)")
    if style.error not in ERROR_LEVELS:
        problems.append("error correction must be L, M, Q or H")
    if not 1 <= style.box_size <= 50 or not 0 <= style.border <= 20:
        problems.append("box size must be 1-50 and border 0-20")
    if not 0.1 <= style.logo_ratio <= 0.3:
        problems.append("logo ratio must be 0.1-0.3 (larger logos hide too much of the code)")
    return problems


def make_qr(data: str, style: Style | None = None) -> Image.Image:
    style = style or Style()
    if not data:
        raise ValueError("there is nothing to encode")
    if len(data) > MAX_DATA:
        raise ValueError(f"data is longer than {MAX_DATA} characters")
    problems = check_style(style)
    if problems:
        raise ValueError("; ".join(problems))
    level = ERROR_LEVELS["H" if style.logo else style.error]
    qr = qrcode.QRCode(error_correction=level, box_size=style.box_size, border=style.border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=parse_color(style.fg), back_color=parse_color(style.bg)).get_image().convert("RGB")
    if style.logo:
        logo = Image.open(style.logo).convert("RGBA")
        size = int(img.width * style.logo_ratio)
        logo.thumbnail((size, size), Image.Resampling.LANCZOS)
        pad = max(4, size // 12)
        plate = Image.new("RGB", (logo.width + 2 * pad, logo.height + 2 * pad), parse_color(style.bg))
        plate.paste(logo, (pad, pad), logo)
        img.paste(plate, ((img.width - plate.width) // 2, (img.height - plate.height) // 2))
    return img


def make_svg(data: str, style: Style | None = None) -> str:
    """Vector output (no logo): crisp at any print size."""
    style = style or Style()
    problems = check_style(style)
    if problems:
        raise ValueError("; ".join(problems))
    qr = qrcode.QRCode(error_correction=ERROR_LEVELS[style.error], border=style.border)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    fg = "#%02x%02x%02x" % parse_color(style.fg)
    bg = "#%02x%02x%02x" % parse_color(style.bg)
    path = "".join(f"M{x},{y}h1v1h-1z" for y, row in enumerate(matrix) for x, on in enumerate(row) if on)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="{bg}"/><path d="{path}" fill="{fg}"/></svg>\n')


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
