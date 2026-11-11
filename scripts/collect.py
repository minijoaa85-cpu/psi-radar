"""Collect dated public news index and Crossref journal metadata; no fabricated conclusions."""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
import os
import re
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"site"/"data.json"
TECH={
 "GaN":['"GaN HEMT"','"gallium nitride" power','"GaN" "data center"'],
 "SiC":['"SiC MOSFET"','"silicon carbide" power semiconductor'],
 "IGBT":['"IGBT" power semiconductor','"IGBT" power module','"trench IGBT"','"RC-IGBT"','"field-stop IGBT"'],
 "SGT":['"shielded gate" MOSFET','"split gate" trench MOSFET'],
 "SJ MOSFET":['"superjunction MOSFET"','"super junction" power MOSFET']}
KEYS={"GaN":("gan","gallium nitride","氮化镓","窒化ガリウ"),"SiC":("sic","silicon carbide","碳化硅","炭化ケイ素"),"IGBT":("igbt","insulated gate bipolar transistor","绝缘栅双极型晶体管","絶縁ゲートバイポーラトランジスタ"),"SGT":("shielded gate","split gate","sgt"),"SJ MOSFET":("superjunction","super junction","sj mosfet")}
TOPICS={"데이터센터":("data center","datacenter","ai server","800vdc"),"신뢰성":("reliability","dynamic r","breakdown","oxide"),"공정·구조":("trench","epitax","wafer","vertical","implant","field stop","lifetime control","reverse conducting","rc-igbt"),"재무·시장":("revenue","margin","earnings","capex","market")}
POWER_CONTEXT=("power","semiconductor","mosfet","hemt","transistor","switching","converter","inverter","charger","charging","gate","breakdown voltage","high voltage","voltage","650v","1200v","1700v","800v","electronic","epitax","wafer","datasheet","data center","datacenter","automotive","device","diode","drain","coolgan","gan-on-si","sicarbide","field-effect","igbt","bipolar transistor","field stop","field-stop","vce(sat)","short-circuit withstand")
EXCLUDE=("generative adversarial network","generative ai network","oil-in-water","membrane filtration","photocatalyst","water treatment","biomedical")
def relevant(title,cat):
 t=clean(title).lower()
 if any(x in t for x in EXCLUDE):return False
 if not any(x in t for x in POWER_CONTEXT):return False
 if cat=="GaN":return bool(re.search(r"\bgan\b|gallium nitride|氮化镓|窒化ガリウ",t))
 if cat=="SiC":return bool(re.search(r"\bsic\b|silicon carbide|碳化硅|炭化ケイ素",t))
 if cat=="IGBT":return bool(re.search(r"\bigbt\b|insulated.gate.bipolar|绝缘栅双极型|絶縁ゲートバイポーラ",t))
 return any(w in t for w in KEYS[cat])
def clean(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(s or "")))).strip()
def classify(title,fallback):
 t=clean(title).lower()
 return next((c for c,words in KEYS.items() if any(w in t for w in words)),fallback)
def classify_topics(t):
 t=clean(t).lower()
 return [k for k,words in TOPICS.items() if any(w in t for w in words)] or ["일반 기술"]
def score(t,c):
 t=t.lower()
 return min(100,{"GaN":50,"SiC":40,"IGBT":30,"SGT":30,"SJ MOSFET":30}.get(c,10)+15*("data center" in t or "800v" in t)+10*("reliability" in t)+10*("trench" in t))
def unique(rows):
 seen=set();out=[]
 for r in rows:
  key=(r.get("doi") or re.sub("[^a-z0-9]","",r["title"].lower())).lower()
  if key not in seen:seen.add(key);out.append(r)
 return out
def news(session,query,category,days=7):
 u="https://news.google.com/rss/search?q="+quote(query+" when:"+str(days)+"d",safe="")+"&hl=en-US&gl=US&ceid=US:en"
 r=session.get(u,timeout=20);r.raise_for_status()
 result=[]
 for it in ET.fromstring(r.content).findall("./channel/item")[:9]:
  title=clean(it.findtext("title"));url=clean(it.findtext("link"))
  if not title or not url or not relevant(title,category):continue
  try:date=parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
  except (TypeError,ValueError,IndexError):date=None
  cat=classify(title,category)
  result.append({"id":hashlib.sha1((title+url).encode()).hexdigest()[:12],"kind":"news","category":cat,"title":title,"date":date,"source":clean(it.findtext("source") or "News RSS"),"url":url,"topics":classify_topics(title),"score":score(title,cat),"lookback_days":days,"summary_ko":"공개 뉴스 색인에서 확인했습니다. 제목과 원문을 검토해 기술적 의미를 판단하세요.","summary_status":"제목 기반·검증 전","evidence":"Google News RSS index"})
 return result
def papers(session,query,category,start):
 r=session.get("https://api.crossref.org/works",params={"query.bibliographic":query,"filter":f"from-pub-date:{start},type:journal-article","sort":"published","order":"desc","rows":8,"select":"DOI,title,published,container-title,URL,abstract"},timeout=25);r.raise_for_status()
 result=[]
 for x in r.json().get("message",{}).get("items",[]):
  title=clean((x.get("title") or [""])[0])
  if not relevant(title,category):continue
  parts=x.get("published",{}).get("date-parts",[[None]])[0]
  date=f"{parts[0]:04}-{(parts[1] if len(parts)>1 else 1):02}-{(parts[2] if len(parts)>2 else 1):02}" if parts[0] else None
  if date and (date > dt.datetime.now(dt.timezone.utc).date().isoformat() or date < start):continue
  abstract=clean(x.get("abstract",""))[:2000]
  doi=x.get("DOI","")
  result.append({"id":hashlib.sha1((doi or title).encode()).hexdigest()[:12],"kind":"paper","category":category,"title":title,"date":date,"source":clean((x.get("container-title") or ["Journal"])[0]),"url":x.get("URL") or "https://doi.org/"+doi,"doi":doi,"topics":classify_topics(title+" "+abstract),"score":score(title,category),"abstract":abstract,"summary_ko":"초록이 수집되었으나 원문의 연구 결론은 별도 검증이 필요합니다." if abstract else "서지 정보만 확보했습니다. 연구 결론은 검증되지 않았습니다.","summary_status":"초록 기반·결론 미검증" if abstract else "서지 기반·결론 미검증","evidence":"Crossref journal metadata"})
 return result
def main():
 now=dt.datetime.now(dt.timezone.utc);start=(now-dt.timedelta(days=8)).date().isoformat()
 paper_start=(now-dt.timedelta(days=45)).date().isoformat()
 session=requests.Session();session.headers.update({"User-Agent":"PSI-Radar/0.1 (public research metadata; github.com/minijoaa85-cpu/psi-radar)"})
 rows=[];errors=[]
 for cat,queries in TECH.items():
  for q in queries:
   try: rows.extend(news(session,q,cat))
   except Exception as e:errors.append(f"news {cat}: {type(e).__name__}: {str(e)[:100]}")
  if cat=="IGBT" and not any(r.get("category")=="IGBT" for r in rows):
   # A quiet 7-day IGBT news week must not be mistaken for a broken collector.
   # Older context is labeled as a 30-day fallback, not as this week's news.
   for q in ('"IGBT" power semiconductor','"IGBT" inverter'):
    try:rows.extend(news(session,q,cat,days=30))
    except Exception as e:errors.append(f"news fallback IGBT: {type(e).__name__}: {str(e)[:100]}")
  try:rows.extend(papers(session,queries[0].replace('"',""),cat,paper_start))
  except Exception as e:errors.append(f"paper {cat}: {type(e).__name__}: {str(e)[:100]}")
 rows=unique(rows)
 # Preserve already reviewed translations across scheduled runs; do not spend on identical records twice.
 previous={}
 if OUT.exists():
  try:
   data=json.loads(OUT.read_text(encoding="utf-8"))
   previous={x.get("id"):x for x in data.get("records",[]) if x.get("id")}
  except (ValueError,OSError,TypeError):pass
 for row in rows:
  old=previous.get(row.get("id"),{})
  if old.get("title_ko"):
   for field in ("title_ko","summary_ko","physics_ko","summary_status"):
    if old.get(field):row[field]=old[field]
 rows.sort(key=lambda x:(x.get("date") or "",x.get("score") or 0),reverse=True)
 if not rows:raise RuntimeError("No metadata collected; retain last successful data. "+str(errors))
 payload={"schema_version":2,"generated_at":now.isoformat(),"window_start":start,"paper_window_start":paper_start,"mode":"live_metadata","records":rows[:150],"counts":{c:sum(r["category"]==c for r in rows) for c in TECH},"errors":errors,"sources":["Crossref","Google News RSS"],"financials":[],"product_specs":[],"notice":"서지·뉴스 메타데이터 기반. 원문 검토 전의 결론이나 금융 실적을 확정하지 않습니다."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Collected",len(rows),"records, errors:",len(errors))
 print("Category counts:",json.dumps(payload["counts"],ensure_ascii=False))
 print("IGBT news records:",sum(x.get("category")=="IGBT" and x.get("kind")=="news" for x in rows),"IGBT papers:",sum(x.get("category")=="IGBT" and x.get("kind")=="paper" for x in rows))
if __name__=="__main__":main()
