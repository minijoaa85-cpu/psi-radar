"""V3.3 source quality: fail closed on corrupt snapshots and invalid archives."""
import json
import shutil
from pathlib import Path
from scripts.snapshot_quality import verify

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
WORKFLOW=(ROOT/".github"/"workflows"/"weekly.yml").read_text(encoding="utf-8")
HTML=(SITE/"index.html").read_text(encoding="utf-8")

def test_existing_committed_snapshot_is_consistent():
    report=verify(SITE)
    assert report["structural_integrity"]=="passed", report["errors"]
    assert report["records"]>0
    assert report["counts_by_kind"]["official"]+report["counts_by_kind"]["paper"]+report["counts_by_kind"]["news"]==report["records"]
    assert report["snapshot_generated_at"]==json.loads((SITE/"data.json").read_text(encoding="utf-8"))["generated_at"]
    assert report["scientific_verification"]=="not_independently_verified"
    assert len(report["files_sha256"]["data.json"])==64
    assert report["archives_sha256"]
    assert set(report["category_counts"])=={"GaN","SiC","IGBT","SJ MOSFET","SGT"}

def test_corrupt_metadata_and_archive_are_rejected(tmp_path):
    site=tmp_path/"site"
    site.mkdir()
    (site/"reports").mkdir()
    for name in ("data.json","benchmark.json","financials.json"):
        shutil.copy2(SITE/name,site/name)
    shutil.copy2(SITE/"reports"/"index.json",site/"reports"/"index.json")
    for item in json.loads((SITE/"reports"/"index.json").read_text(encoding="utf-8"))["reports"]:
        shutil.copy2(SITE/item["file"],site/item["file"])
    records=json.loads((site/"data.json").read_text(encoding="utf-8"))
    records["records"][1]["id"]=records["records"][0]["id"]
    (site/"data.json").write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
    errors=verify(site)["errors"]
    assert any("duplicate" in e for e in errors)
    records["records"][1]["id"]="an_unduplicated_test_id"
    records["counts"]["GaN"] += 1
    (site/"data.json").write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
    assert any("counts differ" in e for e in verify(site)["errors"])
    records["counts"]["GaN"] -= 1
    official=next(row for row in records["records"] if row["kind"]=="official")
    original_url=official["url"]
    official["url"]="https://unverified.example.net/claimed-press-release"
    (site/"data.json").write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
    assert any("official URL domain" in e for e in verify(site)["errors"])
    official["url"]=original_url
    (site/"data.json").write_text(json.dumps(records,ensure_ascii=False),encoding="utf-8")
    weekly=json.loads((site/"reports"/"index.json").read_text(encoding="utf-8"))
    weekly["generated_at"]="2020-01-01T00:00:00+00:00"
    (site/"reports"/"index.json").write_text(json.dumps(weekly),encoding="utf-8")
    assert any("generated_at" in e for e in verify(site)["errors"])

def test_code_push_and_collection_are_distinct_paths():
    assert "if: github.event_name != 'push'" in WORKFLOW
    assert WORKFLOW.count("if: github.event_name != 'push'")>=12
    assert "python -m scripts.snapshot_quality --write" in WORKFLOW
    assert "python -m scripts.snapshot_quality --check" in WORKFLOW
    assert WORKFLOW.index("python -m scripts.weekly_report")<WORKFLOW.index("python -m scripts.snapshot_quality --write")
    assert WORKFLOW.index("python -m scripts.snapshot_quality --check")<WORKFLOW.index("Persist latest successful data")
    assert "git diff --exit-code HEAD -- site/data.json" in WORKFLOW
    assert 'git rev-parse origin/main' in WORKFLOW
    assert "source_health.json" in WORKFLOW
    assert "python -m scripts.build_history_slides" in WORKFLOW
    assert "actions/deploy-pages@v4" in WORKFLOW

def test_dashboard_does_not_claim_independent_verification():
    for text in ('id="trust33"','id="trust33-status"','id="trust33-quality"',
                 'function trust33View()','source_health.json?nocache=',
                 'scientific_verification','source_evidence_tiers',
                 '기술 관련성 점수는 키워드 기반이며 출처 신뢰도 점수가 아닙니다'):
        assert text in HTML
    assert "TRUST33=report" in HTML
    assert "TRUST33_ERROR" in HTML
    assert 'raw.snapshot_generated_at===DB.generated_at' in HTML
    assert 'raw.records===(DB.records||[]).length' in HTML
