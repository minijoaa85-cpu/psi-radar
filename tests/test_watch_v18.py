"""V1.8 saved bookmarks and local-only backup/restore regression safeguards."""
from pathlib import Path
import re
PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
CODE=PAGE.split("const WATCH_TECH_ORDER=",1)[1].split("let FINANCIAL_IR=",1)[0]

def test_saved_article_shelf_and_filter_controls():
 for id in ("watch-bookmark-section","watch-bookmark-feed","watch-bookmark-count",
            "watch-bookmarked-only","watch-backup-export","watch-backup-file"):
  assert f'id="{id}"' in PAGE
 assert 'const WATCH_BOOKMARK_KEY="psi-radar-bookmarks-v1"' in CODE
 assert "WATCH_BOOKMARKS.has(r.url)" in CODE
 assert 'id="watch-bookmark-section" open' in PAGE
 assert "북마크한 공개 원문 링크는 최근 30일 범위를 지나도" in PAGE

def test_bookmark_action_has_persistent_storage_and_safe_html():
 assert "localStorage.getItem(WATCH_BOOKMARK_KEY)" in CODE
 assert "localStorage.setItem(WATCH_BOOKMARK_KEY" in CODE
 assert 'WATCH_BOOKMARK_LIMIT=200' in CODE
 assert 'renderWatchBookmarks();' in CODE
 assert 'toggleWatchBookmark(WATCH_VISIBLE_ITEMS[index])' in CODE
 assert 'esc(r.url)' in CODE and 'esc(r.title)' in CODE
 assert 'u.protocol==="https:"' in CODE
 assert 'new URL(value)' in CODE

def test_json_backup_is_user_initiated_and_download_only():
 assert 'el("watch-backup-export").addEventListener("click"' in CODE
 assert 'new Blob([payload],{type:"application/json;charset=utf-8"})' in CODE
 assert 'URL.createObjectURL(blob)' in CODE
 assert 'link.download="psi-radar-my-watch-backup.json"' in CODE
 assert 'link.click()' in CODE
 assert 'URL.revokeObjectURL(objectUrl)' in CODE
 assert "fetch(" not in CODE
 assert "navigator.sendBeacon" not in CODE

def test_import_validates_before_confirm_and_local_write():
 assert 'value.app!=="PSI Radar My Watch"' in CODE
 assert 'value.schema_version!==1' in CODE
 assert 'file.size>512*1024' in CODE
 assert 'value.read_urls.length>WATCH_READ_LIMIT' in CODE
 assert 'value.bookmarks.length>WATCH_BOOKMARK_LIMIT' in CODE
 assert 'value.read_urls.every(watchValidUrl)' in CODE
 confirm=CODE.index('window.confirm("현재 브라우저')
 write=CODE.index('localStorage.setItem(WATCH_STORAGE_KEY,JSON.stringify(backup.prefs))')
 assert confirm<write
 assert 'localStorage.setItem(WATCH_READ_STORAGE_KEY,JSON.stringify(backup.read))' in CODE
 assert 'localStorage.setItem(WATCH_BOOKMARK_KEY,JSON.stringify(backup.bookmarks))' in CODE
 assert 'e.target.value=""' in CODE
 assert '백업 복원을 완료했습니다' in CODE

def test_bookmark_iso_date_regex_and_mobile_styles():
 assert r'/^\d{4}-\d{2}-\d{2}$/' in CODE
 assert r'/^\\d{4}-\\d{2}-\\d{2}$/' not in CODE
 css=PAGE.split("<style>",1)[1].split("</style>",1)[0]
 assert "watch-bookmark-feed" in css
 assert "@media(max-width:720px){.watch-bookmark-feed{grid-template-columns:1fr}}" in css
 assert 'data-bookmark-index' in CODE and 'data-remove-bookmark' in CODE

def test_old_preferences_and_reading_status_survive_upgrade():
 assert 'const WATCH_STORAGE_KEY="psi-radar-watch-v1"' in CODE
 assert 'const WATCH_READ_STORAGE_KEY="psi-radar-read-v1"' in CODE
 assert 'const WATCH_TECH_ORDER=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in PAGE
 assert 'el("watch-clear-read")' in CODE
 assert 'el("watch-reset")' in CODE
