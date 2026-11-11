"""Project Enigma on the command line.

    python cli.py text "https://fasoftware.dev" -o site.png
    python cli.py wifi --ssid "Home" --password "s3cret!" -o wifi.png --fg "#1f2937"
    python cli.py contact --name "Ada Lovelace" --phone "+44 20 7946 0000" --email ada@example.com -o ada.svg
    python cli.py email --to hi@example.com --subject Hello -o mail.png --logo logo.png
"""

from __future__ import annotations

import argparse
import os
import sys

import enigma_core as core


def build_parser():
    p = argparse.ArgumentParser(prog="enigma", description="QR code generator (PNG or SVG).")
    p.add_argument("--version", action="version", version=f"%(prog)s {core.__version__}")
    sub = p.add_subparsers(dest="kind", required=True)

    def common(sp):
        sp.add_argument("-o", "--output", required=True, help="file to write: .png or .svg")
        sp.add_argument("--fg", default="black", help="module colour (default black)")
        sp.add_argument("--bg", default="white", help="background colour (default white)")
        sp.add_argument("--error", choices=list(core.ERROR_LEVELS), default="M", help="error correction level")
        sp.add_argument("--size", type=int, default=10, help="pixels per module (PNG)")
        sp.add_argument("--border", type=int, default=4, help="quiet zone in modules (default 4)")
        sp.add_argument("--logo", help="image placed in the centre (PNG only; uses level H)")
        sp.add_argument("--force", action="store_true", help="overwrite an existing file")
        return sp

    common(sub.add_parser("text", help="any text or URL")).add_argument("data")
    w = common(sub.add_parser("wifi", help="join a Wi-Fi network"))
    w.add_argument("--ssid", required=True)
    w.add_argument("--password", default="")
    w.add_argument("--security", choices=["WPA", "WEP", "nopass"], default="WPA")
    w.add_argument("--hidden", action="store_true")
    c = common(sub.add_parser("contact", help="vCard contact"))
    c.add_argument("--name", required=True)
    for opt in ("--phone", "--email", "--org", "--url"):
        c.add_argument(opt, default="")
    e = common(sub.add_parser("email", help="pre-filled e-mail"))
    e.add_argument("--to", required=True)
    e.add_argument("--subject", default="")
    e.add_argument("--body", default="")
    s = common(sub.add_parser("sms", help="pre-filled SMS"))
    s.add_argument("--phone", required=True)
    s.add_argument("--message", default="")
    t = common(sub.add_parser("phone", help="call a number"))
    t.add_argument("number")
    g = common(sub.add_parser("geo", help="a location on the map"))
    g.add_argument("lat", type=float)
    g.add_argument("lon", type=float)
    return p


def payload(args) -> str:
    if args.kind == "text":
        return args.data
    if args.kind == "wifi":
        return core.wifi_payload(args.ssid, args.password, args.security, args.hidden)
    if args.kind == "contact":
        return core.vcard_payload(args.name, args.phone, args.email, args.org, args.url)
    if args.kind == "email":
        return core.email_payload(args.to, args.subject, args.body)
    if args.kind == "sms":
        return core.sms_payload(args.phone, args.message)
    if args.kind == "phone":
        return core.phone_payload(args.number)
    return core.geo_payload(args.lat, args.lon)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    out = args.output
    ext = os.path.splitext(out)[1].lower()
    if ext not in (".png", ".svg"):
        print("Error: the output must end in .png or .svg", file=sys.stderr)
        return 2
    if os.path.exists(out) and not args.force:
        print(f"Error: {out} exists (use --force to overwrite)", file=sys.stderr)
        return 2
    style = core.Style(fg=args.fg, bg=args.bg, error=args.error, box_size=args.size, border=args.border,
                       logo=args.logo)
    try:
        data = payload(args)
        if ext == ".svg":
            if args.logo:
                raise ValueError("--logo is only supported for PNG output")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(core.make_svg(data, style))
        else:
            core.make_qr(data, style).save(out)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Saved {out} ({args.kind}, {len(data)} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
