"""V1.3: no fictional growth, deduplicated evidence, safe company attribution."""
import datetime as dt
from zoneinfo import ZoneInfo
from scripts.topic_trends import build_snapshot,kst_week
from scripts.tech_topics import TOPICS

KST=ZoneInfo("Asia/Seoul")
def row(ident,title,day,category="GaN",**extra):
 return {"id":ident,"title":title,"date":day,"url":"https://example.org/"+ident,
         "kind":"news","category":category,**extra}
def test_monday_morning_reports_finished_previous_week():
 when=dt.datetime(2026,11,16,6,0,tzinfo=KST)
 assert kst_week(when)==("2026-W46","2026-11-09","2026-11-15",True)
def test_midweek_is_partial_and_not_backfilled():
 when=dt.datetime(2026,11,12,10,0,tzinfo=KST)
 assert kst_week(when)==("2026-W46","2026-11-09","2026-11-12",False)
 data={"generated_at":when.isoformat(),"records":[]}
 snap=build_snapshot(data,when)
 assert snap["complete_week"] is False
 assert all(x["count"]==0 for x in snap["topics"])
 assert "이전 주차" not in snap or "이전 주차" in snap["warning"]
def test_title_matched_week_dedupe_and_company_mentions():
 when=dt.datetime(2026,11,12,10,tzinfo=KST)
 a=row("1","Mitsubishi Electric reduces frequency dispersion in GaN transistors","2026-11-10",companies=["mitsubishi"])
 duplicate={**a,"id":"2"}
 old=row("old","GaN frequency dispersion","2026-10-15",companies=["mitsubishi"])
 extra=row("other","GaN dynamic RDS(on) publication","2026-11-11",companies=["innoscience"],kind="paper")
 data={"generated_at":when.isoformat(),"records":[a,duplicate,old,extra]}
 snap=build_snapshot(data,when)
 topic=next(x for x in snap["topics"] if x["topic_id"]=="gan-dynamic-ron")
 assert topic["count"]==2
 assert topic["company_mentions"]=={"innoscience":1,"mitsubishi":1}
 assert topic["source_kinds"]=={"news_title_candidate":1,"paper_metadata":1}
 assert len(topic["evidence"])==2
def test_stale_reused_article_not_counted_even_if_date_in_week():
 when=dt.datetime(2026,11,12,10,tzinfo=KST)
 row1=row("stale","GaN dynamic RDS(on)","2026-11-11",stale_reused=True,companies=["infineon"])
 snap=build_snapshot({"generated_at":when.isoformat(),"records":[row1]},when)
 assert next(t for t in snap["topics"] if t["topic_id"]=="gan-dynamic-ron")["count"]==0
def test_official_is_distinct_from_headline_news():
 when=dt.datetime(2026,11,12,10,tzinfo=KST)
 r=row("x","Gate charge and switching loss in GaN","2026-11-10",kind="official",source_type="manufacturer_official",companies=["st"])
 snap=build_snapshot({"generated_at":when.isoformat(),"records":[r]},when)
 t=next(t for t in snap["topics"] if t["topic_id"]=="gan-switching")
 assert t["source_kinds"]=={"manufacturer_announcement":1}
 assert t["company_mentions"]=={"st":1}
def test_dashboard_uses_only_saved_weeks_and_filters_by_topic():
 from pathlib import Path
 page=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
 assert "topic_trends/index.json" in page
 assert "TREND_SNAPSHOTS.filter" in page
 assert "실제 저장" in page
 assert "기록되지 않은 주차를 0건으로 처리하지 않습니다" in page
 assert "arch-trend-companies" in page
 assert "data-week" in page
