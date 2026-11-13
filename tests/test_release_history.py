"""Release history is structured, complete and integrated with both downloads."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
WORKFLOW=(ROOT/".github"/"workflows"/"weekly.yml").read_text(encoding="utf-8")

def test_history_has_unique_ordered_versions_and_explanations():
    assert HISTORY["schema_version"]==1
    rows=HISTORY["entries"]
    assert len(rows)>=29
    assert HISTORY["latest_version"]==rows[-1]["version"]
    assert any(x["version"]=="V2.8" for x in rows)
    assert len({x["version"] for x in rows})==len(rows)
    assert rows[0]["version"]=="V0.3"
    for row in rows:
        assert all(isinstance(row.get(k),str) and len(row[k])>=3 for k in ("title","summary","background","changes","value","date"))
        assert row["version"].startswith("V")

def test_history_optional_rail_and_live_build_identity():
    for value in ('id="history-quick-access"','id="history-close"','id="history-list"',
                  'id="history-current-version"','id="history-filter"',
                  'id="ui-release-label"','version_history.json?nocache='):
        assert value in HTML
    assert '"history-quick-access","history","history-close"' in HTML
    assert 'if(tab==="history")' in HTML
    assert 'tab!=="history"' in HTML
    assert 'id="history" class="hidden"' in HTML

def test_pdf_ppt_are_generated_from_same_source_before_pages_publish():
    for name in ('psi-radar-version-history.pdf','psi-radar-version-history.pptx'):
        assert 'docs/'+name in HTML
        assert name in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
    assert "python -m scripts.build_history_slides" in WORKFLOW
    assert WORKFLOW.index("python -m scripts.build_history_slides")<WORKFLOW.index("actions/upload-pages-artifact@v3")
    assert "site/version_history.json" in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8") or '"version_history.json"' in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
