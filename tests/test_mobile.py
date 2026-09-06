#!/usr/bin/env python3
"""Mobile share sheet: Web Share when present, copy fallback otherwise.

Does not issue. Does not invent a host. Does not mention a store.
"""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "mobile" / "index.html"


def _html() -> str:
    return PAGE.read_text(encoding="utf-8")


def _helpers() -> str:
    html = _html()
    start = html.index("// --- share helpers")
    end = html.index("// --- /share helpers")
    return html[start:end]


def _node(expr: str):
    script = _helpers() + "\nprocess.stdout.write(JSON.stringify(" + expr + "))"
    r = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise AssertionError(r.stderr or r.stdout or "node failed")
    return json.loads(r.stdout)


class MobilePage(unittest.TestCase):
    def test_pick_and_verdict_still_there(self):
        html = _html()
        self.assertIn('type="file"', html)
        self.assertIn('id="f"', html)
        self.assertIn('id="c"', html)
        self.assertIn("UNFORGE-PREUVE-v1", html)
        self.assertIn('class="VERT"', html)
        self.assertIn('class="ROUGE"', html)
        self.assertIn("onchange=run", html)

    def test_web_share_and_copy_fallback(self):
        html = _html()
        self.assertIn("navigator.share", html)
        self.assertIn("preferWebShare", html)
        self.assertIn("navigator.clipboard", html)
        self.assertIn('id="share-btn"', html)
        self.assertIn('id="copy-btn"', html)
        self.assertIn('id="copy-link-btn"', html)
        self.assertIn('id="share-fallback"', html)
        self.assertIn("Share", html)
        self.assertIn("Copy link", html)

    def test_no_store_and_no_seal(self):
        html = _html().lower()
        for banned in (
            "app store",
            "appstore",
            "play.google",
            "itunes.apple",
            "badge",
        ):
            self.assertNotIn(banned, html)
        self.assertIn("does not sign", html)
        self.assertIn("not a seal", html)

    def test_english_share_copy(self):
        html = _html()
        self.assertIn("Sharing is not available here.", html)
        self.assertIn("Copied.", html)
        self.assertIn("Link copied.", html)
        self.assertNotRegex(html, r">\s*(Partager|Copier le lien|Copié)\s*<")


class ShareHelpers(unittest.TestCase):
    def test_share_url_only_http(self):
        self.assertEqual(
            _node("sharePageUrl('https://example.test/mobile/')"),
            "https://example.test/mobile/",
        )
        self.assertEqual(
            _node("sharePageUrl('http://127.0.0.1:8000/mobile/index.html')"),
            "http://127.0.0.1:8000/mobile/index.html",
        )
        self.assertEqual(_node("sharePageUrl('file:///tmp/index.html')"), "")
        self.assertEqual(_node("sharePageUrl('blob:https://x/1')"), "")
        self.assertEqual(_node("sharePageUrl(null)"), "")

    def test_payload_omits_local_url(self):
        data = _node(
            "buildShareData('VERT file matches the card. Signatures stay in check.py.',"
            " 'file:///workspace/mobile/index.html')"
        )
        self.assertEqual(data["title"], "UNFORGE Check")
        self.assertIn("VERT", data["text"])
        self.assertNotIn("url", data)
        self.assertNotIn("seal", data["text"].lower())

    def test_payload_keeps_https_url(self):
        data = _node(
            "buildShareData('ROUGE digest mismatch.', 'https://example.test/check')"
        )
        self.assertEqual(data["url"], "https://example.test/check")
        self.assertEqual(
            _node("shareClipboardText(" + json.dumps(data) + ")"),
            "UNFORGE Check\nROUGE digest mismatch.\nhttps://example.test/check",
        )

    def test_prefer_web_share(self):
        self.assertTrue(
            _node("preferWebShare({share: function(){}}, {title:'UNFORGE Check'})")
        )
        self.assertFalse(_node("preferWebShare({}, {title:'UNFORGE Check'})"))
        self.assertFalse(
            _node(
                "preferWebShare({share:function(){}, canShare:function(){return false}},"
                " {title:'UNFORGE Check'})"
            )
        )
        self.assertTrue(
            _node(
                "preferWebShare({share:function(){}, canShare:function(){return true}},"
                " {title:'UNFORGE Check'})"
            )
        )


if __name__ == "__main__":
    unittest.main()
