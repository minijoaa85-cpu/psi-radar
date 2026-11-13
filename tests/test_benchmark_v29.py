"""V2.9 benchmark plots show source values but never claim unverified equivalence."""
import json
from pathlib import Path
from scripts.validate_benchmark import strictly_comparable

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
BENCH=json.loads((ROOT/"site"/"benchmark.json").read_text(encoding="utf-8"))
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))

def test_metric_studio_is_first_and_preserves_detailed_benchmark():
    for token in ('id="bench-v29"','id="bench-v29-metric"','id="bench-v29-stats"',
                  'id="bench-v29-plot"','id="bench-v29-more"',
                  'function renderBenchmark29(rows)','function benchmark29PairEligible(a,b,key)'):
        assert token in HTML
    assert HTML.index('id="bench-v29"')<HTML.index('id="bench-fom"')
    assert 'renderBenchmark29(rows);' in HTML
    assert 'data-b29-slot="a"' in HTML and 'data-b29-slot="b"' in HTML
    assert 'el("bench-"+slot)' in HTML
    assert 'compareBench();' in HTML
    assert 'id="bench-a"' in HTML and 'id="bench-b"' in HTML
    assert 'id="bench-rows"' in HTML
    assert 'id="bench-history"' in HTML

def test_no_fabricated_eoss_and_real_metric_counts():
    devices=BENCH["devices"]
    assert len(devices)>=22
    assert sum("rds_on" in d["specs"] for d in devices)==16
    assert sum("qg" in d["specs"] for d in devices)==12
    assert sum("eoss" in d["specs"] for d in devices)==0
    for key in ("rds_on","rds_on_max","qg","qoss","eoss","vce_sat","qrr","tsc"):
        assert 'value="'+key+'"' in HTML
    assert '값을 추정하거나 0으로 표시하지 않습니다' in HTML
    assert 'Number.isFinite(v.value)' in HTML

def test_condition_paired_only_when_strict_safety_policy_passes():
    devices=BENCH["devices"]
    assert not strictly_comparable(devices[0],devices[1],"qg")
    assert 'va.kind==="unspecified"' in HTML
    assert 'a.verification!=="datasheet_table_verified"' in HTML
    assert 'b.verification!=="datasheet_table_verified"' in HTML
    assert 'ordered(va.test_conditions)!==ordered(vb.test_conditions)' in HTML
    assert 'B29_BAD.some' in HTML
    assert 'const same=benchmark29PairEligible(a,b,key);' in HTML
    assert '동등조건 검증 비교쌍' in HTML
    assert '원문 최종 검토 권장' in HTML

def test_v29_history_and_pdf_generation_are_same_source():
    assert HISTORY["latest_version"]=="V2.9"
    assert HISTORY["entries"][-1]["version"]=="V2.9"
    assert len(HISTORY["entries"])==30
    assert all(HISTORY["entries"][-1].get(k) for k in ("summary","background","changes","value"))
    assert 'version_history.json?nocache=' in HTML
    builder=(ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
    assert '"version_history.json"' in builder
