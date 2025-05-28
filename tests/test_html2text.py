import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from html2text import html2text


def test_html2text_returns_input():
    html = "<p>Hello</p>"
    assert html2text(html) == html
