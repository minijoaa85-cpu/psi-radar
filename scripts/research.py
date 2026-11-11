"""Additional focused journal discovery for IGBT, shielded-gate and SJ MOSFET.
Uses publication metadata only; never claims to read paywalled full text.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import time
import requests
from scripts.collect import clean, relevant, classify_topics, score

QUERIES={
 "IGBT": ["IGBT trench field stop", "reverse conducting IGBT", "IGBT short circuit reliability"],
 "SGT": ["shielded gate trench MOSFET", "split gate trench power MOSFET", "shielded gate MOSFET"],
 "SJ MOSFET": ["superjunction MOSFET reverse recovery", "superjunction MOSFET charge balance", "super junction power MOSFET"]
}
FOCUSED=("IEEE Transactions on Electron Devices","IEEE Journal of the Electron Devices Society",
 "IEEE Transactions on Power Electronics","Microelectronics Reliability",
 "Solid-State Electronics","IEEE Access","IEEE Transactions on Industry Applications",
 "IEEE Transactions on Industrial Electronics","Journal of Semiconductors",
 "Semiconductor Science and Technology","Applied Physics Letters")
def dated(s,earliest,today):
 return bool(s and earliest<=s<=today)
def make_record(category,title,date,source,url,doi,abstract,provider):
 key=(doi.lower() if doi else title.lower())
 rid=hashlib.sha1(key.encode()).hexdigest()[:12]
 return {"id":rid,"kind":"paper","category":category,"title":title,"date":date,
 "source":source or "학술지 정보 미확인","url":url,"doi":doi,
 "topics":classify_topics(title+" "+abstract),"score":score(title,category)+
 (8 if any(x.lower() in (source or "").lower() for x in FOCUSED) else 0),
 "abstract":abstract[:1800],"summary_ko":"공개 초록을 확인해 주요 결론을 검토하세요." if abstract else "서지 메타데이터만 확인됐으며 결론은 검증되지 않았습니다.",
 "summary_status":"초록 기반·원문 미검증" if abstract else "서지 기반·결론 미검증",
 "lookback_days":365,"evidence":provider+" journal metadata",
 "source_type":"journal","metadata_provider":provider}
def crossref_search(session,q,cat,start,today):
 params={"query.bibliographic":q,"filter":"from-pub-date:"+start+",until-pub-date:"+today+",type:journal-article",
 "rows":25,"select":"DOI,title,published,published-online,published-print,container-title,URL,abstract",
 "sort":"score","order":"desc"}
 r=session.get("https://api.crossref.org/works",params=params,timeout=24)
 if r.status_code==429:
  # Bounded retry; honor a small Retry-After but never keep hammering a rate-limited API.
  value=r.headers.get("Retry-After","1")
  try:delay=min(3,max(0,float(value)))
  except (TypeError,ValueError):delay=1
  time.sleep(delay)
  r=session.get("https://api.crossref.org/works",params=params,timeout=24)
 r.raise_for_status()
 out=[]
 for x in r.json().get("message",{}).get("items",[]):
  title=clean((x.get("title") or [""])[0])
  if not relevant(title,cat):continue
  parts=(x.get("published") or {}).get("date-parts",[[None]])[0]
  if not parts or not parts[0]:continue
  date=f"{parts[0]:04d}-{(parts[1] if len(parts)>1 else 1):02d}-{(parts[2] if len(parts)>2 else 1):02d}"
  if not dated(date,start,today):continue
  doi=str(x.get("DOI") or "").lower()
  url=x.get("URL") or ("https://doi.org/"+doi if doi else "")
  if not url.startswith("https://"):continue
  out.append(make_record(cat,title,date,clean((x.get("container-title") or [""])[0]),url,doi,clean(x.get("abstract","")), "Crossref"))
 return out
def openalex_search(session,q,cat,start,today):
 params={"search":q,"filter":"from_publication_date:"+start+",to_publication_date:"+today+",type:article",
 "per_page":25}
 key=os.getenv("OPENALEX_API_KEY","").strip()
 if key:params["api_key"]=key
 r=session.get("https://api.openalex.org/works",params=params,timeout=24);r.raise_for_status()
 out=[]
 for x in r.json().get("results",[]):
  title=clean(x.get("title") or x.get("display_name") or "")
  if not relevant(title,cat):continue
  date=x.get("publication_date")
  if not dated(date,start,today):continue
  source=((x.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
  # Avoid conference abstracts/books when the aim is journal-first.
  location=x.get("primary_location") or {}
  if not (location.get("source") or {}).get("type") in ("journal",None):continue
  doi=(x.get("doi") or "").replace("https://doi.org/","").lower()
  url="https://doi.org/"+doi if doi else (x.get("id") or "")
  if not url.startswith("https://"):continue
  inv=x.get("abstract_inverted_index") or {}
  words=[]
  for word,positions in inv.items():
   for pos in positions:
    if isinstance(pos,int) and pos<350:words.append((pos,word))
  abstract=" ".join(w for _,w in sorted(words))[:1800]
  out.append(make_record(cat,title,date,source,url,doi,abstract,"OpenAlex"))
 return out
def collect_focused(session,now=None,days=365):
 """One Crossref query per technology, OpenAlex for breadth; circuit-break after HTTP 429."""
 now=now or dt.datetime.now(dt.timezone.utc)
 earliest=(now-dt.timedelta(days=days)).date().isoformat();today=now.date().isoformat()
 results=[];errors=[];stats={};crossref_limited=False
 for cat,queries in QUERIES.items():
  prior=len(results)
  if not crossref_limited:
   try:
    results.extend(crossref_search(session,queries[0],cat,earliest,today))
   except requests.HTTPError as exc:
    code=getattr(getattr(exc,"response",None),"status_code",None)
    if code==429:
     crossref_limited=True
     errors.append("Crossref rate limited (429); further Crossref queries skipped for this run, OpenAlex fallback remains active")
    else:errors.append(f"Crossref {cat} HTTP {code or 'error'}")
   except Exception as exc:errors.append(f"Crossref {cat} {type(exc).__name__}")
  for q in queries:
   try:results.extend(openalex_search(session,q,cat,earliest,today))
   except requests.HTTPError as exc:
    code=getattr(getattr(exc,"response",None),"status_code",None)
    errors.append(f"OpenAlex {cat} HTTP {code or 'error'}")
   except Exception as exc:errors.append(f"OpenAlex {cat} {type(exc).__name__}")
  stats[cat]=len(results)-prior
 return results,errors,stats
