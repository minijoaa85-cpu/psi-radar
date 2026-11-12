"""V1.6 My Watch privacy, filter wiring and attribution regression checks."""
import json
import re
from pathlib import Path
from scripts.briefing import build_briefing

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
ORDER=("GaN","SiC","IGBT","SJ MOSFET","SGT")
def sample(id,kind,title,category="GaN",**kwargs):
 return {"id":id,"kind":kind,"category":category,"title":title,
  "date":"2026-11-11","url":"https://example.org/"+id,"source":"Sample",**kwargs}
def test_briefing_carries_known_company_ids_only():
 data=build_briefing([
  sample("one","news","Infineon GaN HEMT","GaN",companies=["infineon","not_a_vendor","infineon"]),
  sample("two","paper","SiC oxide report","SiC"),
 ],"2026-11-12T04:00:00+00:00")
 gan=next(c for c in data["categories"] if c["category"]=="GaN")
 assert gan["items"][0]["companies"]==["infineon"]
 sic=next(c for c in data["categories"] if c["category"]=="SiC")
 assert sic["items"][0]["companies"]==[]
def test_company_name_in_source_without_attribution_not_assumed():
 data=build_briefing([sample("one","news","Power GaN HEMT breakthrough","GaN",source="Infineon")],"2026-11-12T04:00:00+00:00")
 assert data["categories"][0]["items"][0]["companies"]==[]
def test_all_watch_controls_exist_and_nav_route():
 assert 'data-tab="watchlist"' in HTML
 for id in ("watchlist","watch-techs","watch-companies","watch-save","watch-reset","watch-status",
            "watch-official-only","watch-require-company","watch-kpi","watch-feed"):
  assert f'id="{id}"' in HTML
 assert 'const WATCH_STORAGE_KEY="psi-radar-watch-v1"' in HTML
def test_local_storage_only_and_no_network_account_for_preferences():
 assert "localStorage.getItem(WATCH_STORAGE_KEY)" in HTML
 assert "localStorage.setItem(WATCH_STORAGE_KEY" in HTML
 assert "localStorage.removeItem(WATCH_STORAGE_KEY)" in HTML
 assert "다른 기기에는 동기화되지 않습니다" in HTML
 assert "실시간 푸시 알림·메일·클라우드 계정 저장 기능은 없습니다" in HTML
 assert "WATCH_COMPANY_IDS.has(id)" in HTML
def test_fixed_technology_order_and_manufacturer_interaction():
 pattern=r'const WATCH_TECH_ORDER=\[([^\]]+)\]'
 match=re.search(pattern,HTML)
 assert match
 assert tuple(json.loads("["+match.group(1)+"]"))==ORDER
 assert 'prefs.companies.includes(id)' in HTML
 assert 'renderWatchFeed();' in HTML
 assert 'BRIEFING=data;' in HTML
def test_missing_matching_items_are_not_claimed_as_missing_industry():
 assert "선택 자료 0건은 관련 산업 활동이 없다는 의미가 아닙니다" in HTML
