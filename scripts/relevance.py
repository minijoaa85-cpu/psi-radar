"""V3.4 explainable metadata relevance, separate from publication provenance.

Scores are retrieval heuristics, NOT paper peer review, scientific verification,
or an estimate of commercial performance. Old archived records retain v1 labels.
"""
from __future__ import annotations
import re

PHYSICS={
 "Dynamic / Switching":("dynamic ron","dynamic r(on)","dynamic on-resistance","switching loss",
  "reverse recovery","qrr","eoss","qgd","gate charge","turn-off","turn-on","softness",
  "short circuit","short-circuit","scwt","eoff","eon","hard switching","dv/dt","di/dt"),
 "Device Structure":("trench","superjunction","super junction","shielded gate","split gate",
  "field stop","field-stop","p-gate","e-mode","cascode","vertical gan","cell pitch","pillar",
  "charge balance","p-channel","junction barrier","jfET","channel mobility"),
 "Process / Materials":("epitax","implant","anneal","passivation","metallization","oxide",
  "wafer","buffer layer","interface trap","dislocation","defect","lifetime control","etch",
  "atomic layer deposition","aln","algan","substrate"),
 "Reliability":("reliability","threshold voltage instability","bias stress","breakdown",
  "htrb","h3trb","avalanche","ruggedness","gate oxide","btdb","tdbd","short circuit",
  "bipolar degradation","current collapse","trapping","threshold shift","bias temperature"),
 "Data Center / Power Conversion":("data center","datacenter","server power","800vdc",
  "power conversion","power supply","inverter","on-board charger","power module")
}
SPURIOUS=("stock price","share price","market forecast","market report","distributor",
 "supplier directory","marketplace","shopping","bibliometric","market size")
DEVICE_MARKERS={
 "GaN":("gan hemt","gan transistor","gallium nitride","gan-on-si","gan power"),
 "SiC":("sic mosfet","silicon carbide","sic diode","sic power"),
 "IGBT":("igbt","insulated gate bipolar transistor"),
 "SJ MOSFET":("superjunction","super junction","sj mosfet"),
 "SGT":("shielded gate","split gate","shield gate","sgt mosfet")
}
LAUNCH_MARKERS=("announces","announced","introduces","launched","launches",
 "new generation","unveils","releases","expands portfolio","mass production",
 "qualification","qualified","adopted","design win","production ready")
MARKET_MARKERS=("revenue","earnings","forecast","market growth","capex","investment",
 "capacity expansion","partnership","merger","acquisition")


def _contains(text: str, term: str) -> bool:
    """Avoid matching SGT, GaN and other short keywords inside unrelated words."""
    if len(term)<=5 and term.replace(" ","").isalnum():
        return bool(re.search(r"(?<!\w)"+re.escape(term)+r"(?!\w)",text))
    return term in text


def relevance(row):
    """Two independent lenses: device physics depth and monitoring/industry signal."""
    title=str(row.get("title") or "").lower()
    abstract=str(row.get("abstract") or "").lower()[:1600]
    full=title+" "+abstract
    topics={name:[term for term in terms if _contains(full,term)]
            for name,terms in PHYSICS.items()}
    matched=[k for k,hits in topics.items() if hits]
    category=row.get("category")
    device=any(_contains(full,term) for term in DEVICE_MARKERS.get(category,()))
    title_device=any(_contains(title,term) for term in DEVICE_MARKERS.get(category,()))
    technical_core=sum(bool(topics[k]) for k in (
        "Dynamic / Switching","Device Structure","Process / Materials","Reliability"))
    context=bool(topics["Data Center / Power Conversion"])
    # Not based on whether the record came from a paper, a news index or a
    # manufacturer: provenance and technical relevance are separate.
    technical_score=(16+int(device)*15+int(title_device)*9+
                     min(40,technical_core*11)+int(context)*6+
                     (6 if abstract.strip() and technical_core else 0))
    penalty=20 if any(term in title for term in SPURIOUS) else 0
    technical_score=max(0,min(100,technical_score-penalty))
    technical_level="높음" if technical_score>=70 else "보통" if technical_score>=45 else "낮음"

    launched=any(term in title for term in LAUNCH_MARKERS)
    market=any(term in title for term in MARKET_MARKERS)
    if launched and device:
        signal="제품·양산 발표 후보"
    elif technical_core and device:
        signal="소자·공정 연구 후보"
    elif market or context:
        signal="시장·시스템 적용 후보"
    else:
        signal="일반 메타데이터"
    # This metric orders monitoring candidates only. It is NOT credibility,
    # nor evidence that the described product/technology achieved its claims.
    monitor_score=max(0,min(100,
        15+(30 if device else 0)+(25 if launched else 0)+(12 if context else 0)+
        (12 if market else 0)+(8 if technical_core else 0)-penalty))
    reasons=matched[:4] or ["제목·초록에서 소자·공정 물리 키워드 부족"]
    if penalty:reasons.append("시장·유통 정보 포함 가능성")
    if row.get("kind")=="paper" and not abstract.strip():reasons.append("초록 미확보 — 제목 기반")
    tier={"official":"제조사 직접 발표(주장, 독립 검증 아님)",
          "paper":"학술 서지 메타데이터(본문 미검증)",
          "news":"뉴스 제목 색인(원문 미검증)"}.get(row.get("kind"),"출처 유형 미확인")
    return {
      "relevance_score":technical_score,"relevance_level":technical_level,
      "technical_relevance_score":technical_score,
      "technical_relevance_level":technical_level,
      "relevance_topics":matched,"relevance_reasons":reasons,
      "relevance_method":"metadata-rule-v2",
      "monitoring_signal":signal,"monitoring_priority_score":monitor_score,
      "monitoring_method":"title-signal-v1",
      "evidence_tier":tier,
    }


def annotate(rows):
    for row in rows:row.update(relevance(row))
    return rows
