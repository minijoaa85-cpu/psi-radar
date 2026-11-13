"""Both personal and data-audit tools must stay outside the primary technical navigation."""
from pathlib import Path
from html.parser import HTMLParser

PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
CSS=PAGE.split("<style>",1)[1].split("</style>",1)[0]
def test_secondary_tools_are_outside_primary_tabs_and_ordered():
 nav=PAGE.split('<nav id="nav"',1)[1].split("</nav>",1)[0]
 assert 'data-tab="watchlist"' not in nav
 assert 'data-tab="sources"' not in nav
 tools=PAGE.split('<aside class="personal-tools"',1)[1].split("</aside>",1)[0]
 assert tools.index('id="watch-quick-access"')<tools.index('id="quality-quick-access"')
 assert 'aria-controls="watchlist"' in tools
 assert 'aria-controls="sources"' in tools
 assert 'aria-expanded="false"' in tools
def test_data_quality_is_still_operational_and_has_return():
 assert 'id="sources"' in PAGE
 assert 'id="health"' in PAGE
 assert 'id="quality-close"' in PAGE
 assert 'showRadarSection(isOpen?lastResearchTab:pageId)' in PAGE
 assert 'if(tab!=="watchlist"&&tab!=="sources"&&tab!=="history")lastResearchTab=tab;' in PAGE
 assert 'id="history-quick-access"' in PAGE
 assert 'id="history-close"' in PAGE
 assert '["quality-quick-access","sources","quality-close"]' in PAGE
 assert 'el(buttonId).setAttribute("aria-expanded",String(active))' in PAGE
def test_shortcut_is_vertical_on_desktop_and_mobile():
 assert 'position:fixed;right:0;top:48%' in CSS
 assert 'flex-direction:column' in CSS
 assert '.personal-tools .quality-quick-access' in CSS
 assert '@media(max-width:700px)' in CSS
 assert 'bottom:calc(12px + env(safe-area-inset-bottom,0px))' in CSS
 assert 'main{padding-bottom:calc(117px + env(safe-area-inset-bottom,0px))}' in CSS
def test_preserve_stored_personal_settings_and_sources():
 for key in ("psi-radar-watch-v1","psi-radar-read-v1","psi-radar-bookmarks-v1"):
  assert key in PAGE
 assert 'Source & Data Quality' in PAGE
