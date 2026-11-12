"""Validate curated product specifications and prevent unsafe numeric comparisons."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

PATH=Path(__file__).resolve().parents[1]/"site"/"benchmark.json"
CATEGORIES={"GaN","SiC","IGBT","SGT","SJ MOSFET"}
METRICS={"rds_on","rds_on_max","qg","qrr","vce_sat","tsc","qgd","qoss","eoss","vth"}
UNITS={"rds_on":"mΩ","rds_on_max":"mΩ","qg":"nC","qgd":"nC","qrr":"nC","qoss":"nC","vce_sat":"V","vth":"V","tsc":"µs","eoss":"µJ"}
ALLOWED={"www.infineon.com","infineon.com","www.rohm.com","rohm.com","toshiba.semicon-storage.com","www.st.com","st.com"}
def load():
 return json.loads(PATH.read_text(encoding="utf-8"))
def validate(data):
 errors=[];ids=set()
 for r in data.get("devices",[]):
  rid=r.get("id","")
  if not rid or rid in ids:errors.append("duplicate/empty part id")
  ids.add(rid)
  if r.get("category") not in CATEGORIES:errors.append("unknown category: "+rid)
  if not r.get("part") or not r.get("company"):errors.append("missing product identification: "+rid)
  if r.get("architecture") not in ("discrete","integrated_half_bridge"):errors.append("missing/unrecognized architecture: "+rid)
  if r.get("verification") not in ("product_page","datasheet_table_verified"):errors.append("invalid verification level: "+rid)
  if "datasheet_revision" not in r:errors.append("datasheet revision field missing: "+rid)
  u=urlparse(r.get("url",""))
  if u.scheme!="https" or u.hostname not in ALLOWED:errors.append("not a verified manufacturer hostname: "+rid)
  if not isinstance(r.get("voltage",{}).get("value"),(int,float)) or r["voltage"]["value"]<=0:errors.append("invalid voltage: "+rid)
  for key,v in r.get("specs",{}).items():
   if key not in METRICS:errors.append("unrecognized metric: "+key)
   if not isinstance(v.get("value"),(int,float)) or v["value"]<0:errors.append("invalid metric value "+rid+" "+key)
   if v.get("unit")!=UNITS.get(key):errors.append("wrong unit "+rid+" "+key)
   if v.get("kind") not in ("typ","max","min"):errors.append("missing typ/max/min "+rid+" "+key)
   if not v.get("condition"):errors.append("missing measurement note "+rid+" "+key)
 return errors
def strictly_comparable(a,b,key):
 if a.get("category")!=b.get("category") or a.get("voltage",{}).get("value")!=b.get("voltage",{}).get("value") or a.get("architecture")!=b.get("architecture"):return False
 va=a.get("specs",{}).get(key);vb=b.get("specs",{}).get(key)
 if not va or not vb:return False
 if (va.get("kind"),va.get("unit"))!=(vb.get("kind"),vb.get("unit")):return False
 # Product page partial/test-not-published conditions cannot establish equivalence.
 bad=("제품 페이지","데이터시트 참조","데이터시트 확인","미상","확인 필요","미확인")
 return va.get("condition")==vb.get("condition") and not any(word in str(va.get("condition","")) for word in bad)

def illustrative_fom(record,metric="qg"):
 """Arithmetic only: mOhm*nC; not temperature-normalized or comparable."""
 if record.get("architecture")!="discrete" or record.get("category") not in ("GaN","SiC","SGT","SJ MOSFET"):return None
 r=record.get("specs",{}).get("rds_on");q=record.get("specs",{}).get(metric)
 if not r or not q or r.get("kind")!="typ" or q.get("kind")!="typ":return None
 if r.get("unit")!="mΩ" or q.get("unit")!="nC":return None
 return round(r["value"]*q["value"],4)
def normalized_fom(record,metric="qg"):
 """Show a defensible normalized FOM only when both exact test setups were reviewed."""
 if record.get("verification")!="datasheet_table_verified":return None
 if not record.get("normalization_group"):return None
 v=illustrative_fom(record,metric)
 return v

if __name__=="__main__":
 data=load();errors=validate(data)
 if errors:raise SystemExit("\n".join(errors))
 print("Validated",len(data.get("devices",[])),"manufacturer product entries")
