"""V2.0 integrated analysis must preserve evidence boundaries and source conditions."""
from pathlib import Path

from scripts.integrated import TECHNOLOGIES, make_integrated, safe_https

ROOT=Path(__file__).resolve().parents[1]


def fixtures():
    briefing={
        "generated_at":"2026-11-12T06:00:00+00:00",
        "categories":[{
            "category":"GaN","items":[
                {"title":"Dynamic RDS(on) discussed","url":"https://example.com/paper",
                 "source_level":"research","date":"2026-11-10",
                 "summary":"Metadata only","source":"Journal","topic_ids":["gan-dynamic-ron"],"companies":[]},
                {"title":"Duplicated URL","url":"https://example.com/paper",
                 "source_level":"research","date":"2026-11-10","topic_ids":[]},
                {"title":"Untrusted local URL","url":"http://example.com/item",
                 "source_level":"official","date":"2026-11-11","topic_ids":[]},
            ]
        }]
    }
    topics={"topics":[{"category":"GaN","id":"gan-dynamic-ron",
                       "name":"Dynamic RDS(on)","simple":"Dynamic on-resistance",
                       "why":"Trapping","article_candidates":[
                            {"title":"Current Collapse", "url":"https://example.com/ref",
                             "publisher":"Journal","kind":"paper_metadata","date":"2026-11-10"},
                            {"title":"Unsafe", "url":"javascript:alert(1)", "kind":"news_title_candidate"},
                       ]}]}
    architecture={"categories":[{"category":"GaN","intro":"E-mode GaN",
                                 "physics":["dynamic RDS(on)"],"watch":["Gate stack"]}]}
    benchmark={"reviewed_on":"2026-11-12","devices":[{
        "id":"gan-a","category":"GaN","company":"Infineon","part":"GANA",
        "structure":"E-mode HEMT","package":"TOLL",
        "voltage":{"value":650,"unit":"V"},"url":"https://www.infineon.com/part/GANA",
        "verification":"product_page","specs":{
            "rds_on":{"value":55,"unit":"mΩ","kind":"typ","condition":"VGS not published"},
            "qg":{"value":4,"unit":"nC","kind":"unspecified","condition":"Not published"}},
    }]}
    return briefing,topics,architecture,benchmark


def test_five_categories_and_last_sgt_even_when_no_products():
    data=make_integrated(*fixtures())
    assert [row["category"] for row in data["categories"]]==list(TECHNOLOGIES)
    assert data["categories"][-1]["product_count"]==0
    assert data["categories"][-1]["articles"]==[]
    assert "자료 0건은 연구 부재" in data["warning"]


def test_no_duplicated_or_insecure_source_links():
    data=make_integrated(*fixtures())
    gan=data["categories"][0]
    assert len(gan["articles"])==1
    assert gan["articles"][0]["url"]=="https://example.com/paper"
    assert len(gan["topics"][0]["evidence"])==1
    assert gan["topics"][0]["evidence"][0]["confidence"]=="title_keyword_match"
    assert not safe_https("https://user:password@example.com/secret")
    assert not safe_https("http://example.com/item")


def test_manufacturer_specs_are_not_normalized_without_conditions():
    gan=make_integrated(*fixtures())["categories"][0]
    assert gan["product_count"]==1
    assert gan["datasheet_table_verified_count"]==0
    assert gan["structured_test_conditions_count"]==0
    assert gan["products"][0]["specs"]["qg"]["kind"]=="unspecified"
    assert gan["products"][0]["specs"]["rds_on"]["condition"]=="VGS not published"
    assert "VGS/ID/Tj" in make_integrated(*fixtures())["warning"]


def test_article_and_product_are_same_category_reference_not_false_causal_link():
    gan=make_integrated(*fixtures())["categories"][0]
    assert gan["topics"][0]["id"]=="gan-dynamic-ron"
    assert gan["articles"][0]["source_level"]=="research"
    assert gan["products"][0]["company"]=="Infineon"
    assert "인과관계" in make_integrated(*fixtures())["warning"]


def test_v2_ui_supports_linked_sections_and_stable_legacy_views():
    page=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
    assert 'data-tab="integrated"' in page
    assert 'id="integrated"' in page
    for id in ("intel-categories","intel-topics","intel-evidence","intel-products",
               "intel-company","intel-kpis","intel-warning"):
        assert f'id="{id}"' in page
    assert "integrated.json?nocache=" in page
    assert "data-intel-product" in page
    assert 'activateRadarTab("benchmark")' in page
    assert 'activateRadarTab(destination)' in page
    assert 'el("arch-category").value=INTEL_CAT' in page
    assert 'el("brief-category").value=INTEL_CAT' in page
    assert 'id="watch-quick-access"' in page
    assert 'id="quality-quick-access"' in page


def test_integrated_mobile_layout_and_no_rankings():
    page=(ROOT/"site"/"index.html").read_text(encoding="utf-8")
    assert "@media(max-width:800px){.intel-evidence-grid{grid-template-columns:1fr}}" in page
    assert "뉴스는 제목·메타데이터 기준 후보" not in page or "메타데이터 기준 후보" in page
    assert "같은 분야의 참고자료" in page
    assert "FOM" not in str(make_integrated(*fixtures())["categories"][0]["products"])
