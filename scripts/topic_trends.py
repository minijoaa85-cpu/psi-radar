"""V1.3: Auditable weekly *observed publication* topic statistics.
No missing-week zero filling, no fabricated historical growth, no performance rankings.
"""
from __future__ import annotations
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo
from scripts.tech_topics import TOPICS, news_matches, safe_url, evidence_kind

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"site"/"data.json"
OUT=ROOT/"site"/"topic_trends"
KST=ZoneInfo("Asia/Seoul")
MAX_CARDS=5
def kst_week(now):
 local=now.astimezone(KST)
 # Scheduled 06:00 Monday run covers the fully completed previous Mon-Sun.
 # Manual and push builds on other days show an explicitly incomplete current week.
 if local.weekday()==0 and local.hour<12:
  end=local.date()-dt.timedelta(days=1)
  complete=True
 else:
  end=local.date()
  complete=False
 year,week,_=end.isocalendar()
 start=end-dt.timedelta(days=end.weekday())
 return f"{year}-W{week:02d}",start.isoformat(),end.isoformat(),complete
def company_ids(row):
 # Use conservative title/official attribution from the collector; never infer an owner from keywords.
 return sorted({k for k in row.get("companies",[]) if isinstance(k,str) and k})
def build_snapshot(data,now=None):
 if now is None:
  now=dt.datetime.fromisoformat(data["generated_at"])
 if now.tzinfo is None:now=now.replace(tzinfo=dt.timezone.utc)
 wid,start,end,complete=kst_week(now)
 entries=[]
 for topic in TOPICS:
  matched=[]
  for row in data.get("records",[]):
   # Report published-in-week coverage, NOT discovered-in-week:
   # old references and older 30-day fallback cannot count as newly published.
   day=row.get("date") or ""
   if not (start<=day<=end) or row.get("stale_reused") or not safe_url(row.get("url")):
    continue
   if news_matches(row,topic):
    matched.append(row)
  # Unique URL per topic; prevents duplicates from repeated RSS/indexing.
  distinct={r["url"]:r for r in matched}
  found=sorted(distinct.values(),key=lambda r:(r.get("date") or "",r.get("title") or ""),reverse=True)
  counts=defaultdict(int)
  kinds=defaultdict(int)
  for row in found:
   kinds[evidence_kind(row)]+=1
   for company in company_ids(row):counts[company]+=1
  cards=[{"id":str(r.get("id") or ""),"title":str(r.get("title_ko") or r.get("title") or "")[:200],
          "date":r.get("date") or "","kind":evidence_kind(r),"source":str(r.get("source") or "")[:80],"url":r["url"]} for r in found[:MAX_CARDS]]
  entries.append({"topic_id":topic["id"],"category":topic["category"],"name":topic["name"],
                  "count":len(found),"source_kinds":dict(kinds),
                  "company_mentions":dict(sorted(counts.items(),key=lambda x:(-x[1],x[0]))),
                  "evidence":cards})
 return {"schema_version":1,"week":wid,"week_start":start,"week_to_date":end,"complete_week":complete,
         "generated_at":data.get("generated_at"),"coverage":"saved_collection_publication_date_snapshot",
         "topics":entries,"warning":"현재 주차에 발행일이 속하는 수집 표본만 집계합니다. 과거 주차 0건을 자동 생성하지 않으며, 기사 검색·재수집 범위가 달라질 수 있어 절대적인 업계 성장률이 아닙니다. 기업 집계는 제목에서 확인된 기업명 언급 횟수입니다."}
def main():
 data=json.loads(SOURCE.read_text(encoding="utf-8"))
 now=dt.datetime.fromisoformat(data["generated_at"])
 if now.tzinfo is None:now=now.replace(tzinfo=dt.timezone.utc)
 snapshot=build_snapshot(data,now)
 OUT.mkdir(parents=True,exist_ok=True)
 name=snapshot["week"]+".json"
 (OUT/name).write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
 index=[]
 for p in sorted(OUT.glob("????-W??.json"),reverse=True)[:104]:
  try:
   v=json.loads(p.read_text(encoding="utf-8"))
   index.append({"week":v["week"],"start":v["week_start"],
                 "generated_at":v.get("generated_at"),"file":"topic_trends/"+p.name})
  except (OSError,ValueError,KeyError):continue
 (OUT/"index.json").write_text(json.dumps({"schema_version":1,"generated_at":data.get("generated_at"),
    "weeks":index,"notice":"해당 주차의 마지막 실행 스냅샷만 유지합니다. 이전 주차가 없으면 차트를 0으로 채우지 않습니다."},
    ensure_ascii=False,indent=2),encoding="utf-8")
 print("Topic trends:",snapshot["week"],"topics:",len(snapshot["topics"]),
       "matched:",sum(t["count"] for t in snapshot["topics"]),"weeks:",len(index))
if __name__=="__main__":main()
