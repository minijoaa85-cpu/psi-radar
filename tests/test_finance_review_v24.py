"""V2.4 personal IR review is client-only and isolated from verified finance data."""
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] / "site" / "index.html").read_text(encoding="utf-8")

def test_v24_review_ui_and_controls():
    for token in (
        'id="finance-review-filter"',
        'id="finance-review-export"',
        'id="finance-review-clear"',
        'id="finance-review-summary"',
        'data-finance-review-url',
        'finance-review-control',
    ):
        assert token in HTML

def test_v24_review_local_only_and_no_financial_mutation():
    assert 'psi-radar-finance-review-v1' in HTML
    assert 'localStorage.setItem(FINANCE_REVIEW_KEY' in HTML
    assert 'localStorage.removeItem(FINANCE_REVIEW_KEY' in HTML
    assert 'FINANCE_REVIEWS[r.url]' in HTML
    assert 'financials.json?nocache=' in HTML
    assert 'FINANCE_REVIEWS=' in HTML
    assert 'fetch("financials.json"' in HTML
    assert 'fetch("financial_ir_watch.json' in HTML
    assert 'fetch("financials.json",{' not in HTML

def test_v24_export_formula_escape_and_review_labels():
    assert 'match=>"\'"+match' in HTML
    for label in ("미검토", "검토 중", "검토 완료(개인 기록)", "보류"):
        assert label in HTML
