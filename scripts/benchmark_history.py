"""Maintain versioned product-benchmark snapshots without fabricated datasheet revision dates."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"site"/"benchmark.json"
BASE=ROOT/"site"/"benchmark_history"
def signature(item):
 # Ignore description/portal text; capture documented electrical specs and provenance.
 fields={k:item.get(k) for k in ("part","company","category","architecture","voltage","specs","url","datasheet_revision","verification")}
 return hashlib.sha256(json.dumps(fields,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]
def create_snapshot(data,now=None,existing=None):
 now=now or dt.datetime.now(dt.timezone.utc)
 this={r["id"]:signature(r) for r in data["devices"]}
 previous=(existing or {}).get("parts",{})
 added=sorted(k for k in this if k not in previous)
 changed=sorted(k for k in this if k in previous and this[k]!=previous[k])
 removed=sorted(k for k in previous if k not in this)
 return {"schema_version":1,"captured_at":now.isoformat(),"source_reviewed_on":data.get("reviewed_on"),"catalog_count":len(this),
         "parts":this,"added_ids":added,"changed_ids":changed,"removed_ids":removed,
         "note":"이력은 PSI Radar에 등록된 사양 스냅샷의 변경을 뜻하며 제조사 Datasheet 개정 사실과 동일하지 않습니다."}
def main():
 data=json.loads(MASTER.read_text(encoding="utf-8"))
 BASE.mkdir(parents=True,exist_ok=True)
 files=sorted(BASE.glob("????-??-??.json"))
 last=json.loads(files[-1].read_text(encoding="utf-8")) if files else None
 today=dt.datetime.now(dt.timezone.utc)
 stamp=today.strftime("%Y-%m-%d")
 # Same-day builds don't create synthetic version churn.
 earlier=sorted(p for p in files if p.stem<stamp)
 prior=json.loads(earlier[-1].read_text(encoding="utf-8")) if earlier else None
 snapshot=create_snapshot(data,today,prior)
 file=BASE/(stamp+".json")
 file.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
 entries=[]
 for p in sorted(BASE.glob("????-??-??.json"),reverse=True)[:104]:
  try:
   v=json.loads(p.read_text(encoding="utf-8"))
   entries.append({"date":p.stem,"count":v["catalog_count"],"added":len(v["added_ids"]),"changed":len(v["changed_ids"]),"removed":len(v["removed_ids"]),"file":"benchmark_history/"+p.name})
  except (OSError,ValueError,KeyError):pass
 (BASE/"index.json").write_text(json.dumps({"generated_at":today.isoformat(),"entries":entries},ensure_ascii=False,indent=2),encoding="utf-8")
 print("Benchmark history:",stamp,"total:",snapshot["catalog_count"],"added:",len(snapshot["added_ids"]),"changed:",len(snapshot["changed_ids"]),"prior:",bool(prior))
if __name__=="__main__":main()
