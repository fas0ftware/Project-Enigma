import os
import tempfile
import unittest

from PIL import Image, ImageDraw

import cli
import enigma_core as core

try:
    import cv2
    import numpy as np
except ImportError:  # decoding checks need opencv (requirements-dev.txt)
    cv2 = None


def decode(img: Image.Image) -> str | None:
    arr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    text, points, _ = cv2.QRCodeDetector().detectAndDecode(arr)
    return text if points is not None else None


class PayloadTests(unittest.TestCase):
    def test_wifi_escapes_special_characters(self):
        self.assertEqual(core.wifi_payload('My;Net:"x"', r"p\a,ss"), r'WIFI:T:WPA;S:My\;Net\:\"x\";P:p\\a\,ss;;')
        self.assertEqual(core.wifi_payload("Cafe", security="nopass", hidden=True), "WIFI:T:nopass;S:Cafe;H:true;;")
        for bad in (("", "x"), ("Net", ""), ("Net", "x", "WPA3")):
            with self.assertRaises(ValueError):
                core.wifi_payload(*bad)

    def test_vcard(self):
        card = core.vcard_payload("Ada; Lovelace", phone="+44 (20) 7946-0000", email="ada@example.com", org="A, B")
        self.assertIn("FN:Ada\; Lovelace", card)
        self.assertIn("TEL;TYPE=CELL:+442079460000", card)
        self.assertIn("ORG:A\\, B", card)
        self.assertTrue(card.startswith("BEGIN:VCARD") and card.endswith("END:VCARD"))
        with self.assertRaises(ValueError):
            core.vcard_payload("X", email="not-an-email")
        with self.assertRaises(ValueError):
            core.vcard_payload("X", url="javascript:alert(1)")

    def test_other_payloads(self):
        self.assertEqual(core.email_payload("a@b.co", "Hi there", "x&y"), "mailto:a@b.co?subject=Hi%20there&body=x%26y")
        self.assertEqual(core.sms_payload("+90 555 000 00 00", "Hi"), "SMSTO:+905550000000:Hi")
        self.assertEqual(core.phone_payload("0212-555-0000"), "tel:02125550000")
        self.assertEqual(core.geo_payload(38.4192, 27.1287), "geo:38.419200,27.128700")
        with self.assertRaises(ValueError):
            core.geo_payload(91, 0)
        with self.assertRaises(ValueError):
            core.phone_payload("call me")


class StyleTests(unittest.TestCase):
    def test_contrast_rules(self):
        self.assertAlmostEqual(core.contrast_ratio((0, 0, 0), (255, 255, 255)), 21, places=0)
        self.assertEqual(core.check_style(core.Style(fg="#1f2937", bg="#f9fafb")), [])
        self.assertTrue(core.check_style(core.Style(fg="#cccccc", bg="white")))   # too light
        self.assertTrue(core.check_style(core.Style(fg="white", bg="black")))     # inverted
        self.assertTrue(core.check_style(core.Style(error="X")))
        with self.assertRaises(ValueError):
            core.parse_color("not-a-colour")

    def test_limits(self):
        with self.assertRaises(ValueError):
            core.make_qr("")
        with self.assertRaises(ValueError):
            core.make_qr("x" * (core.MAX_DATA + 1))


@unittest.skipUnless(cv2, "opencv-python-headless not installed")
class RoundTripTests(unittest.TestCase):
    """Every generated code is decoded again with OpenCV and must give back the same text."""

    def test_payload_types_decode(self):
        samples = [
            "https://github.com/fas0ftware",
            "Türkçe karakterler: ğüşöçİ",
            core.wifi_payload("Home Net", "s3cret;pass"),
            core.vcard_payload("Ada Lovelace", phone="+442079460000", email="ada@example.com"),
            core.geo_payload(38.4192, 27.1287),
        ]
        for data in samples:
            with self.subTest(data=data[:30]):
                self.assertEqual(decode(core.make_qr(data)), data)

    def test_colours_and_logo_still_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            logo = os.path.join(tmp, "logo.png")
            img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
            ImageDraw.Draw(img).ellipse((10, 10, 190, 190), fill=(220, 38, 38, 255))
            img.save(logo)
            style = core.Style(fg="#1e3a8a", bg="#fefce8", logo=logo)
            self.assertEqual(decode(core.make_qr("https://example.com/with-logo", style)), "https://example.com/with-logo")

    def test_svg_output(self):
        svg = core.make_svg("hello", core.Style(fg="navy"))
        self.assertTrue(svg.startswith("<svg") and 'fill="#000080"' in svg)


class CliTests(unittest.TestCase):
    def test_writes_png_and_svg_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            png, svg = os.path.join(tmp, "a.png"), os.path.join(tmp, "a.svg")
            self.assertEqual(cli.main(["text", "hi", "-o", png]), 0)
            self.assertEqual(cli.main(["wifi", "--ssid", "Net", "--password", "pw", "-o", svg]), 0)
            self.assertEqual(cli.main(["text", "again", "-o", png]), 2)
            self.assertEqual(cli.main(["text", "again", "-o", png, "--force"]), 0)
            self.assertEqual(cli.main(["text", "x", "-o", os.path.join(tmp, "a.jpg")]), 2)
            self.assertEqual(cli.main(["text", "x", "-o", os.path.join(tmp, "b.png"), "--fg", "white", "--bg", "black"]), 2)
            self.assertEqual(cli.main(["geo", "100", "0", "-o", os.path.join(tmp, "g.png")]), 2)


if __name__ == "__main__":
    unittest.main()
