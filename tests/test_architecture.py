from scripts.architecture import compile_architecture,structure,OVERVIEW,CATS
from scripts.validate_benchmark import load

def test_all_technical_categories_visible_even_if_no_products():
 result=compile_architecture(load())
 assert [x["category"] for x in result["categories"]]==list(CATS)
 assert result["categories"][-1]["category"]=="SGT"
 assert result["categories"][-1]["count"]==0
 assert all(x["physics"] and x["watch"] for x in result["categories"])
def test_st_mastergan_not_mislabelled_discrete():
 rows=load()["devices"]
 integrated=next(x for x in rows if x["part"]=="MASTERGAN6")
 assert structure(integrated)=="드라이버 통합형"
 assert "Trench SiC" in structure(next(x for x in rows if x["part"]=="SCT4036KWATL"))
def test_architecture_counts_are_from_catalog_not_estimated():
 catalog=load()
 overview=compile_architecture(catalog)
 assert sum(x["count"] for x in overview["categories"])==len(catalog["devices"])
 assert len(overview["categories"])==5
 assert "Pillar" in overview["warning"] or "Pillar" in next(x for x in overview["categories"] if x["category"]=="SJ MOSFET")["physics"][0]
def test_readability_heatmap_is_not_performance_ranking():
 from pathlib import Path
 page=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
 assert "제품별 핵심 특성 한눈에 보기" in page
 assert "성능의 좋고 나쁨이 아닌 자료의 확보 상태" in page
 assert "fomStatus" in page
 assert "bench-fom-detail" in page
 assert "Process Architecture · 구조별 기술 지도" in page
