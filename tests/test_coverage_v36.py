"""V3.6: collection coverage UI is gated on the exact published snapshot."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
HEALTH=json.loads((ROOT/"site"/"source_health.json").read_text(encoding="utf-8"))
DATA=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))

def test_coverage_cards_have_five_categories_and_snapshot_guard():
    assert 'id="coverage36"' in HTML
    assert 'id="coverage36-grid"' in HTML
    assert 'function renderCoverage36()' in HTML
    assert 'C36_ORDER=["GaN","SiC","IGBT","SJ MOSFET","SGT"]' in HTML
    assert 'TRUST33.snapshot_generated_at!==DB.generated_at' in HTML
    assert 'TRUST33.structural_integrity!=="passed"' in HTML
    assert 'renderCoverage36();' in HTML

def test_metrics_are_from_published_verified_research_coverage():
    assert HEALTH["snapshot_generated_at"]==DATA["generated_at"]
    coverage=HEALTH["research_coverage"]
    assert set(coverage)=={"GaN","SiC","IGBT","SJ MOSFET","SGT"}
    for technology,counts in coverage.items():
        assert counts["fresh_papers"]+counts["reused_papers"]==counts["published_papers"]
        assert counts["successful"]+counts["failed"]==counts["attempted"]
        assert counts["published_papers"]>=0

def test_empty_or_failed_query_not_mislabeled_as_no_industry_activity():
    for phrase in ("검색 미확인 — 0건으로 해석 금지","검색 성공, 게시 표본 0건",
                   "이전 수집 재사용","검색 성공은 논문 내용 검증이 아닙니다."):
        assert phrase in HTML
