"""Competitor watch: public-source discovery and conservative multilingual attribution.
Mentions are not evidence of a company's ownership, product claim, or official announcement.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import re
from urllib.parse import quote,urlparse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from scripts.collect import clean, relevant, score, classify_topics

COMPANIES={
 "infineon":{"name":"Infineon","region":"Europe","tier":"core","aliases":("Infineon","インフィニオン","英飞凌"),"domains":("infineon.com",)},
 "st":{"name":"STMicroelectronics","region":"Europe","tier":"core","aliases":("STMicroelectronics","ST Microelectronics","意法半导体","STマイクロエレクトロニクス"),"domains":("st.com",)},
 "onsemi":{"name":"onsemi","region":"US","tier":"core","aliases":("onsemi","ON Semiconductor","安森美","オンセミ"),"domains":("onsemi.com",)},
 "rohm":{"name":"ROHM","region":"Japan","tier":"core","aliases":("ROHM","ローム","罗姆半导体"),"domains":("rohm.com",)},
 "mitsubishi":{"name":"Mitsubishi Electric","region":"Japan","tier":"priority","aliases":("Mitsubishi Electric","三菱電機","三菱电机"),"domains":("mitsubishielectric.com",)},
 "fuji":{"name":"Fuji Electric","region":"Japan","tier":"priority","aliases":("Fuji Electric","富士電機","富士电机"),"domains":("fujielectric.com",)},
 "toshiba":{"name":"Toshiba","region":"Japan","tier":"priority","aliases":("Toshiba","東芝","东芝"),"domains":("toshiba.com","toshiba.semicon-storage.com")},
 "innoscience":{"name":"Innoscience","region":"China","tier":"priority","aliases":("Innoscience","英诺赛科","イノサイエンス"),"domains":("innoscience.com",)},
 "sanan":{"name":"Sanan","region":"China","tier":"priority","aliases":("Sanan Semiconductor","Sanan Optoelectronics","三安半导体","三安光电"),"domains":("sanan-ic.com","sanan-e.com")},
 "crmicro":{"name":"CR Micro","region":"China","tier":"priority","aliases":("China Resources Microelectronics","CR Micro","华润微电子","華潤微電子"),"domains":("crmicro.com",)},
 "basicsemi":{"name":"BASiC Semiconductor","region":"China","tier":"priority","aliases":("BASiC Semiconductor","基本半导体"),"domains":("basicsemi.com",)},
 "navitas":{"name":"Navitas","region":"US","tier":"priority","aliases":("Navitas Semiconductor","纳微半导体"),"domains":("navitassemi.com",)},
 "epc":{"name":"EPC","region":"US","tier":"priority","aliases":("Efficient Power Conversion","EPC GaN"),"domains":("epc-co.com",)},
 "wolfspeed":{"name":"Wolfspeed","region":"US","tier":"priority","aliases":("Wolfspeed","Cree Wolfspeed","沃尔夫斯皮德"),"domains":("wolfspeed.com",)}
}
# Search exact company+technology: only public RSS, no paywall crawling or guessed vendor pages.
QUERIES={
 "infineon":'"Infineon" (GaN OR SiC OR IGBT OR MOSFET)',
 "st":'"STMicroelectronics" (GaN OR SiC OR MOSFET)',
 "onsemi":'"onsemi" (SiC OR GaN OR MOSFET)',
 "rohm":'"ROHM" (SiC OR GaN OR MOSFET)',
 "mitsubishi":'"Mitsubishi Electric" (GaN OR SiC OR IGBT)',
 "fuji":'"Fuji Electric" (IGBT OR SiC)',
 "toshiba":'"Toshiba" (SiC OR MOSFET OR IGBT)',
 "innoscience":'"Innoscience" GaN',
 "sanan":'"三安半导体" (碳化硅 OR 氮化镓)',
 "crmicro":'"华润微电子" (IGBT OR MOSFET OR SiC)',
 "basicsemi":'"基本半导体" (SiC OR IGBT)',
 "navitas":'"Navitas Semiconductor" GaN',
 "epc":'"Efficient Power Conversion" GaN',
 "wolfspeed":'"Wolfspeed" SiC',
}
TECH_MARKERS={
 "GaN":("gan","gallium nitride","氮化镓","窒化ガリウ"),
 "SiC":("sic","silicon carbide","碳化硅","炭化ケイ素"),
 "IGBT":("igbt","insulated gate bipolar","绝缘栅双极","絶縁ゲート"),
 "SGT":("shielded gate","split gate","shield gate"),
 "SJ MOSFET":("superjunction","super junction","sj mosfet")
}
def contains(text,alias):
 if re.match(r"^[a-zA-Z0-9 ]+$",alias):
  return bool(re.search(r"(?<![\w])"+re.escape(alias.lower())+r"(?![\w])",text.lower()))
 return alias.lower() in text.lower()
def mentions(title):
 return [key for key,meta in COMPANIES.items() if any(contains(title,a) for a in meta["aliases"])]
def devices(title,fallback=None):
 t=title.lower()
 found=[cat for cat,markers in TECH_MARKERS.items() if any(contains(t,m) for m in markers)]
 return found or ([fallback] if fallback in TECH_MARKERS else [])
def assess_source(url,source,company_key):
 # RSS news.google URLs are NEVER presented as official, even if company appears in title.
 host=urlparse(url).hostname or ""
 safehost=host.lower()
 meta=COMPANIES[company_key]
 official=any(safehost==d or safehost.endswith("."+d) for d in meta["domains"])
 # Source label is a hint but cannot verify linked publisher ownership.
 return "official_verified_url" if official else "news_index_unverified"
def tag_records(rows):
 for row in rows:
  if row.get("source_type")=="manufacturer_official":
   # Official registry has a verified publisher URL and explicit device mentions.
   # Do not overwrite curated provenance with title-mention heuristics.
   continue
  found=mentions(row.get("title",""))
  row["companies"]=found
  row["company_attribution"]="title_mention_only" if found else "not_attributed"
  row["company_source_status"]={k:assess_source(row.get("url",""),row.get("source",""),k) for k in found}
  row["device_mentions"]=devices(row.get("title",""),row.get("category"))
 return rows
def fetch_company_news(session,key,days=7):
 query=QUERIES[key]
 url="https://news.google.com/rss/search?q="+quote(query+" when:"+str(days)+"d",safe="")+"&hl=en-US&gl=US&ceid=US:en"
 resp=session.get(url,timeout=18);resp.raise_for_status()
 out=[]
 for elem in ET.fromstring(resp.content).findall("./channel/item")[:7]:
  title=clean(elem.findtext("title"));link=clean(elem.findtext("link"))
  if not title or not link.startswith("https://") or key not in mentions(title):continue
  cats=devices(title)
  if not cats:continue
  # Strict device-marker guard prevents financial/marketing search hits with no device reference.
  try:date=parsedate_to_datetime(elem.findtext("pubDate")).date().isoformat()
  except (TypeError,ValueError,IndexError):continue
  if date>dt.datetime.now(dt.timezone.utc).date().isoformat():continue
  cat=cats[0]
  rid=hashlib.sha1((title+link).encode()).hexdigest()[:12]
  out.append({"id":rid,"kind":"news","category":cat,"title":title,"date":date,
    "source":clean(elem.findtext("source") or "Google News RSS"),"url":link,
    "topics":classify_topics(title),"score":score(title,cat),"lookback_days":days,
    "summary_ko":"제목만 확보한 공개 뉴스입니다. 기업의 기술·제품 발표 여부는 원문에서 확인해야 합니다.",
    "summary_status":"뉴스 색인·원문 검증 전","evidence":"Google News RSS index",
    "companies":[key],"company_attribution":"title_mention_only","company_source_status":{key:"news_index_unverified"},
    "device_mentions":cats})
 return out
def collect_competitors(session,days=7):
 items=[];errors=[]
 for key in QUERIES:
  try:
   found=fetch_company_news(session,key,days)
   items.extend(found)
   # Expand only quiet Japan/China watchlists; label older sources separately.
   if not found and COMPANIES[key]["region"] in ("Japan","China"):
    older=fetch_company_news(session,key,30)
    items.extend(older)
  except Exception as e:errors.append("competitor "+key+": "+type(e).__name__)
 return items,errors
def summarize_companies(rows):
 data={}
 for key,meta in COMPANIES.items():
  matches=[r for r in rows if key in r.get("companies",[])]
  data[key]={"id":key,"name":meta["name"],"region":meta["region"],"tier":meta["tier"],
     "items":len(matches),"news":sum(r.get("kind")=="news" for r in matches),
     "papers":sum(r.get("kind")=="paper" for r in matches),
     "official":sum(r.get("source_type")=="manufacturer_official" for r in matches),
     "by_device":{d:sum(d in r.get("device_mentions",[]) for r in matches) for d in TECH_MARKERS},
     "last_date":max((r.get("date") or "" for r in matches),default="")}
 return data
