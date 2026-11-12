"""V2.6 visually prioritized, source-bound and safe financial dashboards."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")

def test_v26_visuals_are_primary_and_details_accessible():
    assert 'id="finance-visual-title"' in HTML
    assert 'id="finance-visual-grid"' in HTML
    assert 'function renderFinanceVisual()' in HTML
    assert 'renderFinanceVisual();' in HTML
    assert HTML.index('id="finance-visual-grid"') < HTML.index('id="finance-cards"')
    assert '<details class="portal-details finance-visual-detail">' in HTML
    assert 'finance-visual-ring' in HTML
    assert 'finance-visual-bar' in HTML
    assert '@media(max-width:760px){.finance-visual-grid{grid-template-columns:1fr}' in HTML

def test_v26_no_cross_company_nominal_comparison_or_fabricated_tech_share():
    assert 'period_type===latest.period_type' in HTML
    assert 'x.period===latest.period&&x.period_type===latest.period_type&&x.start===latest.start&&x.end===latest.end' in HTML
    assert 'seg.revenue<=latest.revenue' in HTML
    assert '연결 매출 대비 비율 · 기술별 점유율 아님' in HTML
    assert 'Math.max(Math.abs(a),Math.abs(b),1)' in HTML
    assert '같은 회사·같은 통화' in HTML
    assert 'latest.source' in HTML
    assert 'FINANCIALS.reviewed_on' in HTML

def test_v26_read_only_and_existing_financial_workflows():
    assert 'fetch("financials.json?nocache="' in HTML
    assert 'fetch("financial_review_diff.json?nocache="' in HTML
    assert 'id="finance-ir-items"' in HTML
    assert 'id="finance-review-export"' in HTML
    assert 'localStorage.setItem(FINANCE_REVIEW_KEY' in HTML
    assert 'fetch("financials.json",{' not in HTML
