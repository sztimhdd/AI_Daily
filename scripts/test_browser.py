#!/usr/bin/env python3
"""Optional isolated headless HTML-extraction smoke test. No live websites/CDP."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from ai_daily.fetch import extract_title, html_to_markdown
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    try:
        context = browser.new_context()
        context.route('**/*', lambda route: route.abort())
        page = context.new_page()
        page.set_content('<title>Fixture story</title><article>Community case study.</article>')
        html = page.content()
        assert extract_title(html) == 'Fixture story'
        assert 'Community case study.' in html_to_markdown(html)
        print('PASS: isolated headless extraction; no network or personal profile')
    finally:
        browser.close()
