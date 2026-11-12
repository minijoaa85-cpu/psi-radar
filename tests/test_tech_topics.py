"""V1.2 evidence matching regression; no unsupported scientific claims."""
from pathlib import Path
from scripts.tech_topics import TOPICS,hit_title,news_matches,build_map

def topic(name):
 return next(t for t in TOPICS if t["id"]==name)

def test_gan_frequency_dispersion_maps_only_to_dynamic_rds_on():
 article={"id":"a","kind":"news","category":"GaN","title":"Mitsubishi demonstrates suppression of frequency dispersion in GaN","url":"https://example.org/real-article","date":"2026-11-12"}
 assert news_matches(article,topic("gan-dynamic-ron"))
 assert not news_matches(article,topic("sic-trench"))
 assert not news_matches(article,topic("gan-gate"))

def test_generic_mentions_do_not_create_research_evidence():
 article={"id":"b","kind":"news","category":"GaN","title":"GaN demand may increase next year","url":"https://example.org/news"}
 result=build_map([article],{"devices":[]})
 assert all(not t["article_candidates"] for t in result["topics"])

def test_title_matching_does_not_imply_verified_result():
 item={"id":"p","category":"SJ MOSFET","kind":"paper","title":"Pillar Charge Balance in Superjunction Devices","url":"https://doi.org/10.1234/example"}
 result=build_map([item],{"devices":[]})
 refs=next(t["article_candidates"] for t in result["topics"] if t["id"]=="sj-pillar")
 assert len(refs)==1 and refs[0]["kind"]=="paper_metadata"
 assert refs[0]["confidence"]=="title_keyword_match"
 assert "인과관계" in result["warning"]

def test_manufacturer_announcement_and_device_reference_distinct():
 item={"id":"o","category":"GaN","kind":"official","title":"GaN switching loss and gate charge","source_type":"manufacturer_official","url":"https://www.st.com/example"}
 product={"id":"part","part":"P1","company":"Maker","category":"GaN","url":"https://www.st.com/part","specs":{"qg":{"value":7,"unit":"nC","kind":"typ"}}}
 result=build_map([item],{"devices":[product]})
 t=next(t for t in result["topics"] if t["id"]=="gan-switching")
 assert t["article_candidates"][0]["kind"]=="manufacturer_announcement"
 assert t["products"][0]["relationship"]=="same_technology_reference_only"
 assert "qg" in t["products"][0]["metrics_available"]

def test_sgt_with_no_verified_product_does_not_fabricate_values():
 result=build_map([],{"devices":[]})
 assert all(not t["products"] for t in result["topics"] if t["category"]=="SGT")

def test_user_friendly_architecture_ui_has_topic_controls():
 s=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
 assert 'id="arch-topic-buttons"' in s
 assert 'id="arch-topic-detail"' in s
 assert 'topic_map.json?nocache=' in s
 assert "논문 실험 결과·제품 구조와의 인과관계는 검증하지 않았습니다" in s
 assert "renderTopicExplorer(selected.category)" in s

def test_tech_map_covers_five_categories_and_unique_ids():
 assert {t["category"] for t in TOPICS}=={"GaN","SiC","IGBT","SGT","SJ MOSFET"}
 ids=[t["id"] for t in TOPICS]
 assert len(ids)==len(set(ids))
