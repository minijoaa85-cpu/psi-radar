"""V2.5: transparent within-company financial trends and pending changes.

Derived numbers never overwrite the manually verified source or its pinned baseline.
"""
from __future__ import annotations
import json
from pathlib import Path
from scripts.validate_financials import validate_snapshot

ROOT=Path(__file__).resolve().parents[1]
LIVE=ROOT/"site"/"financials.json"
BASE=ROOT/"site"/"financial_baseline.json"
OUT=ROOT/"site"/"financial_review_diff.json"
METRICS=("revenue","operating_income","operating_margin","segment_result","segment_result_margin","profit","profit_margin")

def rows(company):
    return [(("group",p["period"],p["period_type"]),p) for p in company.get("periods",[])] + [
        (("segment",p["name"],p["period"],p["period_type"]),p) for p in company.get("segments",[])]

def changes(current,baseline):
    old={c["id"]:c for c in baseline["companies"]}
    result=[]
    for c in current["companies"]:
        baseline_company=old.get(c["id"])
        if not baseline_company:
            result.append(dict(company=c["id"],scope="company",period="",field="company_added",before=None,after=c["name"],review_required=True))
            continue
        before=dict(rows(baseline_company))
        after=dict(rows(c))
        for key,item in after.items():
            previous=before.get(key)
            if previous is None:
                result.append(dict(company=c["id"],scope=key[0],period=item["period"],field="new_period",before=None,after="new_record",review_required=True,source=item["source"]))
                continue
            for field in METRICS:
                if item.get(field)!=previous.get(field):
                    result.append(dict(company=c["id"],scope=key[0],period=item["period"],field=field,before=previous.get(field),after=item.get(field),review_required=True,source=item["source"]))
            for field in ("source","start","end","published","profit_label"):
                if item.get(field)!=previous.get(field):
                    result.append(dict(company=c["id"],scope=key[0],period=item["period"],field=field,before=previous.get(field),after=item.get(field),review_required=True,source=item["source"]))
        for key,item in before.items():
            if key not in after:
                result.append(dict(company=c["id"],scope=key[0],period=item["period"],field="record_removed",before="existing_record",after=None,review_required=True,source=item["source"]))
    return result

def rate(previous,current):
    if type(previous) not in (int,float) or type(current) not in (int,float) or previous<=0:
        return None
    return round((current-previous)/previous*100,2)

def trends(current):
    result=[]
    for company in current["companies"]:
        group=sorted(company.get("periods",[]),key=lambda p:p["end"])
        for a,b in zip(group,group[1:]):
            # Only explicitly comparable periods; H1 year-on-year is NOT sequential quarter.
            if a["period_type"]!=b["period_type"]:continue
            comparison="YoY H1" if b["period_type"]=="half_year" else "sequential quarters"
            for field in ("revenue","operating_income","segment_result"):
                if type(a.get(field)) not in (int,float) or type(b.get(field)) not in (int,float):continue
                result.append(dict(company=company["id"],scope="group",name="연결",metric=field,period_from=a["period"],period_to=b["period"],period_type=b["period_type"],comparison=comparison,
                                   previous=a[field],current=b[field],change_pct=rate(a[field],b[field]),currency=company["currency"],source_from=a["source"],source_to=b["source"]))
        segments={}
        for p in company.get("segments",[]):segments.setdefault((p["name"],p["period_type"]),[]).append(p)
        for (name,kind),items in segments.items():
            items=sorted(items,key=lambda p:p["end"])
            for a,b in zip(items,items[1:]):
                if type(a.get("revenue")) not in (int,float) or type(b.get("revenue")) not in (int,float):continue
                result.append(dict(company=company["id"],scope="segment",name=name,metric="revenue",period_from=a["period"],period_to=b["period"],period_type=kind,comparison="YoY H1" if kind=="half_year" else "sequential quarters",
                    previous=a["revenue"],current=b["revenue"],change_pct=rate(a["revenue"],b["revenue"]),currency=company["currency"],source_from=a["source"],source_to=b["source"]))
    return result

def build(current,baseline):
    validate_snapshot(current)
    assert baseline.get("schema_version")==1
    assert {x["id"] for x in baseline["companies"]}=={x["id"] for x in current["companies"]}
    return dict(schema_version=1,version="2.5",baseline_reviewed_on=baseline["baseline_reviewed_on"],current_reviewed_on=current["reviewed_on"],
                changes=changes(current,baseline),trends=trends(current),
                warning="수동 검증본 대비 변경 후보일 뿐 숫자를 자동 승인하지 않습니다. 동일 기업·동일 기간 종류 안에서만 비교하고, H1은 전년 동기 비교입니다. 수치 변화율은 보고된 양의 기준값에 한해 계산합니다.")

def main():
    data=build(json.loads(LIVE.read_text(encoding="utf-8")),json.loads(BASE.read_text(encoding="utf-8")))
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Finance V2.5: {len(data['trends'])} comparable trends, {len(data['changes'])} changes to review; verified financial figures unchanged")

if __name__=="__main__":main()
