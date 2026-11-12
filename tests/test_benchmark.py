from scripts.validate_benchmark import load,validate,strictly_comparable

def test_curated_catalog_has_device_specific_metric_provenance():
 data=load()
 assert not validate(data)
 products=data["devices"]
 assert len(products)>=7
 assert {"GaN","SiC","IGBT","SJ MOSFET"}.issubset({r["category"] for r in products})
 assert all(r["source_type"]=="manufacturer_product_page" for r in products)
def test_igbt_saturation_not_compared_with_mosfet_on_resistance():
 products=load()["devices"]
 a=next(r for r in products if r["category"]=="IGBT")
 b=next(r for r in products if r["category"]=="GaN")
 assert not strictly_comparable(a,b,"vce_sat")
 assert not strictly_comparable(a,b,"rds_on")
def test_missing_measurement_conditions_block_fom():
 products=load()["devices"]
 a,b=[r for r in products if r["category"]=="GaN"][:2]
 assert not strictly_comparable(a,b,"rds_on")
 assert not strictly_comparable(a,b,"qg")
def test_sgt_paper_is_not_fabricated_product():
 data=load()
 assert not [r for r in data["devices"] if r["category"]=="SGT"]
 assert any(r["category"]=="SGT" and "not_product_datasheet" in r["type"] for r in data["research_references"])
def test_invalid_source_and_spec_are_rejected():
 import copy
 data=copy.deepcopy(load())
 data["devices"][0]["url"]="https://example.net/fake"
 data["devices"][0]["specs"]["qg"]["kind"]="unknown"
 errors=validate(data)
 assert len(errors)>=2
