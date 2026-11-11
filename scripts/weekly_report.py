"""Persist one immutable-ish (updated within same week) Korean weekly digest per ISO week.
Journal references are explicitly separate from the seven-day news bulletin.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"site"/"data.json"
REPORTS=ROOT/"site"/"reports"
KST=ZoneInfo("Asia/Seoul")
CATS=("GaN","SiC","IGBT","SGT","SJ MOSFET")
def week_id(value):
 local=value.astimezone(KST) if value.tzinfo else value.replace(tzinfo=KST)
 y,w,_=local.isocalendar()
 return f"{y}-W{w:02d}"
def week_start(value):
 local=value.astimezone(KST)
 return (local.date()-dt.timedelta(days=local.weekday())).isoformat()
def preview(row):
 keys=("id","kind","category","title","title_ko","summary_ko","summary_status","date","source","url","doi","relevance_score","relevance_level","relevance_reasons","relevance_topics","stale_reused","companies","company_attribution","company_source_status","device_mentions")
 out={k:row[k] for k in keys if k in row}
 for key in ("title","title_ko","summary_ko"):
  if key in out:out[key]=str(out[key])[:700]
 return out
def build_digest(data,when,prior=None):
 wid=week_id(when);start=week_start(when)
 # Explicit publication-week selection; no old research can inflate fresh news counts.
 newest=[r for r in data.get("records",[]) if r.get("date") and start<=r["date"]<=when.astimezone(KST).date().isoformat() and not r.get("stale_reused")]
 seen=set(str(x) for x in (prior or {}).get("all_ids",[]))
 first=prior is None
 selected=sorted(newest,key=lambda r:(int(r.get("relevance_score") or 0),int(r.get("score") or 0)),reverse=True)
 fresh=[r for r in selected if r.get("id") not in seen]
 research=sorted([r for r in data.get("records",[]) if r.get("kind")=="paper"],key=lambda r:(int(r.get("relevance_score") or 0),r.get("date") or ""),reverse=True)
 return {"schema_version":1,"week":wid,"week_start":start,"generated_at":data.get("generated_at"),"baseline":first,
         "new_items_count":len(fresh),"published_this_week_count":len(newest),"research_reference_count":len(research),
         "total_collection_count":len(data.get("records",[])),
         "by_category":{c:sum(r.get("category")==c for r in newest) for c in CATS},
         "company_mentions":{key:sum(key in r.get("companies",[]) for r in newest) for key in data.get("competitor_stats",{})},
         "new_items":[preview(r) for r in fresh[:20]],"weekly_items":[preview(r) for r in selected[:20]],
         "research_highlights":[preview(r) for r in research[:12]],
         # Bounded all-id list for next week delta detection, not shown in UI.
         "all_ids":sorted({r.get("id") for r in data.get("records",[]) if r.get("id")}),
         "collection_errors":len(data.get("errors",[])),
         "ai_usage":{"calls":data.get("ai_usage",{}).get("calls",0),"successes":data.get("ai_usage",{}).get("successes",0),
                      "failures":data.get("ai_usage",{}).get("failures",0),"estimated_cost_usd":data.get("ai_usage",{}).get("estimated_cost_usd",0)},
         "notice":"자동 수집 메타데이터·AI 요약은 원문 검증 전입니다. 학술지 참고자료는 이번 주 신규 발표와 별개입니다."}
def main():
 data=json.loads(SOURCE.read_text(encoding="utf-8"))
 when=dt.datetime.fromisoformat(data["generated_at"])
 if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
 REPORTS.mkdir(parents=True,exist_ok=True)
 wid=week_id(when)
 candidates=sorted(REPORTS.glob("????-W??.json"))
 older=[p for p in candidates if p.stem<wid]
 prior=json.loads(older[-1].read_text(encoding="utf-8")) if older else None
 digest=build_digest(data,when,prior)
 (REPORTS/(wid+".json")).write_text(json.dumps(digest,ensure_ascii=False,indent=2),encoding="utf-8")
 entries=[]
 for path in sorted(REPORTS.glob("????-W??.json"),reverse=True)[:104]:
  try:
   x=json.loads(path.read_text(encoding="utf-8"))
   entries.append({"week":x["week"],"week_start":x["week_start"],"generated_at":x.get("generated_at"),
                   "new_items_count":x.get("new_items_count",0),"published_this_week_count":x.get("published_this_week_count",0),
                   "research_reference_count":x.get("research_reference_count",0),
                   "baseline":x.get("baseline",False),"file":"reports/"+path.name})
  except (OSError,ValueError,KeyError):continue
 (REPORTS/"index.json").write_text(json.dumps({"schema_version":1,"generated_at":data.get("generated_at"),"reports":entries},ensure_ascii=False,indent=2),encoding="utf-8")
 print("Weekly archive:",wid,"baseline:",digest["baseline"],"new:",digest["new_items_count"],"research references:",digest["research_reference_count"],"archives:",len(entries))
if __name__=="__main__":main()
