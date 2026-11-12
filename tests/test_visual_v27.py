"""V2.7 Overview and Weekly chart integrity, record provenance and baseline safeguards."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
DATA=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
ARCHIVE=json.loads((ROOT/"site"/"reports"/"index.json").read_text(encoding="utf-8"))

def test_v27_overview_main_ui_and_rendering():
    for token in ('id="pulse27-overview-bars"','id="pulse27-overview-stats"',
                  'id="pulse27-updated"','function pulse27Overview()',
                  'pulse27Overview();','id="pulse27-go-weekly"'):
        assert token in HTML
    assert HTML.index('id="pulse27-overview-bars"') < HTML.index('id="total"')
    assert "DB.records||[]" in HTML
    assert 'r.category===t' in HTML
    assert 'DB.generated_at' in HTML

def test_v27_weekly_existing_reports_only():
    for token in ('id="pulse27-weekly-bars"','id="pulse27-weekly-history"',
                  'id="pulse27-weekly-kpis"','function pulse27Week(report)',
                  'PULSE27_ARCHIVE=items.filter','pulse27Week(report);'):
        assert token in HTML
    assert 'report.by_category||{}' in HTML
    assert 'rows.length<2?' in HTML
    assert 'report.research_reference_count' in HTML
    assert 'reports/index.json?nocache=' in HTML
    assert "if(!items.length)" in HTML

def test_v27_stored_snapshot_is_not_extrapolated():
    weeks=ARCHIVE["reports"]
    assert len({x["week"] for x in weeks})==len(weeks)
    for r in weeks:
        file=ROOT/"site"/r["file"]
        report=json.loads(file.read_text(encoding="utf-8"))
        assert report["week"]==r["week"]
        assert sum(report["by_category"].values())==report["published_this_week_count"]
        assert report["new_items_count"]>=0
    assert len(DATA["records"])>=len(weeks)
