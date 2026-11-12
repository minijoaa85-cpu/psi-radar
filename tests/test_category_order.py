"""Keep the user-facing technology order consistent across all views and generated reports."""
import json
import re
from pathlib import Path
from scripts.architecture import CATS,compile_architecture
from scripts.briefing import CATEGORIES as BRIEF_CATS, build_briefing
from scripts.tech_topics import TOPICS, CATEGORIES as TOPIC_CATS
from scripts.weekly_report import CATS as WEEKLY_CATS
from scripts.collect import TECH, KEYS
from scripts.research import QUERIES
from scripts.validate_benchmark import load

BASE=Path(__file__).resolve().parents[1]
ORDER=("GaN","SiC","IGBT","SJ MOSFET","SGT")
def test_server_and_collection_category_order():
 assert CATS==BRIEF_CATS==TOPIC_CATS==WEEKLY_CATS==ORDER
 assert tuple(TECH)==tuple(KEYS)==ORDER
 assert tuple(QUERIES)==ORDER[2:]
def test_topic_groups_have_sj_before_sgt():
 order=list(dict.fromkeys(t["category"] for t in TOPICS))
 assert order==list(ORDER)
def test_dashboard_selects_have_sgt_last():
 html=(BASE/"site"/"index.html").read_text(encoding="utf-8")
 for id in ("cat","research-cat","company-tech","brief-category","arch-category","bench-category"):
  match=re.search(r'<select\s+id="'+re.escape(id)+r'"[^>]*>(.*?)</select>',html,re.S)
  assert match,id
  options=re.findall(r'<option[^>]*>([^<]+)</option>',match.group(1))
  filtered=[o for o in options if o in ORDER]
  assert filtered==list(ORDER),(id,filtered)
def test_overview_priority_cards_and_competitor_matrix_order():
 html=(BASE/"site"/"index.html").read_text(encoding="utf-8")
 overview=html.split('<section id="overview">',1)[1].split('</section>',1)[0]
 assert overview.index('<b>SJ · 10%</b>')<overview.index('<b>SGT · 10%</b>')
 assert 'const devices=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in html
 assert 'const counts=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in html
 assert "IGBT · SJ MOSFET" in html
def test_static_architecture_and_generated_briefing_order():
 payload=json.loads((BASE/"site"/"architecture.json").read_text(encoding="utf-8"))
 assert [r["category"] for r in payload["categories"]]==list(ORDER)
 assert [r["category"] for r in compile_architecture(load())["categories"]]==list(ORDER)
 brief=build_briefing([],"2026-11-12T00:00:00+00:00")
 assert [x["category"] for x in brief["categories"]]==list(ORDER)
