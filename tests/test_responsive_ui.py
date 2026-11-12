"""Regression guards for readability across phone/tablet/desktop widths.

These are CSS/DOM structural checks, not pixel-perfect browser screenshots.
"""
from pathlib import Path
import re

PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
CSS=PAGE.split("<style>",1)[1].split("</style>",1)[0]
SCRIPT=PAGE.split("<script>",1)[1].split("</script>",1)[0]

def test_checkbox_fixed_size_overrides_global_text_input_rule():
 assert "input{min-width:260px;flex:1}" in CSS
 assert re.search(r'input\[type="checkbox"\],input\[type="radio"\]\s*\{[^}]*min-width:0;[^}]*width:16px;[^}]*flex:0 0 16px;',CSS)
 assert "watch-choice-text" in CSS and "watch-choice-text" in SCRIPT
 assert "overflow-wrap:anywhere" in CSS

def test_mobile_nav_wrapping_and_input_flex():
 assert re.search(r'\.nav\{[^}]*flex-wrap:wrap;',CSS)
 assert "@media(max-width:600px)" in CSS
 assert "grid-template-columns:repeat(2,minmax(0,1fr))" in CSS
 assert "white-space:normal" in CSS
 assert "input:not([type=\"checkbox\"]):not([type=\"radio\"])" in CSS

def test_phone_tablet_watchlist_columns():
 assert "@media(max-width:950px)" in CSS
 assert "@media(max-width:370px)" in CSS
 assert re.search(r'\.mywatch-toggles\{grid-template-columns:1fr\}',CSS)
 assert "max-width:100%" in CSS
 assert ".fom-heat-wrap" in CSS and ".benchmark-table-wrap" in CSS

def test_order_and_functionality_untouched():
 for item in ('id="watch-techs"','id="watch-companies"','id="watch-save"','id="watch-reset"',
              'id="watch-feed"','id="brief-feed"','id="bench-fom"','id="arch-overview"'):
  assert item in PAGE
 assert 'const WATCH_TECH_ORDER=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in PAGE
