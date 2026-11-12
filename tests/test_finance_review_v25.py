"""V2.5 finance audit regression: no fabricated figures or automatic approvals."""
import copy
import json
from pathlib import Path
from scripts.financial_review_diff import build,changes,trends,rate

ROOT=Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT/"site"/name).read_text(encoding="utf-8"))

def test_baseline_matches_verified_original():
    current=read("financials.json")
    baseline=read("financial_baseline.json")
    result=build(current,baseline)
    assert result["changes"]==[]
    assert len(result["trends"])==9
    assert current["auto_refresh"] is False
    assert baseline["baseline_reviewed_on"]=="2026-11-12"

def test_review_queue_detects_only_changed_metrics():
    current=read("financials.json")
    baseline=read("financial_baseline.json")
    current["companies"][0]["periods"][-1]["revenue"]+=12
    item=changes(current,baseline)
    assert len(item)==1
    assert item[0]["field"]=="revenue"
    assert item[0]["before"]==4706
    assert item[0]["after"]==4718
    assert item[0]["review_required"] is True

def test_segmentation_and_noncomparable_excluded():
    rows=trends(read("financials.json"))
    assert any(x["company"]=="rohm" and x["comparison"]=="YoY H1" for x in rows)
    assert not any(x["company"]=="rohm" and x["comparison"]=="sequential quarters" for x in rows)
    assert all(x["currency"] in {"EUR","USD","JPY"} for x in rows)
    assert all(x["scope"]=="group" or x["scope"]=="segment" for x in rows)
    assert not any(x["company"]=="onsemi" and x["metric"]=="operating_income" for x in rows)
    assert rate(0,100) is None
    assert rate(-20,10) is None

def test_v25_frontend_and_workflow():
    html=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
    workflow=(ROOT/".github"/"workflows"/"weekly.yml").read_text(encoding="utf-8")
    for token in ('id="finance-v25"','id="finance-v25-trends"','id="finance-v25-audit-items"',
                  "financial_review_diff.json?nocache=","renderFinanceV25"):
        assert token in html
    assert "python -m scripts.financial_review_diff" in workflow
    assert "financials.json" not in workflow.split("git add",1)[1].split("\n",1)[0]
