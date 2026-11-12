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
def eligible_week_rows(rows,start,end):
 """Shared, deduplicated observation base for both topic numerators and category denominators."""
 seen=set()
 result=[]
 for row in rows:
  day=row.get("date") or ""
  if not (start<=day<=end) or row.get("stale_reused") or not safe_url(row.get("url")):
   continue
  url=row["url"]
  if url in seen:continue
  seen.add(url)
  result.append(row)
 return result

def source_kind_counts(rows):
 counts=defaultdict(int)
 for row in rows:counts[evidence_kind(row)]+=1
 return dict(counts)

def build_snapshot(data,now=None):
 if now is None:
  now=dt.datetime.fromisoformat(data["generated_at"])
 if now.tzinfo is None:now=now.replace(tzinfo=dt.timezone.utc)
 wid,start,end,complete=kst_week(now)
 observed=eligible_week_rows(data.get("records",[]),start,end)
 entries=[]
 for topic in TOPICS:
  # Same category, same week, unique-URL observation base.
  category_sample=[r for r in observed if r.get("category")==topic["category"]]
  matched=[r for r in category_sample if news_matches(r,topic)]
  found=sorted(matched,key=lambda r:(r.get("date") or "",r.get("title") or ""),reverse=True)
  paper_sample=[r for r in category_sample if evidence_kind(r)=="paper_metadata"]
  paper_matches=[r for r in found if evidence_kind(r)=="paper_metadata"]
  # These are within-sample descriptive fractions, NOT field-wide publication trends.
  sample_size=len(category_sample)
  research_sample_size=len(paper_sample)
  counts=defaultdict(int)
  kinds=defaultdict(int)
  for row in found:
   kinds[evidence_kind(row)]+=1
   for company in company_ids(row):counts[company]+=1
  cards=[{"id":str(r.get("id") or ""),"title":str(r.get("title_ko") or r.get("title") or "")[:200],
          "date":r.get("date") or "","kind":evidence_kind(r),"source":str(r.get("source") or "")[:80],"url":r["url"]} for r in found[:MAX_CARDS]]
  official=[r for r in found if evidence_kind(r)=="manufacturer_announcement"]
  def cards_for(items,limit=4):
   return [{"title":str(r.get("title_ko") or r.get("title") or "")[:200],
            "date":r.get("date") or "","source":str(r.get("source") or "")[:80],
            "url":r["url"]} for r in items[:limit]]
  entries.append({"topic_id":topic["id"],"category":topic["category"],"name":topic["name"],
                  "count":len(found),"source_kinds":dict(kinds),
                  "category_sample_count":sample_size,
                  "topic_share_of_sample_pct":round(len(found)*100/sample_size,1) if sample_size>=5 else None,
                  "research_sample_count":research_sample_size,
                  "research_topic_count":len(paper_matches),
                  "research_share_of_sample_pct":round(len(paper_matches)*100/research_sample_size,1) if research_sample_size>=5 else None,
                  "new_official_announcements":cards_for(official),
                  "research_evidence":cards_for(paper_matches),
                  "company_mentions":dict(sorted(counts.items(),key=lambda x:(-x[1],x[0]))),
                  "evidence":cards})
 return {"schema_version":2,"week":wid,"week_start":start,"week_to_date":end,"complete_week":complete,
         "generated_at":data.get("generated_at"),"coverage":"saved_collection_publication_date_snapshot", "counting_unit":"distinct_source_urls",
         "topics":entries,"warning":"현재 주차에 발행일이 속하는 수집 표본만 집계합니다. 과거 주차 0건을 자동 생성하지 않으며, 기사 검색·재수집 범위가 달라질 수 있어 절대적인 업계 성장률이 아닙니다. 기업 집계는 제목에서 확인된 기업명 언급 횟수입니다. 연구 집중도는 동일 주차·동일 기술군의 수집 논문 표본에서 제목이 일치한 비율일 뿐 업계 전체 연구 집중도가 아닙니다. 표본이 5건 미만일 때 백분율을 표시하지 않습니다."}
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
