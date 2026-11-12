"""V1.2 technology-to-evidence index built from public metadata, NOT claims of causality.
Only title keyword hits qualify as topic candidates; a product spec is a reference, never proof.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"site"/"data.json"
CATALOG=ROOT/"site"/"benchmark.json"
DEST=ROOT/"site"/"topic_map.json"
CATEGORIES=("GaN","SiC","IGBT","SGT","SJ MOSFET")
TOPICS=[
 {"id":"gan-dynamic-ron","category":"GaN","name":"Dynamic RDS(on)","simple":"스위칭 후 온저항이 변하는 현상","why":"트랩·버퍼 영향으로 도통 손실이 달라질 수 있습니다. 제품의 정적 Ron 값만으로 판단하지 않습니다.","terms":["dynamic ron","dynamic r(on)","dynamic rds","current collapse","frequency dispersion","동적 온저항","주파수 분산"],"metrics":["rds_on","qoss"]},
 {"id":"gan-gate","category":"GaN","name":"Gate Reliability","simple":"게이트 구동과 장기 안정성","why":"Threshold 변화와 게이트 누설은 사용 조건에 따라 달라질 수 있습니다.","terms":["gate reliability","gate leakage","gate breakdown","threshold instability","gate stress","게이트 신뢰성"],"metrics":["vth"]},
 {"id":"gan-switching","category":"GaN","name":"Qg · Qoss · Eoss","simple":"스위칭과 출력 용량 관련 특성","why":"동작 전압·구동 조건이 달라지면 비교 결과도 달라집니다.","terms":["gate charge","output capacitance","switching loss","qoss","eoss","qgd","스위칭 손실"],"metrics":["qg","qgd","qoss","eoss"]},
 {"id":"sic-trench","category":"SiC","name":"Trench / Planar","simple":"SiC 셀 구조 변화","why":"채널·JFET·Trench 전계의 균형이 중요합니다.","terms":["trench mosfet","planar mosfet","trench sic","sic trench","트렌치"],"metrics":["rds_on"]},
 {"id":"sic-oxide","category":"SiC","name":"Gate Oxide Reliability","simple":"SiC 게이트 산화막의 내구성","why":"산화막 전계와 온도·구동 조건에 따른 신뢰성을 함께 확인해야 합니다.","terms":["gate oxide","oxide reliability","bias temperature instability","bt i","threshold voltage instability","산화막 신뢰성"],"metrics":["vth"]},
 {"id":"sic-short","category":"SiC","name":"Short Circuit · Body Diode","simple":"단락 내량과 다이오드 동작","why":"단락 시험조건·바디다이오드 전류·열 조건이 비교의 핵심입니다.","terms":["short-circuit withstand","short circuit","body diode","short-circuit","scwt","단락 내량"],"metrics":["tsc","qrr"]},
 {"id":"igbt-loss","category":"IGBT","name":"VCE(sat) · Eoff","simple":"도통 손실과 Turn-off 손실의 균형","why":"VCE(sat), Eoff는 IC·Tj·VGE·게이트 저항에 따라 달라집니다.","terms":["vce(sat)","vcesat","eoff","turn-off loss","turn off loss","conduction loss","도통 손실"],"metrics":["vce_sat"]},
 {"id":"igbt-field","category":"IGBT","name":"Field-stop / Trench","simple":"셀 및 Field-stop 구조","why":"공식 구조 표기와 실제 전기적 특성은 구분하여 읽어야 합니다.","terms":["field stop","field-stop","trench igbt","트렌치 igbt"],"metrics":["vce_sat"]},
 {"id":"igbt-short","category":"IGBT","name":"SCWT · Ruggedness","simple":"단락·파괴 내량","why":"제조사별 단락 내량 수치는 VDC·Tj·구동 조건이 맞아야 합니다.","terms":["short circuit","short-circuit","scwt","ruggedness","단락 내량"],"metrics":["tsc"]},
 {"id":"sgt-shield","category":"SGT","name":"Shield Gate / Field Plate","simple":"Shield 전극과 게이트 분리","why":"Cell Pitch와 게이트-드레인 결합 성분이 동적 특성에 영향을 줍니다.","terms":["shielded gate","shield gate","split gate","field plate","field-plate","차폐 게이트"],"metrics":["rds_on","qgd"]},
 {"id":"sgt-charge","category":"SGT","name":"Qgd · Qoss","simple":"게이트·출력 전하","why":"저압 MOSFET의 구동 손실과 스위칭 손실을 함께 살펴봅니다.","terms":["qgd","qoss","gate charge","output charge","gate-drain capacitance"],"metrics":["qgd","qoss"]},
 {"id":"sj-pillar","category":"SJ MOSFET","name":"Pillar Charge Balance","simple":"P/N 필라 전하 균형","why":"P/N 농도 불균형은 BVDSS 및 Ron 트레이드오프와 연관됩니다.","terms":["charge balance","charge imbalance","pillar","superjunction","super junction","필라"],"metrics":["rds_on","rds_on_max"]},
 {"id":"sj-recovery","category":"SJ MOSFET","name":"Qrr · Softness","simple":"바디다이오드 역회복","why":"Qrr 수치 외에 전류·dI/dt·Tj·복구 파형의 부드러움을 확인해야 합니다.","terms":["reverse recovery","qrr","softness","body diode","역회복"],"metrics":["qrr"]},
 {"id":"sj-breakdown","category":"SJ MOSFET","name":"Breakdown · Edge","simple":"항복 전압과 종단 구조","why":"Wafer Edge와 Pillar Charge Balance의 내압 경향은 구분해 검토합니다.","terms":["breakdown voltage","bv dss","bvdss","edge termination","avalanche","항복 전압"],"metrics":["rds_on_max"]},
]
def hit_title(text,term):
 text=(text or "").casefold()
 pattern=r"(?<![a-z0-9])"+re.escape(term.casefold()).replace(r"\ ",r"\s+")+r"(?![a-z0-9])"
 return bool(re.search(pattern,text))
def news_matches(row,topic):
 if row.get("category")!=topic["category"]:return False
 title=str(row.get("title") or "")+" "+str(row.get("title_ko") or "")
 return any(hit_title(title,word) for word in topic["terms"])
def safe_url(url):
 parsed=urlparse(url or "")
 return parsed.scheme=="https" and bool(parsed.hostname)
def evidence_kind(row):
 if row.get("source_type")=="manufacturer_official" and row.get("kind")=="official":return "manufacturer_announcement"
 if row.get("kind")=="paper":return "paper_metadata"
 return "news_title_candidate"
def build_map(records,catalog):
 mapped=[]
 for topic in TOPICS:
  articles=[r for r in records if news_matches(r,topic) and safe_url(r.get("url"))]
  articles.sort(key=lambda r:(r.get("kind")=="official",r.get("date") or "",r.get("relevance_score") or 0),reverse=True)
  links=[];seen=set()
  for row in articles:
   key=row.get("url")
   if key in seen:continue
   seen.add(key)
   links.append({"id":str(row.get("id") or ""),"title":str(row.get("title_ko") or row.get("title") or "")[:220],
                 "date":row.get("date") or "","kind":evidence_kind(row),
                 "publisher":str(row.get("source") or "")[:100],"url":key,
                 "confidence":"title_keyword_match","matched_terms":[term for term in topic["terms"] if hit_title(str(row.get("title") or "")+" "+str(row.get("title_ko") or ""),term)][:3]})
   if len(links)>=10:break
  products=[p for p in catalog.get("devices",[]) if p.get("category")==topic["category"] and safe_url(p.get("url"))]
  # Prefer product pages that actually expose the metric; never assert research-to-product causal proof.
  products.sort(key=lambda p:(sum(k in p.get("specs",{}) for k in topic["metrics"]),p.get("part") or ""),reverse=True)
  refs=[{"id":p["id"],"part":p["part"],"company":p["company"],"url":p["url"],
         "metrics_available":[k for k in topic["metrics"] if k in p.get("specs",{})],
         "relationship":"same_technology_reference_only"} for p in products[:8]]
  mapped.append({k:topic[k] for k in ("id","category","name","simple","why")}|{"article_candidates":links,"products":refs})
 return {"schema_version":1,"source_generated_at":None,"benchmark_reviewed_on":catalog.get("reviewed_on"),
         "topics":mapped,"method":"Category-constrained literal title keyword match; products are same-technology references only.",
         "warning":"기사·논문은 제목 기반 후보입니다. 논문의 실험 결과 또는 제조사 제품과의 인과관계를 검증하지 않았습니다. 결과가 0건이면 수집범위에서 관련 제목을 찾지 못한 것입니다."}
def main():
 records=json.loads(REPORT.read_text(encoding="utf-8"))
 catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
 out=build_map(records.get("records",[]),catalog)
 out["source_generated_at"]=records.get("generated_at")
 DEST.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Topic map:",len(out["topics"]),"topics,",sum(len(x["article_candidates"]) for x in out["topics"]),"title matches")
if __name__=="__main__":main()
