"""V1.9 saved-bookmark library: simple search, category filtering and correct delete mapping."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
CSS=HTML.split("<style>",1)[1].split("</style>",1)[0]
SCRIPT=HTML.split("<script>",1)[1].split("</script>",1)[0]

def test_search_category_sort_ui_present():
 for id in ("watch-saved-search","watch-saved-category","watch-saved-sort",
            "watch-saved-results","watch-saved-category-counts","watch-bookmark-feed"):
  assert HTML.count(f'id="{id}"')==1
 assert 'placeholder="제목·출처·링크 검색"' in HTML
 for category in ("GaN","SiC","IGBT","SJ MOSFET","SGT"):
  assert f'<option>{category}</option>' in HTML
 assert 'value="unknown"' in HTML
 for sort in ("saved-new","published-new","published-old","title"):
  assert f'value="{sort}"' in HTML

def test_saved_library_filters_only_saved_bookmarks():
 s=SCRIPT.split("function watchSavedItems(){",1)[1].split("function renderWatchBookmarks(){",1)[0]
 assert '[...WATCH_BOOKMARKS.values()]' in s
 assert 'el("watch-saved-search").value.trim()' in s
 assert 'el("watch-saved-category").value' in s
 assert "r.title,r.source,r.url" in s
 assert 'r.category===category' in s
 assert 'sort==="published-new"' in s and 'sort==="published-old"' in s
 assert 'sort==="title"' in s
 assert 'localeCompare(b.title,"ko")' in s

def test_bookmark_remove_after_sort_uses_filtered_item_index():
 assert "WATCH_BOOKMARK_VISIBLE=items;" in SCRIPT
 assert 'WATCH_BOOKMARK_VISIBLE[i])toggleWatchBookmark(WATCH_BOOKMARK_VISIBLE[i])' in SCRIPT
 assert "data-remove-bookmark" in SCRIPT
 assert 'WATCH_BOOKMARKS.delete(url)' in SCRIPT

def test_saved_search_updates_without_network_or_bookmark_rewrites():
 s=SCRIPT.split('for(const id of ["watch-saved-search"',1)[1].split('el("watch-bookmark-feed").addEventListener',1)[0]
 assert '"input":"change",renderWatchBookmarks' in s
 assert 'data-saved-category' in s
 assert 'fetch(' not in s and 'localStorage.setItem(' not in s
 assert 'renderWatchBookmarks();' in s

def test_saved_library_mobile_layout_and_previous_keys_unchanged():
 assert '.watch-saved-controls' in CSS
 assert '@media(max-width:420px)' in CSS
 assert 'grid-template-columns:1fr' in CSS
 for key in ("psi-radar-watch-v1","psi-radar-read-v1","psi-radar-bookmarks-v1"):
  assert key in HTML
 assert 'schema_version:1' in SCRIPT
 assert 'const WATCH_BOOKMARK_LIMIT=200' in SCRIPT
