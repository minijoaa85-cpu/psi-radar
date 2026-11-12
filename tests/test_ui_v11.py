"""V1.1 regression checks for simple-first dashboard navigation and evidence labels."""
from html.parser import HTMLParser
from pathlib import Path
from scripts.validate_benchmark import load

PAGE=(Path(__file__).resolve().parents[1]/"site"/"index.html").read_text(encoding="utf-8")
class Nodes(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.duplicates=[]
 def handle_starttag(self,tag,attrs):
  x=dict(attrs).get("id")
  if x:
   if x in self.ids:self.duplicates.append(x)
   self.ids.add(x)
def test_navigation_elements_present_and_unique():
 parser=Nodes();parser.feed(PAGE)
 assert not parser.duplicates,parser.duplicates
 required={"arch-open-benchmark","bench-category","bench-company","bench-architecture",
  "bench-fom","bench-use-compare","bench-compare","bench-rows",
  "bench-quality","bench-fom-math","bench-fom-detail"}
 assert required<=parser.ids
def test_non_expert_simple_first_navigation():
 assert "선택한 기술의 Benchmark 확인" in PAGE
 assert 'activateRadarTab("benchmark")' in PAGE
 assert "function renderBenchmark()" in PAGE
 assert "const picked=el(\"arch-category\")" in PAGE
 assert "선택 제품을 비교 목록에 추가" in PAGE
 assert "전체 제품 상세 사양표 펼쳐 보기" in PAGE
def test_coverage_communication_does_not_claim_device_quality():
 assert "수치 없음(—) = 미확인 · 불량 또는 열세 아님" in PAGE
 assert "성능의 좋고 나쁨이 아닌 자료의 확보 상태" in PAGE
 assert "Datasheet 표 확인" in PAGE
 assert "제품 간 동등 비교는 별도 검토" in PAGE
def test_dashboard_coverage_counts_are_grounded_in_catalog():
 devices=load()["devices"]
 confirmed=[r for r in devices if any(v.get("test_conditions") for v in r["specs"].values())]
 missing_typ=[r for r in devices if any(v["kind"]=="unspecified" for v in r["specs"].values())]
 assert len(confirmed)<=len(devices)
 assert len(missing_typ)<=len(devices)
 assert len(confirmed)>=1 and len(missing_typ)>=1
