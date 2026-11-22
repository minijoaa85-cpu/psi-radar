"""V3.5 executive reading queue: source fidelity and no invented product conclusions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
BRIEF=json.loads((ROOT/"site"/"briefing.json").read_text(encoding="utf-8"))
DATA=json.loads((ROOT/"site"/"data.json").read_text(encoding="utf-8"))
HISTORY=json.loads((ROOT/"site"/"version_history.json").read_text(encoding="utf-8"))

def test_executive_first_screen_and_drilldown():
    assert HTML.index('id="trust33"')<HTML.index('id="exec35"')<HTML.index('id="mission30"')
    for token in ('id="exec35-status"','id="exec35-cards"','id="exec35-open"',
                  'id="exec35-kpis"','function renderExecutive35()',
                  'renderExecutive35();','EX35_ORDER=["GaN","SiC","IGBT","SJ MOSFET","SGT"]',
                  'showRadarSection("briefing")','el("brief-category").value=b.dataset.ex35Tech'):
        assert token in HTML
    assert 'BRIEFING.generated_at!==DB.generated_at' in HTML
    assert "검토 목록을 표시하지 않습니다" in HTML

def test_brief_source_levels_and_evidence_do_not_claim_verified_performance():
    assert BRIEF["generated_at"]==DATA["generated_at"]
    rows=[x for cat in BRIEF["categories"] for x in cat["items"]]
    assert rows
    for entry in rows:
        assert entry["source_level"] in ("official","research","news")
        assert entry["url"].startswith("https://")
    for phrase in ("제조사 공식 주장(독립 검증 전)","논문 서지 자료(본문 검증 전)",
                   "뉴스 제목 후보(원문 검증 전)","실제 신규성 미확인",
                   "일반적인 엔지니어링 확인 항목"):
        assert phrase in HTML

def test_recommendations_are_questions_not_unverified_facts():
    for q in ("Dynamic RDS(on)","Gate Oxide 신뢰성","VCE(sat)","Charge Balance","Qg/Qgd"):
        assert q in HTML
    assert "기술 우위의 순위나 이번 주 신규 발표 검증이 아닙니다." in HTML
    assert 'EX35_ORDER.map(tech=>' in HTML
    assert 'if(!row)return' in HTML

def test_history_and_slides_are_synchronized():
    assert HISTORY["latest_version"]=="V3.6"
    assert len(HISTORY["entries"])==37
    assert HISTORY["entries"][-1]["version"]=="V3.6"
    assert all(HISTORY["entries"][-1][key] for key in ("summary","background","changes","value"))
    assert "V3.5" in (ROOT/"scripts"/"build_history_slides.py").read_text(encoding="utf-8")
