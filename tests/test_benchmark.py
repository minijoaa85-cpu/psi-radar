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

def test_indicative_fom_math_is_not_normalized():
 from scripts.validate_benchmark import illustrative_fom,normalized_fom
 products=load()["devices"]
 gan=next(r for r in products if r["part"]=="IGT65R055D2")
 assert illustrative_fom(gan,"qg")==258.5
 assert normalized_fom(gan,"qg") is None
 assert illustrative_fom(gan,"qgd") is None
def test_integrated_gan_not_discrete_fom():
 from scripts.validate_benchmark import illustrative_fom,strictly_comparable
 rows=load()["devices"]
 integrated=next(r for r in rows if r["part"]=="MASTERGAN6")
 discrete=next(r for r in rows if r["part"]=="IGT65R055D2")
 assert illustrative_fom(integrated,"qg") is None
 assert not strictly_comparable(integrated,discrete,"rds_on")
def test_expanded_parts_come_from_manufacturer_pages():
 rows=load()["devices"]
 assert len(rows)>=12
 assert {"STMicroelectronics","Toshiba","ROHM","Infineon"}<=set(r["company"] for r in rows)
def test_snapshot_change_tracking():
 import datetime as dt
 from scripts.benchmark_history import create_snapshot
 data=load()
 when=dt.datetime(2026,11,12,tzinfo=dt.timezone.utc)
 first=create_snapshot(data,when)
 assert len(first["added_ids"])==len(data["devices"])
 assert not first["changed_ids"]
 same=create_snapshot(data,when,first)
 assert not same["added_ids"] and not same["changed_ids"]
 changed=__import__("copy").deepcopy(data)
 changed["devices"][0]["specs"]["qg"]["value"]+=0.1
 second=create_snapshot(changed,when,first)
 assert second["changed_ids"]==[data["devices"][0]["id"]]
