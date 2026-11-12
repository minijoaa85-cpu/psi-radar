"""My Watch should remain accessible but not compete with core technology navigation."""
from pathlib import Path
import re

PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
CSS=PAGE.split("<style>",1)[1].split("</style>",1)[0]
def test_main_nav_only_contains_research_pages():
 nav=PAGE.split('<nav id="nav"',1)[1].split("</nav>",1)[0]
 assert 'data-tab="watchlist"' not in nav
 assert 'data-tab="overview"' in nav
 assert 'data-tab="briefing"' in nav
 assert 'data-tab="architecture"' in nav
 assert 'data-tab="benchmark"' in nav
def test_personal_entry_is_external_accessible_control():
 assert PAGE.count('id="watch-quick-access"')==1
 assert 'aria-controls="watchlist"' in PAGE
 assert 'aria-expanded="false"' in PAGE
 assert 'id="watch-close"' in PAGE
 assert 'aria-label="My Watch 닫고 이전 분석 화면으로 돌아가기"' in PAGE
 assert '.watch-quick-access{' in CSS
 assert 'position:fixed' in CSS
def test_return_to_previous_research_page():
 assert 'let lastResearchTab="overview"' in PAGE
 assert 'if(tab!=="watchlist")lastResearchTab=tab;' in PAGE
 assert 'showRadarSection(isOpen?lastResearchTab:"watchlist")' in PAGE
 assert 'showRadarSection(lastResearchTab);' in PAGE
 assert 'classList.toggle("hidden",page.id!==tab)' in PAGE
def test_mobile_access_does_not_require_horizontal_menu_scroll():
 assert '@media(max-width:700px)' in CSS
 assert 'bottom:calc(15px + env(safe-area-inset-bottom,0px))' in CSS
 assert 'right:12px' in CSS
 assert 'border-radius:24px' in CSS
def test_no_watch_data_loss_or_feature_removal():
 for key in ('psi-radar-watch-v1','psi-radar-read-v1','psi-radar-bookmarks-v1'):
  assert key in PAGE
 for name in ('watch-bookmark-feed','watch-backup-export','watch-backup-file','watch-techs','watch-companies'):
  assert f'id="{name}"' in PAGE
