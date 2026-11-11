"""Explainable process-architecture relevance heuristics. Metadata-based, not paper peer review."""
from __future__ import annotations
import re

PHYSICS={
 "Dynamic / Switching": ("dynamic ron","dynamic r(on)","switching loss","reverse recovery","qrr","eoss","qgd","gate charge","turn-off","turn-on","softness","short circuit","short-circuit","scwt","eoff","eon"),
 "Device Structure": ("trench","superjunction","super junction","shielded gate","split gate","field stop","field-stop","p-gate","e-mode","cascode","vertical gan","cell pitch","pillar","charge balance"),
 "Process / Materials": ("epitax","implant","anneal","passivation","metallization","oxide","wafer","buffer layer","interface traps","dislocation","defects","lifetime control"),
 "Reliability": ("reliability","threshold voltage instability","bias stress","breakdown","htrb","h3trb","avalanche","ruggedness","gate oxide","btdb","tdbd","short circuit"),
 "Data Center / Power Conversion": ("data center","datacenter","server power","800vdc","power conversion","power supply","inverter","on-board charger","power module")
}
SPURIOUS=("stock price","share price","market forecast","market report","distributor","supplier directory","marketplace","shopping","review of literature","bibliometric","survey of","market size")
def relevance(row):
 """Returns relevance_score and interpretable category labels; all are deterministic estimates."""
 title=str(row.get("title") or "").lower()
 abstract=str(row.get("abstract") or "").lower()
 full=title+" "+abstract[:1600]
 hit={k:[w for w in words if w in full] for k,words in PHYSICS.items()}
 matched=[k for k,hits in hit.items() if hits]
 evidence=bool(abstract.strip())
 doi=bool(row.get("doi"))
 # Applies across device categories equally. Separates engineering relevance from editorial priority.
 points=18+min(38,len(matched)*10)+min(14,sum(bool(v) for v in hit.values())*3)
 points+=12 if evidence else 0
 points+=8 if doi else 0
 points+=6 if row.get("kind")=="paper" else 0
 penalty=25 if any(term in title for term in SPURIOUS) else 0
 score=max(0,min(100,points-penalty))
 status="높음" if score>=70 else "보통" if score>=45 else "낮음"
 reasons=matched[:4] or ["제목·초록에서 공정/소자 물리 키워드 부족"]
 if not evidence and row.get("kind")=="paper":reasons.append("초록 없음: 제목만으로 평가")
 if penalty:reasons.append("비기술/시장성 콘텐츠 가능성")
 return {"relevance_score":score,"relevance_level":status,"relevance_topics":matched,"relevance_reasons":reasons,"relevance_method":"metadata-rule-v1"}
def annotate(rows):
 for row in rows:row.update(relevance(row))
 return rows
