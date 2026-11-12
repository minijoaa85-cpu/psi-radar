"""Maintained registry of verified manufacturer-owned article URLs and publicly documented facts.
These are curated reference records, not newly scraped weekly press releases.
Never infer a release from the existence of a company portal.
"""
from __future__ import annotations
import datetime as dt
import hashlib
from urllib.parse import urlparse

SOURCES=[
 {"company":"st","date":"2026-05-26","title":"STMicroelectronics announces new 700V PowerGaN HEMTs for AI servers and robotics","title_ko":"ST, AI 서버·로봇용 700V PowerGaN HEMT 제품군 발표","devices":["GaN"],"category":"GaN",
  "url":"https://newsroom.st.com/media-center/press-item.html/n4776.html",
  "summary_ko":"ST 공식 발표: 700V E-mode GaN HEMT 7종, 제품별 RDS(on) typ. 53~270mΩ 및 6~29A급 정격을 공개. 패키지와 측정 조건에 따라 비교해야 합니다.",
  "physics_ko":"고주파 전력 변환에서는 Qg×RDS(on), 스위칭 손실과 게이트 루프 기생 인덕턴스를 함께 평가해야 합니다."},
 {"company":"st","date":"2026-06-26","title":"STMicroelectronics and the infrastructure of Cloud AI","title_ko":"ST, AI 데이터센터 전력망에서 SiC·GaN 및 800VDC 기술 활용 소개","devices":["GaN","SiC"],"category":"GaN",
  "url":"https://newsroom.st.com/media-center/press-item.html/f0022.html",
  "summary_ko":"ST 공식 기술 소개: AI 데이터센터의 800VDC 전력 아키텍처와 SiC·GaN 등 전력반도체 적용 방향을 설명합니다.",
  "physics_ko":"소자 전압 정격과 시스템 배전 전압은 동일하지 않으므로 회로 토폴로지 및 변환 단계별 구분이 필요합니다."},
 {"company":"rohm","date":"2026-08-25","title":"ROHM Introduces 650V IGBTs Achieving Low Loss Characteristics","title_ko":"ROHM, 4세대 650V IGBT 출시 및 단락 내량 특성 발표","devices":["IGBT"],"category":"IGBT",
  "url":"https://www.rohm.com/news-detail?defaultGroupId=false&news-title=2026-08-25_news_igbt",
  "summary_ko":"ROHM 공식 발표: 4세대 650V IGBT에서 일부 제품의 VCE(sat) typ. 1.55V 및 Tj=25°C에서 7µs 단락 내량을 공개했습니다. 제품별 사양은 원본 표를 확인해야 합니다.",
  "physics_ko":"VCE(sat) 저감과 단락 내량의 상충 관계는 캐리어 축적, 구조·공정·Termination 설계와 연결됩니다."},
 {"company":"rohm","date":"2026-04-21","title":"ROHM Develops 5th Generation SiC MOSFETs","title_ko":"ROHM, 5세대 SiC MOSFET 개발·고온 온저항 개선 발표","devices":["SiC"],"category":"SiC",
  "url":"https://www.rohm.com/news-detail?defaultGroupId=false&news-title=2026-04-21_news_sic-mosfet",
  "summary_ko":"ROHM 공식 발표: 동일 내압·칩 크기 기준으로 Tj=175°C에서 4세대 대비 온저항 약 30% 감소를 주장합니다. 독립 실측은 아닙니다.",
  "physics_ko":"셀 구조·채널 및 JFET 저항, Drift 저항의 온도 의존성을 함께 평가해야 합니다."},
 {"company":"rohm","date":"2026-07-09","title":"ROHM Launches 600V Super Junction MOSFETs in Surface-Mount Packages","title_ko":"ROHM, 방열 성능을 강조한 600V SJ MOSFET 제품군 출시","devices":["SJ MOSFET"],"category":"SJ MOSFET",
  "url":"https://www.rohm.com/news-detail?defaultGroupId=false&news-title=2026-07-09_news_super-junction-mosfet",
  "summary_ko":"ROHM 공식 발표: 600V Super Junction MOSFET 신제품과 표면실장 패키징·열 성능을 소개했습니다.",
  "physics_ko":"SJ Pillar Charge Balance와 RDS(on), 열저항 및 패키지 기생 성분을 구분하여 비교해야 합니다."},
 {"company":"rohm","date":"2026-06-03","title":"ROHM SiC MOSFET Adopted in BBU for AI Servers","title_ko":"ROHM, AI 서버 BBU에 750V SiC MOSFET 채택 발표","devices":["SiC"],"category":"SiC",
  "url":"https://www.rohm.com/news-detail?defaultGroupId=false&news-title=2026-06-03_news_sic-mosfet",
  "summary_ko":"ROHM 공식 발표: AI 서버 백업 배터리 장치에 750V SiC MOSFET SCT4013DLL 채택을 발표했으며 800VDC 시스템 응용을 설명합니다.",
  "physics_ko":"실제 Device VDS 정격은 시스템 버스 전압과 같지 않으며 회로 내 소자 전압 스트레스를 기준으로 평가합니다."},
 {"company":"innoscience","date":"2026-10-28","title":"Innoscience Advances AI Infrastructure Power as Part of the NVIDIA MGX Ecosystem","title_ko":"Innoscience, NVIDIA MGX 생태계 관련 AI 서버·800VDC GaN 전원 솔루션 발표","devices":["GaN"],"category":"GaN",
  "url":"https://www.innoscience.com/news/press-releases/18684",
  "summary_ko":"Innoscience 공식 발표: OCP 행사에서 AI 서버와 800VDC 전력 아키텍처를 위한 GaN 응용 솔루션을 소개했습니다.",
  "physics_ko":"E-mode GaN의 Dynamic Ron, Gate Reliability, 고주파 스위칭 성능을 실제 회로 조건에서 비교할 필요가 있습니다."},
]
PORTALS={
 "st":{"title":"ST 공식 기술 뉴스","url":"https://newsroom.st.com/all-news/product-technology"},
 "rohm":{"title":"ROHM 공식 뉴스·제품 자료","url":"https://www.rohm.com/"},
 "innoscience":{"title":"Innoscience 공식 보도자료","url":"https://www.innoscience.com/news/press-releases"},
 "basicsemi":{"title":"BASiC Semiconductor 공식 뉴스·제품","url":"https://www.basicsemi.com/"},
}
def build_official_records(today=None):
 from scripts.competitors import COMPANIES
 from scripts.collect import classify_topics,score
 today=today or dt.datetime.now(dt.timezone.utc).date()
 out=[]
 for item in SOURCES:
  date=dt.date.fromisoformat(item["date"])
  if date>today:continue
  key=item["company"]
  host=(urlparse(item["url"]).hostname or "").lower()
  allowed=COMPANIES[key]["domains"]
  if not any(host==d or host.endswith("."+d) for d in allowed):continue
  title=item["title"]
  id="official-"+hashlib.sha1(item["url"].encode()).hexdigest()[:16]
  out.append({"id":id,"kind":"official","category":item["category"],
   "title":title,"title_ko":item["title_ko"],"summary_ko":item["summary_ko"],
   "physics_ko":item["physics_ko"],"date":date.isoformat(),
   "url":item["url"],"source":COMPANIES[key]["name"]+" Newsroom",
   "summary_status":"제조사 원문에 근거한 한국어 핵심 정보 (독립 검증 아님)",
   "source_type":"manufacturer_official","company_attribution":"publisher_official",
   "company_source_status":{key:"official_verified_url"},"companies":[key],
   "device_mentions":item["devices"],"topics":classify_topics(title),
   "score":score(title,item["category"]),"lookback_days":365,
   "evidence":"Verified official manufacturer article URL","metadata_provider":"curated_official_registry"})
 return out
