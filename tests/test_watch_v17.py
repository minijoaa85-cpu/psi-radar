"""V1.7 My Watch bulk selection and browser-local reading state regression checks."""
from pathlib import Path
import re

PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
WATCH=PAGE.split('const WATCH_TECH_ORDER=',1)[1].split('let BRIEFING=',1)[0]
def test_bulk_select_controls_in_both_groups():
 for group in ("tech","company"):
  assert f'data-watch-select="{group}" data-action="all"' in PAGE
  assert f'data-watch-select="{group}" data-action="none"' in PAGE
 assert 'id="watch-tech-count"' in PAGE
 assert 'id="watch-company-count"' in PAGE
 assert 'document.querySelectorAll("[data-watch-select]")' in WATCH
 assert 'input.checked=checked' in WATCH
 assert 'updateWatchSelectionCounts()' in WATCH
def test_read_unread_controls_and_local_only_storage():
 for id in ("watch-unread-only","watch-mark-all-read","watch-clear-read"):
  assert f'id="{id}"' in PAGE
 assert 'const WATCH_READ_STORAGE_KEY="psi-radar-read-v1"' in WATCH
 assert 'localStorage.getItem(WATCH_READ_STORAGE_KEY)' in WATCH
 assert 'localStorage.setItem(WATCH_READ_STORAGE_KEY' in WATCH
 assert 'localStorage.removeItem(WATCH_READ_STORAGE_KEY)' in WATCH
 assert "setWatchRead(row.url,!WATCH_READ.has(row.url))" in WATCH
 assert "if(el(\"watch-unread-only\").checked)items=items.filter(r=>!WATCH_READ.has(r.url));" in WATCH
def test_read_stats_calculated_before_unread_filter():
 before=WATCH.index("const totalBeforeUnread=items.length")
 after=WATCH.index('if(el("watch-unread-only").checked)')
 assert before<after
 assert '(totalBeforeUnread-unread)+"건"' in WATCH
 assert 'WATCH_VISIBLE_ITEMS=items.slice(0,30);' in WATCH
 assert 'el("watch-mark-all-read").disabled=!WATCH_VISIBLE_ITEMS.length;' in WATCH
def test_no_false_new_article_claims():
 assert "최근 새로 발표된 자료라는 뜻은 아닙니다" in PAGE
 assert "미열람 0건은 신규 기사 0건을 의미하지 않습니다" in PAGE
 assert "선택 자료 0건은 관련 산업 활동이 없다는 의미가 아닙니다" in PAGE
def test_existing_watchlist_and_technology_order_unchanged():
 assert 'const WATCH_TECH_ORDER=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in PAGE
 assert 'localStorage.setItem(WATCH_STORAGE_KEY' in WATCH
 assert 'el("watch-save").addEventListener("click"' in WATCH
 assert 'el("watch-reset").addEventListener("click"' in WATCH
def test_phone_select_all_and_read_css():
 css=PAGE.split("<style>",1)[1].split("</style>",1)[0]
 assert ".watch-bulk" in css and ".watch-read-help" in css
 assert ".watch-read-toggle" in css
 assert "min-height:36px" in css
