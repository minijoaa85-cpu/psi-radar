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

def test_sunday_afternoon_is_not_mistaken_for_full_week():
 when=dt.datetime(2026,11,15,15,0,tzinfo=KST)
 assert kst_week(when)==("2026-W46","2026-11-09","2026-11-15",False)

def test_v14_research_focus_uses_same_week_same_category_denominator():
 when=dt.datetime(2026,11,12,10,0,tzinfo=KST)
 articles=[row("r"+str(i),"Trench MOSFET SiC gate oxide reliability" if i<2 else "SiC high voltage semiconductor","2026-11-10",category="SiC",kind="paper") for i in range(6)]
 snap=build_snapshot({"generated_at":when.isoformat(),"records":articles},when)
 t=next(x for x in snap["topics"] if x["topic_id"]=="sic-oxide")
 assert t["research_sample_count"]==6
 assert t["research_topic_count"]==2
 assert t["research_share_of_sample_pct"]==33.3
 assert t["topic_share_of_sample_pct"]==33.3

def test_v14_small_research_sample_never_shows_percent():
 when=dt.datetime(2026,11,12,10,0,tzinfo=KST)
 entries=[row(str(i),"Gate oxide reliability SiC","2026-11-10",category="SiC",kind="paper") for i in range(4)]
 snap=build_snapshot({"generated_at":when.isoformat(),"records":entries},when)
 t=next(x for x in snap["topics"] if x["topic_id"]=="sic-oxide")
 assert t["research_topic_count"]==4
 assert t["research_share_of_sample_pct"] is None

def test_v14_old_manufacturer_press_release_not_misidentified_new():
 when=dt.datetime(2026,11,12,10,0,tzinfo=KST)
 old=row("old-official","Field stop trench IGBT new release","2026-09-01",category="IGBT",kind="official",source_type="manufacturer_official")
 recent=row("new-official","Field stop trench IGBT technology","2026-11-10",category="IGBT",kind="official",source_type="manufacturer_official")
 news=row("new-news","Field-stop trench IGBT news","2026-11-10",category="IGBT")
 snap=build_snapshot({"generated_at":when.isoformat(),"records":[old,recent,news]},when)
 t=next(x for x in snap["topics"] if x["topic_id"]=="igbt-field")
 assert t["source_kinds"]=={"manufacturer_announcement":1,"news_title_candidate":1}
 assert len(t["new_official_announcements"])==1
 assert t["new_official_announcements"][0]["url"]==recent["url"]
 assert t["count"]==2

def test_v14_category_sample_dedupes_article_url_in_denominator():
 when=dt.datetime(2026,11,12,10,0,tzinfo=KST)
 first=row("dup","SiC gate oxide reliability","2026-11-10",category="SiC",kind="paper")
 second={**first,"id":"duplicate-key"}
 snap=build_snapshot({"generated_at":when.isoformat(),"records":[first,second]},when)
 t=next(x for x in snap["topics"] if x["topic_id"]=="sic-oxide")
 assert t["count"]==1 and t["research_sample_count"]==1

def test_v14_dashboard_labels_do_not_rank_manufacturer_quality():
 from pathlib import Path
 page=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
 assert 'id="arch-source-summary"' in page
 assert 'id="arch-research-focus"' in page
 assert 'id="arch-official-evidence"' in page
 assert "연구 주제 집중도 · 표본 관측치" in page
 assert "전체 산업 연구 비중이 아닙니다" in page
 assert "공식 발표" in page
