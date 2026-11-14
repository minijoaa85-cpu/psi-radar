"""V3.0 Mission Control — cross-source overview without fabricated aggregate scores."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
VERSIONS=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))
BENCH=json.loads((ROOT/"site"/"benchmark.json").read_text(encoding="utf-8"))
RECORDS=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
FINANCE=json.loads((ROOT/"site"/"financials.json").read_text(encoding="utf-8"))

def test_mission_on_overview_and_navigation_groups_preserved():
    for tag in ('id="mission30"', 'id="mission30-tabs"', 'id="mission30-kpis"',
                'id="mission30-channels"','id="mission30-evidence"',
                'id="mission30-journey"','id="mission30-stamp"'):
        assert tag in HTML
    assert HTML.index('id="mission30"')<HTML.index('id="pulse27-overview-title"')
    for target in ("research","competitors","benchmark","market","integrated","weekly"):
        assert 'data-m30-destination="'+target+'"' in HTML
    assert "showRadarSection(page);" in HTML
    assert 'el("research-cat").value=M30_SELECTED' in HTML
    assert 'el("company-tech").value=M30_SELECTED' in HTML
    assert 'el("bench-category").value=M30_SELECTED' in HTML
    assert 'INTEL_CAT=M30_SELECTED' in HTML
    assert 'const M30_TECHS=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in HTML

def test_v30_readiness_and_provenance_separated():
    assert 'M30_READY.records=true' in HTML
    assert 'M30_READY.benchmark=true' in HTML
    assert 'M30_READY.financials=true' in HTML
    assert 'M30_READY.weekly=true' in HTML
    assert 'M30_READY.ir=true' in HTML
    assert 'DB=d;M30_READY.records=true;render()' in HTML
    assert 'new Date(DB.generated_at)' in HTML
    assert "BENCH.reviewed_on" in HTML
    assert "FINANCIALS.reviewed_on" in HTML
    assert 'M28_COMPANIES.some(c=>c.rx.test(String(r.title||"")))' in HTML
    assert 'r.review_status==="human_review_required"' in HTML
    assert '등록 제품 · 수동 출처 확인' in HTML
    assert '공식 실적 · 수동 검증' in HTML or '수동 검증입니다' in HTML or '수동 검증 스냅샷' in HTML
    assert '기업·기술 우열' in HTML
    assert 'M30_READY.records?num:"—"' in HTML

def test_v30_references_real_existing_data_types():
    records=RECORDS["records"]
    assert len(records)>0
    assert {r["category"] for r in records}.issubset({"GaN","SiC","IGBT","SJ MOSFET","SGT"})
    assert len(BENCH["devices"])>=22
    assert len(FINANCE["companies"])==4
    assert 'BENCH.devices||[]' in HTML
    assert 'FINANCIALS.companies||[]' in HTML
    assert 'PULSE27_ARCHIVE||[]' in HTML
    assert 'DB.records||[]' in HTML

def test_v30_release_history_drives_pdf_and_ppt():
    # Release history is append-only. Preserve V3.0 validation across later releases.
    v30=next(entry for entry in VERSIONS["entries"] if entry["version"]=="V3.0")
    assert len(VERSIONS["entries"])>=31
    assert VERSIONS["latest_version"]==VERSIONS["entries"][-1]["version"]
    assert all(v30[key] for key in ("summary","background","changes","value"))
    script=(ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
    assert '"version_history.json"' in script
    assert 'version_history.json?nocache=' in HTML
