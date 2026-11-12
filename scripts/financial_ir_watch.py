"""V2.3: conservative official IR announcement discovery, never automatic monetary edits.

Fetch only explicitly configured first-party IR landing pages. Extract hyperlinks
that LOOK like earnings releases, keep provenance and identify candidates for
human review. Nothing here parses earnings figures or changes financials.json.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests

from scripts.validate_financials import COMPANY_RULES, PATH, validate_snapshot

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
OUTPUT=SITE/"financial_ir_watch.json"
SOURCES={
 "infineon":{"name":"Infineon","landing":"https://www.infineon.com/about/investor/news",
             "fallback":"https://www.infineon.com/about/press",
             "keywords":("quarterly report","financial results","earnings","fiscal year","quarter results","fy 20")},
 "st":{"name":"STMicroelectronics","landing":"https://investors.st.com/",
       "fallback":"https://newsroom.st.com/",
       "keywords":("financial results","quarterly results","earnings release","quarter 20","q1 20","q2 20","q3 20","q4 20")},
 "onsemi":{"name":"onsemi","landing":"https://investor.onsemi.com/news",
            "fallback":"https://investor.onsemi.com/",
            "keywords":("reports first quarter","reports second quarter","reports third quarter","reports fourth quarter",
                        "reports q1","reports q2","reports q3","reports q4","financial results")},
 "rohm":{"name":"ROHM","landing":"https://www.rohm.com/ir",
          "fallback":"https://www.rohm.com/ir/library/ir-news-releases",
          "keywords":("financial report","financial results","fact book","earnings","financial statements","results briefing")},
}
MAX_PER_COMPANY=12
TIMEOUT=(6,14)


def normalize_url(value):
 if not isinstance(value,str):return None
 try:
  parts=urlsplit(value.strip())
  if parts.scheme!="https" or not parts.hostname or parts.username or parts.password:return None
  # Drop tracking query/fragment. Keep case-sensitive path.
  host=parts.hostname.lower()
  if parts.port not in (None,443):return None
  path=parts.path.rstrip("/") or "/"
  return urlunsplit(("https",host,path,"",""))
 except ValueError:return None


def allowed_url(url,company):
 canonical=normalize_url(url)
 if not canonical:return False
 host=urlsplit(canonical).hostname or ""
 domains=COMPANY_RULES[company][2]
 return any(host==d or host.endswith("."+d) for d in domains)


class LinkExtractor(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.links=[]
  self.current=None
  self.depth=0
 def handle_starttag(self,tag,attrs):
  if self.current is not None:
   self.depth+=1
   return
  if tag!="a":return
  href=dict(attrs).get("href")
  if href:
   self.current={"href":href,"text":[]}
   self.depth=0
 def handle_data(self,data):
  if self.current is not None:self.current["text"].append(data)
 def handle_endtag(self,tag):
  if self.current is None:return
  if self.depth:
   self.depth-=1
  elif tag=="a":
   self.links.append((self.current["href"]," ".join(self.current["text"])))
   self.current=None


def normalized_title(value):
 return " ".join(unescape(value or "").split())[:240]


def candidates_from_html(html,company,base_url=None):
 conf=SOURCES[company]
 parser=LinkExtractor()
 parser.feed(html)
 matched={}
 for href,text in parser.links:
  title=normalized_title(text)
  if len(title)<12:continue
  lower=title.lower()
  if not any(word in lower for word in conf["keywords"]):continue
  url=normalize_url(urljoin(base_url or conf["landing"],href))
  if not url or not allowed_url(url,company):continue
  # Do not treat overview/category pages, advertising links or file downloads as releases.
  path=urlsplit(url).path.lower()
  if path in ("/","/ir","/news","/about/investor","/about/investor/news"):continue
  if path.endswith((".jpg",".jpeg",".png",".svg",".zip",".mp4")):continue
  matched[url]={"title":title,"url":url,"company":company,
                "source_level":"official_host_link","review_status":"unverified_candidate"}
  if len(matched)>=MAX_PER_COMPANY:break
 return list(matched.values())


def curated_urls(snapshot,company):
 obj=next((c for c in snapshot["companies"] if c["id"]==company),None)
 if obj is None:return set()
 return {normalize_url(r["source"]) for kind in ("periods","segments") for r in obj.get(kind,[])}


def run_watch(snapshot,previous=None,session=None,now=None):
 validate_snapshot(snapshot)
 now=now or dt.datetime.now(dt.timezone.utc)
 if now.tzinfo is None:now=now.replace(tzinfo=dt.timezone.utc)
 scan_time=now.isoformat(timespec="seconds")
 previous=previous if isinstance(previous,dict) else {}
 prev={r.get("url"):r for r in previous.get("candidates",[]) if isinstance(r,dict) and normalize_url(r.get("url"))}
 own_session=session or requests.Session()
 records=[]
 diagnostics=[]
 for company,conf in SOURCES.items():
  observed=[]
  last_error=""
  succeeded=False
  used_landing=conf["landing"]
  for landing in (conf["landing"],conf["fallback"]):
   try:
    response=own_session.get(landing,timeout=TIMEOUT,headers={
      "User-Agent":"PSI-Radar-IR-Monitor/2.3 (public first-party IR announcements; low frequency)",
      "Accept":"text/html,application/xhtml+xml"})
    response.raise_for_status()
    if not allowed_url(response.url,company):
     raise ValueError("IR landing redirected outside approved company host")
    if "html" not in response.headers.get("Content-Type","").lower():
     raise ValueError("not HTML")
    if len(response.content)>3_000_000:raise ValueError("HTML larger than 3 MB")
    observed=candidates_from_html(response.text,company,base_url=response.url)
    succeeded=True
    used_landing=landing
    break
   except (requests.RequestException,ValueError,UnicodeError) as exc:
    last_error=str(exc)[:140]
  diagnostics.append({
    "company":company,"status":"ok" if succeeded else "source_unavailable",
    "observed":len(observed),"landing":used_landing,"checked_at":scan_time,
    **({"note":last_error} if not succeeded else {})
  })
  if not succeeded:
   # Preserve older unverified candidates when both official sources fail.
   observed=[r for r in previous.get("candidates",[])
             if isinstance(r,dict) and r.get("company")==company]
  trusted=curated_urls(snapshot,company)
  for row in observed:
   url=row["url"]
   if not allowed_url(url,company):continue
   old=prev.get(url,{})
   records.append({
     "company":company,"title":normalized_title(row["title"]),
     "url":url,
     "first_observed_at":old.get("first_observed_at") or scan_time,
     "last_observed_at":scan_time if diagnostics[-1]["status"]=="ok" else old.get("last_observed_at",scan_time),
     "review_status":"already_in_verified_financials" if url in trusted else "human_review_required",
     "listed_on_official_ir":diagnostics[-1]["status"]=="ok",
     "source_publication_date":None,
   })
 # Include historic candidates for manual review across a few weekly executions;
 # do not mark missing due to a layout change as rejected.
 merged={r["url"]:r for r in records}
 for url,old in prev.items():
  if url not in merged and old.get("company") in SOURCES and allowed_url(url,old["company"]):
   merged[url]={**old,"listed_on_official_ir":False}
 ordered=sorted(merged.values(),key=lambda r:(r.get("first_observed_at") or "",r["url"]),reverse=True)[:80]
 return {
   "schema_version":1,"version":"2.3","checked_at":scan_time,
   "financials_reviewed_on":snapshot["reviewed_on"],"automatic_metric_updates":False,
   "candidate_count":sum(r["review_status"]=="human_review_required" for r in ordered),
   "candidates":ordered,"sources":diagnostics,
   "warning":"공식 IR 목록의 링크 제목을 이용한 신규 실적 후보 탐지입니다. 최초 관측일은 발표일이 아니며, 링크 등록만으로 숫자·공시의 신규성·회사 성과가 검증되지 않습니다. 재무 수치는 수동 검증 후 별도 반영됩니다.",
 }


def main():
 finance=json.loads(PATH.read_text(encoding="utf-8"))
 try:previous=json.loads(OUTPUT.read_text(encoding="utf-8"))
 except (OSError,ValueError):previous={}
 result=run_watch(finance,previous=previous)
 OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("IR watch:",len(result["sources"]),"sources",
       result["candidate_count"],"human-review candidates",
       sum(r["status"]!="ok" for r in result["sources"]),"unavailable sources",
       "metrics auto-updated: no")


if __name__=="__main__":main()
