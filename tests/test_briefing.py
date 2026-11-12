"""V1.5 briefing: prioritize reading without pretending to verify technology impact."""
import datetime as dt
from pathlib import Path
from scripts.briefing import build_briefing,reading_score

STAMP="2026-11-12T09:00:00+00:00"
def row(id,kind,title,date="2026-11-11",category="GaN",**kwargs):
 return {"id":id,"kind":kind,"title":title,"date":date,"category":category,
         "url":"https://example.org/"+id,"source":"Sample",**kwargs}
def test_official_evidence_is_first_and_cautioned():
 records=[
  row("news","news","GaN HEMT launch reported"),
  row("official","official","Manufacturer releases GaN HEMT",source_type="manufacturer_official"),
  row("paper","paper","GaN HEMT gate reliability paper"),
 ]
 items=build_briefing(records,STAMP)["categories"][0]["items"]
 assert [r["source_level"] for r in items]==["official","research","news"]
 assert items[0]["evidence_status"]=="manufacturer_claim"
 assert items[0]["change_candidate"] and "미확인" in items[0]["change_caution"]
 assert items[1]["evidence_status"]=="metadata_only"
 assert items[2]["evidence_status"]=="title_not_verified"
def test_older_articles_and_future_articles_excluded():
 records=[row("old","news","GaN transistor","2026-09-01"),row("new","news","GaN transistor"),row("future","news","GaN transistor","2027-01-01")]
 out=build_briefing(records,STAMP)
 assert [r["id"] for r in out["categories"][0]["items"]]==["new"]
def test_duplicate_url_not_double_counted():
 a=row("1","news","GaN gate reliability")
 b={**a,"id":"other"}
 b["url"]=a["url"]
 out=build_briefing([a,b],STAMP)
 assert out["categories"][0]["count"]==1
def test_nonofficial_type_cannot_become_manufacturer_official():
 a=row("fraud","news","Company officially announces GaN devices")
 out=build_briefing([a],STAMP)
 assert out["categories"][0]["items"][0]["source_level"]=="news"
def test_technical_change_word_is_not_technical_rank():
 a=row("new","news","GaN device launches")
 out=build_briefing([a],STAMP)
 item=out["categories"][0]["items"][0]
 assert item["change_candidate"]
 assert "기술 성과" in out["warning"]
 assert "열람 순서" in item["priority_basis"]
def test_all_five_technology_categories_and_empty_support():
 result=build_briefing([],STAMP)
 assert {x["category"] for x in result["categories"]}=={"GaN","SiC","IGBT","SGT","SJ MOSFET"}
 assert all(x["count"]==0 for x in result["categories"])
def test_briefing_page_is_interactive_and_source_clear():
 s=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
 for key in ("brief-category","brief-type","brief-change","brief-summary","brief-feed"):
  assert 'id="'+key+'"' in s
 assert 'data-tab="briefing"' in s
 assert "briefing.json?nocache=" in s
 assert "변화 표현" in s
