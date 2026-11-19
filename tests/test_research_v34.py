"""V3.4 academic breadth & evidence-separated relevance; no live-network dependence."""
import json
from pathlib import Path
from scripts import research, relevance
from scripts.snapshot_quality import verify

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
COLLECT=(ROOT/"scripts"/"collect.py").read_text(encoding="utf-8")
QUALITY=(ROOT/"scripts"/"snapshot_quality.py").read_text(encoding="utf-8")
DATA=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))

def test_gan_and_sic_get_focused_year_long_queries():
    assert set(research.QUERIES)=={"GaN","SiC","IGBT","SJ MOSFET","SGT"}
    for tech in ("GaN","SiC"):
        assert len(research.QUERIES[tech])>=3
        assert any("reliability" in query.lower() for query in research.QUERIES[tech])
    assert 'collect_focused(session,now,include_coverage=True)' in COLLECT
    assert '"research_coverage":research_coverage' in COLLECT
    assert '"relevance_method":"metadata-rule-v2"' in COLLECT
    assert '"published_papers"' in COLLECT
    assert '"reused_papers"' in COLLECT
    assert '"result_state"' in COLLECT

def test_research_provider_success_and_zero_are_different(monkeypatch):
    from datetime import datetime, timezone
    from requests import HTTPError
    now=datetime(2026,11,19,tzinfo=timezone.utc)
    paper=research.make_record("GaN","GaN HEMT dynamic on-resistance reliability","2026-09-16",
        "IEEE Transactions on Electron Devices","https://doi.org/10.1234/example",
        "10.1234/example","dynamic on-resistance measurement","Crossref")
    def fake_crossref(session,q,cat,start,end):
        if cat=="SiC":raise HTTPError("synthetic unavailable")
        return [paper] if cat=="GaN" else []
    def fake_alex(session,q,cat,start,end):
        if cat=="SiC":raise HTTPError("synthetic unavailable")
        return [paper] if cat=="GaN" else []
    monkeypatch.setattr(research,"crossref_search",fake_crossref)
    monkeypatch.setattr(research,"openalex_search",fake_alex)
    found,errors,stats,cov=research.collect_focused(object(),now,include_coverage=True)
    assert set(cov)==set(research.QUERIES)
    assert stats["GaN"]==1 and len([r for r in found if r["category"]=="GaN"])==1
    assert cov["GaN"]["successful"]>=1
    assert cov["GaN"]["search_state"]=="searched"
    assert cov["SiC"]["successful"]==0
    assert cov["SiC"]["search_state"]=="unavailable"
    assert cov["SiC"]["failed"]==cov["SiC"]["attempted"]
    assert errors
    assert all(0<=v["accepted_candidates"]<=24 for v in cov.values())

def test_technical_and_monitoring_signals_are_not_credibility():
    subject="GaN HEMT announces new 650V power transistor for data center"
    news=relevance.relevance({"kind":"news","category":"GaN","title":subject})
    official=relevance.relevance({"kind":"official","category":"GaN","title":subject})
    assert news["relevance_method"]=="metadata-rule-v2"
    assert news["technical_relevance_score"]==official["technical_relevance_score"]
    assert news["monitoring_priority_score"]==official["monitoring_priority_score"]
    assert news["evidence_tier"]!=official["evidence_tier"]
    assert news["monitoring_signal"]=="제품·양산 발표 후보"
    physics=relevance.relevance({"kind":"paper","category":"SiC",
        "title":"SiC MOSFET trench gate oxide reliability and channel mobility",
        "abstract":"Threshold instability and oxide reliability measurements"})
    assert physics["technical_relevance_score"]>news["technical_relevance_score"]
    assert "Reliability" in physics["relevance_topics"]
    assert 0<=physics["monitoring_priority_score"]<=100
    assert "source credibility" not in physics["evidence_tier"]

def test_legacy_snapshot_is_not_mislabeled_as_queried():
    report=verify(ROOT/"site")
    assert report["structural_integrity"]=="passed"
    assert 'research_coverage' in report
    if "research_coverage" not in DATA:
        assert report["research_coverage"]=={}
    assert 'research query outcomes unavailable for pre-V3.4 snapshot' in QUALITY
    for marker in ('id="coverage34"','id="coverage34-grid"',
                   'id="coverage34-stamp"','function renderCoverage34()',
                   '검색 이력 미기록','검색 성공 · 일치 문헌 0',
                   '수집 API 사용 불가','renderCoverage34();'):
        assert marker in HTML

def test_v34_release_history_shared_pdf_ppt():
    assert HISTORY["latest_version"]=="V3.4"
    assert len(HISTORY["entries"])==35
    assert HISTORY["entries"][-1]["version"]=="V3.4"
    assert all(HISTORY["entries"][-1].get(k) for k in ("summary","background","changes","value"))
    assert '"version_history.json"' in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
