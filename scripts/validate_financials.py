"""Validate the manually curated official financial snapshot.

No FX conversions, estimations, accidental mixing of FY quarter vs half-year,
company-level metrics vs segment KPIs or inferred profitability.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"site"/"financials.json"
COMPANY_RULES={
 "infineon":("EUR","IFRS",("infineon.com",)),
 "st":("USD","US GAAP",("st.com","sec.gov")),
 "onsemi":("USD","US GAAP",("onsemi.com",)),
 "rohm":("JPY","Japanese GAAP",("rohm.com",)),
}
ALLOWED_TYPES={"quarter","half_year"}
ALLOWED_SEGMENT_PROFITS={"Segment Result","Segment Profit/Loss"}
def check(condition,message):
 if not condition:raise ValueError(message)
def source_valid(url,id):
 try:
  p=urlparse(url)
  host=(p.hostname or "").lower()
  return p.scheme=="https" and not p.username and not p.password and any(
   host==domain or host.endswith("."+domain) for domain in COMPANY_RULES[id][2]
  )
 except (ValueError,TypeError):
  return False
def date(value):
 check(isinstance(value,str),"Date must be a string")
 return dt.date.fromisoformat(value)
def number(value,allow_none=False):
 if allow_none and value is None:return
 check(type(value) in (int,float),"Metric must be numeric, not inferred text or boolean")
 check(abs(value)<1e9,"Value magnitude invalid")
def validate_snapshot(data):
 check(data.get("schema_version")==1,"Unsupported financial schema")
 check(data.get("auto_refresh") is False,"Do not claim automatic finance extraction")
 check(date(data.get("reviewed_on"))<=dt.date.today(),"Review date cannot be in the future")
 companies=data.get("companies")
 check(isinstance(companies,list) and len(companies)==4,"Four curated companies expected")
 check({x.get("id") for x in companies}==set(COMPANY_RULES),"Wrong or duplicate company IDs")
 checked=0
 for company in companies:
  id=company["id"]
  currency,accounting,_=COMPANY_RULES[id]
  check(company.get("currency")==currency,f"{id}: unexpected currency")
  check(company.get("accounting")==accounting,f"{id}: unexpected accounting convention")
  check(company.get("source_scope")=="Consolidated group",f"{id}: missing reporting scope")
  periods=company.get("periods") or []
  check(periods,f"{id}: no company financial periods")
  keys=set()
  for row in periods+company.get("segments",[]):
   kind=row.get("period_type")
   check(kind in ALLOWED_TYPES,f"{id}: period kind missing")
   start,end=date(row.get("start")),date(row.get("end"))
   check(start<=end and end<=date(data["reviewed_on"]),f"{id}: period exceeds financial review date")
   days=(end-start).days+1
   check(75<=days<=100 if kind=="quarter" else 175<=days<=190,f"{id}: invalid {kind} duration {days}")
   check(source_valid(row.get("source"),id),f"{id}: wrong/nonofficial source host")
   check(date(row.get("published"))<=date(data["reviewed_on"]),f"{id}: unpublished date")
   number(row.get("revenue"))
   check(row["revenue"]>0,f"{id}: revenue must be positive")
   if "name" in row:
    check(row.get("name"),f"{id}: unnamed segment")
    number(row.get("profit"),allow_none=True)
    if row.get("profit") is not None:check(row.get("profit_label") in ALLOWED_SEGMENT_PROFITS,f"{id}: unlabeled segment profit")
    number(row.get("profit_margin"),allow_none=True)
   else:
    number(row.get("operating_income"),allow_none=True)
    number(row.get("operating_margin"),allow_none=True)
    number(row.get("segment_result"),allow_none=True)
    number(row.get("segment_result_margin"),allow_none=True)
    check(row.get("reviewed_on")==data["reviewed_on"],f"{id}: row review date mismatch")
    if id=="infineon":
     check(row.get("operating_income") is None and row.get("segment_result") is not None,f"{id}: do not substitute segment result for GAAP income")
    key=(row.get("period"),kind)
    check(key not in keys,f"{id}: duplicate period")
    keys.add(key)
   checked+=1
  for seg in company.get("segments",[]):
   check((seg.get("period"),seg.get("period_type")) in keys,f"{id}: segment without same-period group statement")
   check(seg.get("note"),f"{id}: segment scope explanation needed")
  check(company.get("notes"),f"{id}: needs accounting caveat")
  if id=="rohm":
   check(all(r["period_type"]=="half_year" for r in periods+company.get("segments",[])),"ROHM H1 must not become a quarter")
 check(data.get("warning") and data.get("refresh_policy"),"Data interpretation guidance missing")
 return checked
def main():
 data=json.loads(PATH.read_text(encoding="utf-8"))
 n=validate_snapshot(data)
 print(f"Validated official financial snapshot: {len(data['companies'])} companies, {n} period/segment records; manual update only")
if __name__=="__main__":main()
