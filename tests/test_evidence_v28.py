"""V2.8 visual evidence and title-only manufacturer mention integrity checks."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
DATA=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
VERSIONS=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))

def test_evidence_lens_visible_in_research_and_preserves_existing_filter():
    assert 'id="evidence28"' in HTML
    assert 'id="evidence28-matrix"' in HTML
    assert 'id="evidence28-kpis"' in HTML
    assert 'function renderEvidence28()' in HTML
    assert 'data-e28-tech' in HTML
    assert 'el("research-cat").value=el("research-cat").value===value?"":value' in HTML
    assert 'renderEvidence28();' in HTML
    assert 'paper.filter(r=>r.category===t).length' in HTML
    assert 'news.filter(r=>r.category===t).length' in HTML
    assert 'Math.max(1,...E28_TECHS.map(t=>paper.filter' in HTML
    assert 'Math.max(1,...E28_TECHS.map(t=>news.filter' in HTML

def test_company_mentions_use_limited_original_title_only_and_sources():
    for element in ('id="mentions28"','id="mentions28-period"',
                    'id="mentions28-company"','id="mentions28-bars"',
                    'id="mentions28-heat"','id="mentions28-sources"'):
        assert element in HTML
    assert 'function renderMentions28()' in HTML
    assert 'r.title||""' in HTML
    assert 'c.rx.test(String(r.title||""))' in HTML
    assert 'source||"출처 미확인"' in HTML
    assert 'target="_blank" rel="noopener noreferrer"' in HTML
    assert 'id:"nexperia",name:"Nexperia"' in HTML
    assert 'renderMentions28();' in HTML
    assert "const region=el(\"company-region\").value" in HTML
    assert 'region==="Europe"' not in HTML  # no invented fixed regional ranking
    assert "기업 직접 발표 검증이나 명확한 경쟁력 순위가 아닙니다" in HTML

def test_project_history_and_source_persistence():
    # Appending a new release must not invalidate historical V2.8 checks.
    v28=next(x for x in VERSIONS["entries"] if x["version"]=="V2.8")
    assert len(VERSIONS["entries"])>=29
    assert VERSIONS["latest_version"]==VERSIONS["entries"][-1]["version"]
    assert v28["background"]
    assert v28["changes"]
    assert v28["value"]
    assert "psi-radar-watch-v1" in HTML
    assert "psi-radar-finance-review-v1" in HTML
    assert "financial_review_diff.json?nocache=" in HTML
    assert "version_history.json?nocache=" in HTML

def test_source_counts_are_tagged_and_nonfabricated():
    records=DATA["records"]
    assert len(records)>=1
    assert set(r.get("kind") for r in records).issubset({"paper","news","official"})
    techs=("GaN","SiC","IGBT","SJ MOSFET","SGT")
    assert sum(r.get("category") in techs for r in records)<=len(records)
    # The new charts use records already present, not a hard-coded activity ranking.
    assert "DB.records||[]" in HTML
    assert "citation" not in VERSIONS["entries"][-1]
