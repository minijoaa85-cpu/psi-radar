"""V1.5 concise reading-priority briefing from public, provenance-labelled metadata.

A priority is a reading order, NOT technical impact, verified product improvement,
market position, or a prediction. No extra AI/API requests are made.
"""
from __future__ import annotations
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from scripts.tech_topics import TOPICS, news_matches, evidence_kind

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"site"/"data.json"
OUT=ROOT/"site"/"briefing.json"
CATEGORIES=("GaN","SiC","IGBT","SGT","SJ MOSFET")
WINDOW_DAYS=30
MAX_PER_CATEGORY=16
MAX_SUMMARY_CHARS=220
ANNOUNCEMENT_TERMS=(
 "introduc","unveil","launch","release","expand","announc","debut",
 "발표","출시","확대","공개","신제품"
)
def valid_url(url):
 p=urlparse(url or "")
 return p.scheme=="https" and bool(p.hostname)
def parsed_day(value):
 try:return dt.date.fromisoformat(str(value)[:10])
 except (TypeError,ValueError):return None
def source_level(row):
 kind=evidence_kind(row)
 if kind=="manufacturer_announcement":return "official"
 if kind=="paper_metadata":return "research"
 return "news"
def candidate_change(title):
 s=(title or "").casefold()
 return any(x in s for x in ANNOUNCEMENT_TERMS)
def brief_summary(row):
 # No assertions about performance, novelty, commercialization or causality.
 s=(row.get("summary_ko") or "").strip()
 if row.get("kind")=="news":
  # Existing short summaries may be AI extrapolations from a headline;
  # read from the headline only, without ungrounded additional interpretations.
  return ("제목 기준: "+str(row.get("title_ko") or row.get("title") or "").strip())[:MAX_SUMMARY_CHARS]
 if row.get("kind")=="paper":
  return "공개 논문 메타데이터를 확인했습니다. 실험 결과와 데이터는 원문에서 검토해야 합니다."
 if row.get("source_type")=="manufacturer_official":
  if s and len(s)<=MAX_SUMMARY_CHARS:return "제조사 설명: "+s
  return "제조사가 공개한 기술·제품 발표입니다. 발표 내용은 제조사 주장으로 확인하세요."
 return ("공개자료 제목 기준: "+str(row.get("title_ko") or row.get("title") or ""))[:MAX_SUMMARY_CHARS]
def reading_score(row,days_old):
 # Reading priority: source provenance, then publication freshness,
 # then explicit title wording. Never score claimed engineering progress.
 type_=source_level(row)
 base={"official":300,"research":200,"news":100}[type_]
 return base+max(0,30-days_old)+(5 if candidate_change(str(row.get("title") or "")) else 0)
def build_briefing(records,generated):
 now=dt.datetime.fromisoformat(generated)
 if now.tzinfo is None:now=now.replace(tzinfo=dt.timezone.utc)
 today=now.date()
 categories=[]
 seen_global=set()
 for category in CATEGORIES:
  items=[]
  for r in records:
   if r.get("category")!=category or r.get("stale_reused") or not valid_url(r.get("url")):continue
   date=parsed_day(r.get("date"))
   if not date:continue
   age=(today-date).days
   if not 0<=age<=WINDOW_DAYS:continue
   url=r["url"]
   if url in seen_global:continue
   # Use source URL as a single canonical source item across the briefing.
   seen_global.add(url)
   matched=[t for t in TOPICS if t["category"]==category and news_matches(r,t)]
   type_=source_level(r)
   title=str(r.get("title_ko") or r.get("title") or "").strip()
   if not title:continue
   items.append({"id":str(r.get("id") or ""),"category":category,"title":title[:260],
    "date":date.isoformat(),"source":str(r.get("source") or "출처 미상")[:100],
    "url":url,"source_level":type_,
    "evidence_label":{"official":"제조사 공식 원문","research":"학술 논문 메타데이터","news":"기사 제목·원문 미검증"}[type_],
    "change_candidate":candidate_change(str(r.get("title") or "")+" "+title),
    "change_caution":"신제품·변화 관련 표현이 제목에 있음. 신규성·성과는 원문 검토 전 미확인." if candidate_change(str(r.get("title") or "")+" "+title) else None,
    "summary":brief_summary(r),"topic_ids":[t["id"] for t in matched],
    "reading_priority":reading_score(r,age),
    "priority_basis":"공식 출처/논문 메타데이터/뉴스 유형, 발행일, 제목 표현을 고려한 열람 순서",
    "evidence_status":"manufacturer_claim" if type_=="official" else "metadata_only" if type_=="research" else "title_not_verified"})
  items.sort(key=lambda x:(-x["reading_priority"],x["date"],x["title"]),reverse=False)
  # Ensure exact order: high priority first, recent first on ties.
  items.sort(key=lambda x:(x["reading_priority"],x["date"]),reverse=True)
  items=items[:MAX_PER_CATEGORY]
  totals={k:sum(x["source_level"]==k for x in items) for k in ("official","research","news")}
  categories.append({"category":category,"count":len(items),"by_source":totals,
   "new_announcement_title_candidates":sum(x["change_candidate"] for x in items),
   "items":items})
 return {"schema_version":1,"generated_at":generated,"lookback_days":WINDOW_DAYS,
 "categories":categories,
 "method":"Windowed and deduplicated source metadata. Reading order is provenance > recency > change words in title.",
 "warning":"중요도는 읽기 순서일 뿐 기술 성과나 경쟁력 평가가 아닙니다. 제목의 신규 발표 표현은 실제 최초 발표·양산·성능 향상의 검증이 아닙니다. 공식 발표는 제조사의 주장, 논문은 메타데이터, 일반 뉴스는 제목 기반 정보로 구분합니다.",
 "source_limit":"수집된 공공 원문 링크·메타데이터 범위이며 전체 산업의 완전한 발표 목록이 아닙니다."}
def main():
 data=json.loads(DATA.read_text(encoding="utf-8"))
 result=build_briefing(data.get("records",[]),data["generated_at"])
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Briefing:",sum(c["count"] for c in result["categories"]),"items from",len(result["categories"]),"technologies")
if __name__=="__main__":main()
