"""Build version-history PDF and editable PPTX from site/version_history.json.

Both downloads and the in-dashboard history share one reviewed JSON source.
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"site"/"version_history.json"
OUT=ROOT/"site"/"docs"
BG="#0B1423"; CARD="#142840"; WHITE="#F0F7FD"; BLUE="#6ABFFF"; MUTED="#B2C9E0"
def rgb(s):return RGBColor.from_string(s[1:])
def page_data(data):
 e=data["entries"]
 p=[("RELEASE HISTORY","PSI Radar","Power Semiconductor Intelligence · 전체 버전 기록",
     [("플랫폼","공개 근거 기반의 기술·경쟁사·제품·재무 인텔리전스"),("기록 범위",e[0]["version"]+" – "+e[-1]["version"]),("업데이트 일자",data["updated_on"])]),
    ("EXECUTIVE SUMMARY","개발 전체 요약","V3.0: 공개 근거 → 기술 분석 → 경쟁사 → 제품 → 재무 연결",
     [("기술·출처","논문·뉴스·제조사 공식 원문 및 근거 수준 분리"),("제품·구조","Benchmark·FOM·Architecture·Device Physics"),("사용자 경험","Briefing·My Watch·탐색형 메뉴"),("재무 근거","공식 IR 4개사·개인 검토·기준본 변경 감시"),("통합 관제","V3.0 Mission Control · 기술군 선택·원문·제품·IR 원클릭 연결")]),
    ("DEVELOPMENT JOURNEY","개발 단계별 흐름","실제 구현 및 README를 기준으로 묶은 버전 영역",
     [("V0.x","공개 자료 수집·관련성·제품 근거"),("V1.0–1.4","구조·물리·논문과 연구 동향"),("V1.5–1.9","Briefing·My Watch 개인 자료 관리"),("V2.0–2.7","재무·공식 IR 감시 및 Overview 시각화"),("V2.8–V3.0","근거 분포·제품 비교·통합 Mission Control")])]
 for x in e:
  p.append((x["version"],x["version"]+"  "+x["title"],x["summary"],
    [("WHY · 개발 배경",x["background"]),("WHAT · 핵심 변경",x["changes"]),("VALUE · 사용자 가치",x["value"])]))
 p.append(("NEXT RELEASE RULE","차기 버전 관리 규칙","Single source of truth: site/version_history.json",
    [("01","새 버전의 한 줄 요약과 배경·개선·가치를 기록"),("02","우측 History 패널이 동일한 기록을 표시"),("03","배포 CI에서 PPTX와 PDF를 함께 재생성"),("04","테스트 및 라이브 배포 확인 후 공개")]))
 return p
def font_file():
 for p in ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf","/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"):
  if Path(p).exists():return p
 raise RuntimeError("Korean font missing; install fonts-nanum")
def ppt_text(sl,s,x,y,w,h,size=16,color=WHITE,bold=False):
 t=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame
 t.clear();t.word_wrap=True
 t.margin_left=t.margin_right=t.margin_top=t.margin_bottom=Pt(0)
 for i,line in enumerate(str(s).split("\n")):
  pp=t.paragraphs[0] if not i else t.add_paragraph()
  pp.text=line;pp.font.name="NanumGothic";pp.font.size=Pt(size);pp.font.bold=bold;pp.font.color.rgb=rgb(color)
def ppt(pages,path):
 prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
 for i,(tag,title,sub,blocks) in enumerate(pages):
  sl=prs.slides.add_slide(prs.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=rgb(BG)
  ppt_text(sl,"PSI RADAR / "+tag,.68,.38,11,.3,12,BLUE,True)
  ppt_text(sl,title,.68,.98,11.9,.76,30,WHITE,True)
  ppt_text(sl,sub,.68,1.85,11.8,.7,17,MUTED)
  step=1.08 if len(blocks)<=3 else .77;start=2.8
  for j,(label,value) in enumerate(blocks):
   y=start+j*step
   shape=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(.68),Inches(y),Inches(11.95),Inches(step-.1))
   shape.fill.solid();shape.fill.fore_color.rgb=rgb(CARD);shape.line.color.rgb=rgb("#355777")
   ppt_text(sl,label,.95,y+.13,3.0,.4,15,BLUE,True)
   ppt_text(sl,value,3.7,y+.11,8.55,step-.18,16 if step>1 else 14,WHITE)
  ppt_text(sl,f"Github README + implementation records  |  {i+1:02d} / {len(pages):02d}",.68,7.02,12,.27,10,MUTED)
 prs.save(path)
def pdf(pages,path):
 pdfmetrics.registerFont(TTFont("Nanum",font_file()))
 c=canvas.Canvas(str(path),pagesize=(960,540));c.setTitle("PSI Radar Version History")
 def words(s,maxw,size):
  lines=[];line=""
  for word in str(s).split(" "):
   probe=(line+" "+word).strip()
   if pdfmetrics.stringWidth(probe,"Nanum",size)>maxw and line:lines.append(line);line=word
   else:line=probe
  if line:lines.append(line)
  return lines
 def write(s,x,y,size,color,maxw=850,maxlines=3):
  c.setFillColor(HexColor(color));c.setFont("Nanum",size)
  for j,line in enumerate(words(s,maxw,size)[:maxlines]):c.drawString(x,540-y-j*(size*1.45),line)
 for i,(tag,title,sub,blocks) in enumerate(pages):
  c.setFillColor(HexColor(BG));c.rect(0,0,960,540,fill=1,stroke=0)
  c.setFillColor(HexColor(BLUE));c.rect(0,533,960,7,fill=1,stroke=0)
  write("PSI RADAR / "+tag,47,36,10,BLUE);write(title,47,89,27,WHITE,850,2)
  write(sub,48,139,14,MUTED)
  step=78 if len(blocks)<=3 else 56
  for j,(label,value) in enumerate(blocks):
   top=201+j*step
   c.setFillColor(HexColor(CARD));c.roundRect(47,540-top-(step-9),866,step-9,9,stroke=0,fill=1)
   write(label,65,top+16,12,BLUE,205,2)
   write(value,264,top+15,14 if step>60 else 12,WHITE,619,3)
  write(f"Github README + implementation records    {i+1:02d} / {len(pages):02d}",47,510,9,MUTED)
  c.showPage()
 c.save()
def main():
 d=json.loads(SRC.read_text(encoding="utf8"));e=d["entries"]
 assert d["latest_version"]==e[-1]["version"]
 assert len({r["version"] for r in e})==len(e)
 OUT.mkdir(parents=True,exist_ok=True);pages=page_data(d)
 ppt(pages,OUT/"psi-radar-version-history.pptx")
 pdf(pages,OUT/"psi-radar-version-history.pdf")
 print(f"Built {len(pages)} release history slides in PPTX and PDF")
if __name__=="__main__":main()
