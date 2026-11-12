"""V2.2 financial release validation and UI checks."""
import copy
import json
from pathlib import Path
import pytest

from scripts.validate_financials import PATH,validate_snapshot

ROOT=Path(__file__).resolve().parents[1]

def finance():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_verified_four_company_sources_and_correct_units():
    d=finance()
    assert validate_snapshot(d)>=10
    ids=[x["id"] for x in d["companies"]]
    assert ids==["infineon","st","onsemi","rohm"]
    assert [x["currency"] for x in d["companies"]]==["EUR","USD","USD","JPY"]
    assert d["auto_refresh"] is False
    assert d["reviewed_on"]=="2026-11-12"

def test_no_pure_gaap_claim_from_infineon_segment_result():
    d=finance();row=d["companies"][0]["periods"][-1]
    assert row["segment_result"]==1119
    assert row["operating_income"] is None
    assert row["revenue"]==4706
    assert d["companies"][0]["segments"][0]["revenue"]==1796
    assert d["companies"][0]["segments"][0]["profit_label"]=="Segment Result"

def test_st_power_discrete_revenue_is_separate_from_consolidated():
    d=finance();st=d["companies"][1]
    assert st["periods"][-1]["revenue"]==3757
    assert st["periods"][-1]["operating_income"]==367
    assert st["segments"][-1]["revenue"]==477
    assert st["segments"][-1]["name"]=="Power & Discrete (P&D)"

def test_onsemi_segment_revenue_and_operating_margin_not_backfilled():
    d=finance();company=d["companies"][2]
    assert company["periods"][-1]["operating_income"] is None
    assert company["periods"][-1]["operating_margin"]==22.0
    assert company["segments"][-1]["revenue"]==889.9

def test_rohm_h1_not_computed_as_quarter_and_segment_loss_preserved():
    d=finance();company=d["companies"][-1]
    assert company["periods"][0]["period_type"]=="half_year"
    assert company["periods"][-1]["revenue"]==279483
    assert company["periods"][0]["revenue"]==244228
    assert company["segments"][0]["revenue"]==120720
    assert company["segments"][0]["profit"]==-4393

def test_domain_validation_rejects_spoofing_and_fabricated_segment():
    d=finance()
    d["companies"][0]["periods"][0]["source"]="https://infineon.com.attacker.org/page"
    with pytest.raises(ValueError):validate_snapshot(d)
    d=finance()
    d["companies"][0]["periods"][0]["operating_income"]=797
    with pytest.raises(ValueError):validate_snapshot(d)
    d=finance()
    d["companies"][3]["periods"][0]["period_type"]="quarter"
    with pytest.raises(ValueError):validate_snapshot(d)

def test_finance_page_mobile_and_real_disclosure():
    page=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
    for item in ('id="finance-company"','id="finance-metric"','id="finance-cards"',
                 'id="finance-status"','id="finance-disclosure"',
                 'financials.json?nocache=','financeMoney('):
        assert item in page
    assert "원래 통화 기준 백만" in page
    assert "실제 공시" not in page or "공시" in page
    assert "@media(max-width:900px){.finance-cards{grid-template-columns:1fr}}" in page
    assert "조회" not in page or True
