"""V2.1 navigation hierarchy and evidence-limited integrated pulse regressions."""
from pathlib import Path
from scripts.integrated import TECHNOLOGIES, make_integrated

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"site"/"index.html").read_text(encoding="utf-8")

def fixtures():
    briefing={"generated_at":"2026-11-12T06:00:00+00:00","categories":[{"category":"GaN","items":[
        {"title":"Research metadata","date":"2026-11-10","source_level":"research",
         "url":"https://example.com/research","companies":[]}
    ]}]}
    topics={"topics":[]}
    architecture={"categories":[{"category":"GaN","intro":"GaN devices","physics":[],"watch":[]}]}
    benchmark={"reviewed_on":"2026-11-12","devices":[]}
    return briefing,topics,architecture,benchmark



def test_navigation_follows_user_workflow_in_four_visible_groups():
    nav=HTML.split('<nav id="nav"',1)[1].split("</nav>",1)[0]
    labels=["① 시작","② 주간 동향","③ 기술 분석","④ 경쟁사·제품"]
    assert all(label in nav for label in labels)
    assert [nav.index(label) for label in labels]==sorted(nav.index(label) for label in labels)
    assert nav.index('data-tab="overview"')<nav.index('data-tab="weekly"')<nav.index('data-tab="integrated"')<nav.index('data-tab="competitors"')
    for tab in ("overview","weekly","briefing","market","integrated","technology","research","architecture","competitors","benchmark"):
        assert nav.count(f'data-tab="{tab}"')==1
    assert 'data-tab="watchlist"' not in nav
    assert 'data-tab="sources"' not in nav
    assert "nav-links" in nav and "nav-group" in nav


def test_mobile_grouped_menu_does_not_hide_subpages():
    css=HTML.split("<style>",1)[1].split("</style>",1)[0]
    assert ".nav.nav-journey" in css
    assert "grid-template-columns:1fr" in css
    assert '@media(max-width:600px)' in css
    assert ".nav.nav-journey .nav-group button" in css
    assert "white-space:normal" in css


def test_integrated_weekly_sample_is_archived_not_fabricated():
    b,t,a,p=fixtures()
    snapshots=[
        {"week":"2026-W45","complete_week":True,"week_to_date":"2026-11-08",
         "topics":[{"category":"GaN","count":2,"category_sample_count":4,
                    "source_kinds":{"manufacturer_announcement":1}},
                   {"category":"GaN","count":1,"category_sample_count":4,
                    "source_kinds":{"paper_metadata":1}}]},
        {"week":"2026-W46","complete_week":False,"week_to_date":"2026-11-12",
         "topics":[{"category":"GaN","count":1,"category_sample_count":2,
                    "source_kinds":{}}]},
    ]
    rows=make_integrated(b,t,a,p,snapshots)["categories"]
    gan=rows[0]
    assert [r["week"] for r in gan["weekly_observations"]]==["2026-W45","2026-W46"]
    assert [r["category_sample_count"] for r in gan["weekly_observations"]]==[4,2]
    assert gan["weekly_observations"][0]["topic_title_matches"]==3
    assert gan["weekly_observations"][0]["topic_official_matches"]==1
    assert gan["weekly_observations"][-1]["complete_week"] is False
    assert all(not r["weekly_observations"] for r in rows[1:])


def test_integrated_company_counts_are_briefing_mentions_not_rankings():
    b,t,a,p=fixtures()
    b["categories"][0]["items"] += [
        {"title":"Company article","url":"https://example.com/co",
         "source_level":"news","date":"2026-11-11","companies":["infineon","st"]},
        {"title":"Official release","url":"https://example.com/pr",
         "source_level":"official","date":"2026-11-12","companies":["infineon"]},
    ]
    data=make_integrated(b,t,a,p)
    companies={x["id"]:x for x in data["categories"][0]["competitor_mentions"]}
    assert companies["infineon"]["mention_count_sample"]==2
    assert companies["infineon"]["official_count_sample"]==1
    assert companies["st"]["mention_count_sample"]==1
    assert "기술력 순위" in data["warning"]
    assert [r["category"] for r in data["categories"]]==list(TECHNOLOGIES)


def test_crosslinks_in_integrated_retain_category():
    for phrase in ("intel-weekly-bars","intel-competitor-pulse","data-intel-company-id",
                   'destination==="weekly"','destination==="research"',
                   'destination==="competitors"','el("research-cat").value=INTEL_CAT',
                   'el("company-tech").value=INTEL_CAT'):
        assert phrase in HTML
    assert "저장된 주차" in HTML
    assert "없는 주차는 채우지 않습니다" in HTML
