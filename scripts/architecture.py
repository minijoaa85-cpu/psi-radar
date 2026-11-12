"""PSI Radar V1.0 — architecture overview from curated benchmark metadata.
Classification shows stated product structure only; not reverse-engineered silicon process.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"site"/"benchmark.json"
DEST=ROOT/"site"/"architecture.json"
CATS=("GaN","SiC","IGBT","SJ MOSFET","SGT")
OVERVIEW={
 "GaN":{"intro":"E-mode HEMT 및 집적형 GaN 전력 스테이지","physics":["Dynamic RDS(on)","Gate reliability","Qg, Qoss / Eoss","기생 인덕턴스"],"watch":["Gate stack·2DEG 안정성","Buffer 및 Trapping","Package 및 구동 통합"]},
 "SiC":{"intro":"Trench·Planar SiC MOSFET 구조와 전력 손실","physics":["RDS(on) vs Tj","Gate oxide","Short-circuit withstand","Body diode"],"watch":["채널 이동도 / JFET","Oxide 신뢰성","Trench corner 전계"]},
 "IGBT":{"intro":"Field-stop·Trench 셀, 양극성 캐리어 손실 특성","physics":["VCE(sat) vs Eoff","SCWT","Turn-off tail","FRD"],"watch":["Field-stop profile","Lifetime control","Trench cell 설계"]},
 "SJ MOSFET":{"intro":"Superjunction Pillar Charge Balance 및 Body Diode","physics":["P/N pillar balance","BVDSS / Ron","Qrr 및 Softness","EAS"],"watch":["Pillar 농도 경사","Edge termination","Reverse recovery"]},
 "SGT":{"intro":"Shielded Gate Trench / Field Plate 기반 저압 MOSFET","physics":["RDS(on)","Qgd, Qoss","Shield electrode bias","Cell pitch"],"watch":["Gate–shield capacitance","Split gate 구조","저압 디바이스 FOM"]},
}
def structure(row):
 cat=row.get("category");title=str(row.get("structure") or "").lower()
 if row.get("architecture")=="integrated_half_bridge":return "드라이버 통합형"
 if cat=="GaN":return "E-mode HEMT" if "e-mode" in title else "구조 미분류"
 if cat=="SiC":return "Trench SiC MOSFET" if "trench" in title else "Planar SiC MOSFET" if "planar" in title else "SiC MOSFET (구조 미상)"
 if cat=="IGBT":return "Field-stop Trench IGBT" if "field-stop" in title and "trench" in title else "IGBT (구조 미상)"
 if cat=="SGT":return "Shielded Gate Trench" if "shield" in title else "SGT (구조 미상)"
 if cat=="SJ MOSFET":return "Superjunction MOSFET" if "superjunction" in title else "SJ MOSFET (구조 미상)"
 return "미분류"
def compile_architecture(catalog):
 devices=catalog.get("devices",[])
 result=[]
 for cat in CATS:
  matches=[r for r in devices if r.get("category")==cat]
  counts=dict(Counter(structure(r) for r in matches))
  result.append({"category":cat,**OVERVIEW[cat],"count":len(matches),
    "companies":sorted(set(r["company"] for r in matches)),
    "structures":counts,
    "official_sample_ids":[r["id"] for r in matches],
    "official_sources":[{"company":r["company"],"part":r["part"],"url":r["url"],"structure":structure(r)} for r in matches[:15]]})
 return {"schema_version":1,"benchmark_reviewed_on":catalog.get("reviewed_on"),"categories":result,
 "method":"Curated device structure field; no cross-section microscopy or teardown verification",
 "warning":"등록 제품 구성·공식 제조사 표기 기반입니다. 소자 내부 Pillar 농도, 공정 Recipe, 구조 성능 순위, 세대간 수율·면적 개선율은 검증하지 않았습니다."}
def main():
 source=json.loads(SOURCE.read_text(encoding="utf-8"))
 out=compile_architecture(source)
 DEST.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Architecture map:",len(out["categories"]),"categories,",sum(a["count"] for a in out["categories"]),"products")
if __name__=="__main__":main()
