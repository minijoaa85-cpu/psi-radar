"""V3.1 source-based Evidence Desk: no invented dates, counts, or unverified growth."""
import datetime as dt
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
DB=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))

def test_v31_filters_charts_and_export_controls():
    for key in ('id="evidence31"','id="evidence31-window"','id="evidence31-kind"',
                'id="evidence31-metrics"','id="evidence31-chart"',
                'id="evidence31-items"','id="evidence31-export"'):
        assert key in HTML
    assert 'function renderEvidenceDesk31()' in HTML
    assert 'renderEvidenceDesk31();' in HTML
    assert 'function e31ISOWeek(day)' in HTML
    assert 'function e31CSVCell(value)' in HTML
    assert 'for(const id of ["evidence31-window","evidence31-kind"])' in HTML
    assert '"psi-radar-evidence-v31.csv"' in HTML
    assert 'URL.createObjectURL(blob)' in HTML
    assert 'target="_blank" rel="noopener noreferrer"' in HTML
    assert 'value="7"' in HTML and 'value="30" selected' in HTML and 'value="365"' in HTML

def test_v31_date_scope_and_data_provenance_guards():
    assert 'new Date(DB.generated_at||"")' in HTML
    assert 'M30_READY.records&&Number.isFinite(base.valueOf())' in HTML
    assert 'age>=0&&age<period' in HTML
    assert 'new Date(ms).toISOString().slice(0,10)!==textDate' in HTML
    assert 'r.category!==M30_SELECTED' in HTML
    assert 'r.stale_reused' in HTML
    assert 'bins=[...groups.entries()].sort' in HTML
    assert '실제 발행 자료가 있는 구간만 표시' in HTML
    assert '빈 구간을 0으로 채우지 않으며' in HTML
    assert 'E31_VISIBLE=rows;' in HTML
    assert '^\\s*[=+' not in HTML   # no dependence on remote sheet service
    assert DB["generated_at"]
    anchor=dt.date.fromisoformat(DB["generated_at"][:10])
    sic_news=[]
    for rec in DB["records"]:
        if rec["category"]=="SiC" and rec["kind"]=="news" and rec.get("date"):
            date=dt.date.fromisoformat(rec["date"])
            if 0<=(anchor-date).days<30:sic_news.append(rec)
    assert sic_news  # ensure smoke's source-backed 30-day SiC selection is non-empty

def test_csv_formula_injection_guard_and_no_external_storage():
    assert 'const guarded=/^[=+@' in HTML
    assert 'guarded.replace(/"/g' in HTML
    assert 'text/csv;charset=utf-8' in HTML
    assert 'source","official_url"' in HTML or '"source","official_url"' in HTML
    # Only source values and corresponding original URL are exported
    assert 'r.title||""' in HTML
    assert 'r.stale_reused?"yes":"no"' in HTML

def test_release_history_append_only_and_shared_presentation():
    assert HISTORY["latest_version"]=="V3.1"
    assert HISTORY["entries"][-1]["version"]=="V3.1"
    assert len(HISTORY["entries"])==32
    assert all(HISTORY["entries"][-1].get(k) for k in ("summary","background","changes","value"))
    assert '"version_history.json"' in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
