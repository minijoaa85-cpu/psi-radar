"""V3.2 weekly evidence comparison stays grounded in stored report snapshots."""
import json
import datetime as dt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))
INDEX=json.loads((ROOT/"site"/"reports"/"index.json").read_text(encoding="utf-8"))
CATS=("GaN","SiC","IGBT","SJ MOSFET","SGT")

def test_v32_interface_and_download_are_source_driven():
    for token in ('id="weekly-review32"','id="weekly-review32-base"',
                  'id="weekly-review32-metrics"','id="weekly-review32-bars"',
                  'id="weekly-review32-sources"','id="weekly-review32-status"',
                  'id="weekly-review32-download"','id="weekly-review32-copy"',
                  'function w32Valid(report)','function w32Coverage(report)',
                  'function w32AsMarkdown(current,base)','function w32Render()',
                  'function w32SetCurrent(report)'):
        assert token in HTML
    assert HTML.index('id="weekly-review32"')<HTML.index('id="weekly-details"')
    assert 'w32SetCurrent(report);' in HTML
    assert 'W32_CACHE=new Map()' in HTML
    assert "reports/index.json?nocache=" in HTML
    assert 'file==="reports/"+report.week+".json"' in HTML or 'file!=="reports/"+report.week+".json"' in HTML
    assert '"psi-radar-weekly-evidence-v32.md"' in HTML
    assert 'navigator.clipboard.writeText(W32_REPORT_TEXT)' in HTML

def test_v32_never_claims_weekly_growth_from_partial_snapshots():
    assert 'generated>=end?"주차 완료 후 생성":"주차 진행 중/기준일 미확인"' in HTML
    assert 'W32_TECHS.reduce((sum,k)=>sum+report.by_category[k],0)===report.published_this_week_count' in HTML
    assert 'Array.isArray(report.weekly_items)' in HTML
    assert 'current.week===base.week' in HTML
    assert 'w32Valid(current)' in HTML and 'w32Valid(base)' in HTML
    assert '기술 순위 아님' in HTML or '성능 순위' in HTML
    assert '증감률·성능 순위 아님' in HTML
    assert '수집 공백·진행 중인 주차를 0% 성장이나 기술 활동 부재로 해석하지 않습니다.' in HTML
    assert 'weekly_items.slice(0,10)' in HTML
    assert 'target="_blank" rel="noopener noreferrer"' in HTML

def test_saved_reports_are_real_and_partial_before_week_end():
    entries=INDEX["reports"]
    assert len(entries)>=2
    for entry in entries:
        data=json.loads((ROOT/"site"/entry["file"]).read_text(encoding="utf-8"))
        assert data["week"]==entry["week"]
        assert sum(data["by_category"].get(k,0) for k in CATS)==data["published_this_week_count"]
        assert all(isinstance(data["by_category"][k],int) and data["by_category"][k]>=0 for k in CATS)
        assert data["published_this_week_count"]>=0
    w47=json.loads((ROOT/"site"/"reports"/"2026-W47.json").read_text(encoding="utf-8"))
    start=dt.datetime.fromisoformat(w47["week_start"]+"T00:00:00+09:00")
    gen=dt.datetime.fromisoformat(w47["generated_at"])
    assert gen<start+dt.timedelta(days=7)
    assert w47["published_this_week_count"]==0

def test_v32_append_only_history_and_presentation_generator():
    v32=next(x for x in HISTORY["entries"] if x["version"]=="V3.2")
    assert HISTORY["latest_version"]==HISTORY["entries"][-1]["version"]
    assert len(HISTORY["entries"])>=33
    assert all(v32.get(k) for k in ("summary","background","changes","value"))
    build=(ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
    assert '"version_history.json"' in build
    assert "pdf(" in build and "ppt(" in build
