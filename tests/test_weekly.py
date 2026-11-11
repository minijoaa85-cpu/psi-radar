import datetime as dt
from zoneinfo import ZoneInfo
from scripts.relevance import relevance,annotate
from scripts.weekly_report import week_id,week_start,build_digest

KST=ZoneInfo("Asia/Seoul")
def test_relevance_explainable():
 detailed={"kind":"paper","title":"Improved gate oxide reliability of trench IGBT","abstract":"Threshold voltage instability and short circuit measured","doi":"10.1/a"}
 generic={"kind":"paper","title":"IGBT overview","abstract":"","doi":""}
 a,b=relevance(detailed),relevance(generic)
 assert a["relevance_score"]>b["relevance_score"]
 assert "Reliability" in a["relevance_topics"]
 assert a["relevance_method"]=="metadata-rule-v1"
def test_equal_technical_relevance_for_equal_priority_categories():
 row={"kind":"paper","title":"Trench MOSFET gate oxide reliability","abstract":"electric field","doi":"10.1/a"}
 assert relevance(dict(row,category="IGBT"))["relevance_score"]==relevance(dict(row,category="SGT"))["relevance_score"]==relevance(dict(row,category="SJ MOSFET"))["relevance_score"]
def test_archive_week_boundaries_kst():
 value=dt.datetime(2026,11,15,21,5,tzinfo=dt.timezone.utc)
 assert week_start(value)=="2026-11-16"
 assert week_id(value)=="2026-W47"
def test_baseline_and_prior_week_delta():
 when=dt.datetime(2026,11,16,9,tzinfo=KST)
 rows=[
  {"id":"new","category":"GaN","kind":"news","title":"650V GaN data center","date":"2026-11-16","relevance_score":80,"url":"https://example.org/1"},
  {"id":"old","category":"IGBT","kind":"paper","title":"IGBT trench","date":"2026-10-10","relevance_score":85,"url":"https://example.org/2"},
  {"id":"excluded","category":"SiC","kind":"paper","title":"SiC reliability","date":"2026-11-16","stale_reused":True,"relevance_score":70},
 ]
 data={"records":rows,"generated_at":when.isoformat(),"errors":[]}
 first=build_digest(data,when)
 assert first["baseline"] and first["published_this_week_count"]==1
 assert first["research_reference_count"]==2
 assert first["new_items_count"]==1
 previous={"all_ids":["old"],"week":"2026-W46"}
 later=build_digest(data,when,previous)
 assert not later["baseline"] and later["new_items_count"]==1
 assert later["new_items"][0]["id"]=="new"
 assert "abstract" not in later["research_highlights"][0]
def test_relevance_annotations_preserve_source_fields():
 r={"id":"x","title":"superjunction MOSFET reverse recovery","kind":"paper","date":"2026-10-01"}
 annotate([r])
 assert r["id"]=="x" and isinstance(r["relevance_reasons"],list)
