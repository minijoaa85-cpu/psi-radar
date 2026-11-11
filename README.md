# PSI Radar V0.2 — Power Semiconductor Intelligence Radar

공개 자료 기반 한국어 전력반도체 주간 기술 모니터링 웹 플랫폼. GaN (40%) > SiC (30%) > IGBT (10%) = UD/UG SGT (10%) = SJ MOSFET (10%).

**Web:** https://minijoaa85-cpu.github.io/psi-radar/  
**Workflow:** https://github.com/minijoaa85-cpu/psi-radar/actions/workflows/weekly.yml

## 기능

- GaN·SiC·IGBT·SGT·SJ MOSFET 뉴스와 학술지 DOI 메타데이터 수집 및 원문/DOI 연결
- 뉴스 최근 8일, 학술지 최근 45일 검색 / 관련 없는 GAN·SiC 소재 논문 최소화
- 한국어 제목 및 기술 해설(선택적 OpenAI API)
- 뉴스는 **제목 기반 요약**(사실 확정 금지), 학술지 논문은 **공개 초록 기반 요약**(원문 검증 전 표시)
- 중요도·기술별 필터, 한국어·원문 제목 검색, Device Physics 참고 내용 접기/펼치기
- 중복 자료 캐시 재사용 / AI 비용 및 API 오류 모니터링
- 기업 재무 및 제품 Datasheet 비교 기능은 후속 개발이며 현재 데이터가 없음을 표기

## OpenAI API 연결 — 소유자가 최초 1회 설정

1. https://platform.openai.com/ 에서 API 계정/프로젝트를 확인하고 **새 API 키를 발급**합니다. ChatGPT Plus 요금과는 별개입니다.
2. OpenAI Platform 프로젝트의 **Usage / Limits 및 Budget** 설정에서 월별 비용 예산과 알림을 설정하세요. 로컬 추정 한도는 계정 전체 청구 상한이 아닙니다.
3. GitHub **Settings → Secrets and variables → Actions → New repository secret**에 아래 이름으로 API 키를 등록합니다.
   - Name: `OPENAI_API_KEY`
   - Secret: 발급한 키 값 (**대화창, GitHub 코드, README, 이슈에 붙여 넣지 마세요**)
4. GitHub Actions → `PSI Radar - Weekly Collect and Deploy` → **Run workflow**를 실행합니다.
5. 배포 후 대시보드 **Data Quality** 탭에서 AI 호출 횟수·캐시·추정 비용을 확인합니다.

**API 키 없이도 정상 작동합니다.** 공개 뉴스와 서지 정보를 수집하고 웹 화면을 배포합니다. AI 요약은 API 키가 연결된 뒤 정기/수동 실행에서만 활성화됩니다.

## 비용 최소화 기본값 (실행별 제한)

| 항목 | 기본값 |
|---|---|
| 모델 | `gpt-4.1-mini` |
| 1회 수집 실행 AI 요청 상한 | 12회 |
| 입력 토큰 로컬 추정 예산 | 12,000 |
| 출력 토큰 로컬 예산 | 3,600 |
| 1회 실행 추정 비용 상한 | US$0.02 |
| API 1회 출력 제한 | 최대 280 tokens |
| 동일 자료 중복 과금 | 이전 데이터에 저장된 번역 재사용 |
| 코드 Push 실행 | AI 호출 상한 0, 번역 API 사용하지 않음 |

`0.02 USD`는 **추정 비용 제한**으로 API 서버가 계산하는 최종 청구액에 대한 법적·기술적 보증이 아닙니다. API 오류·토큰 계산 차이·워크플로 재실행 횟수·다른 API 사용량 등은 별개입니다. **프로젝트 차원의 예산·알림도 반드시 설정**하세요.

`scripts/ai_enrich.py`가 모델별 가격 허용 목록을 유지합니다. 모델을 바꾸기 전 공식 가격을 확인하고 목록을 수정해야 합니다.

## 실행 및 검증

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/collect.py
python scripts/ai_enrich.py
python -m http.server 8000 --directory site
```
http://localhost:8000 에 접속합니다.

GitHub Pages는 저장소 Settings → Pages → **Source: GitHub Actions**를 사용합니다.
정기 실행은 월요일 06:00 KST를 목표로 하지만 GitHub Actions 예약 실행은 지연되거나 정책에 따라 중단될 수 있습니다.

## 데이터 정책

- Google News RSS는 **뉴스 색인**이며 제조사 공식 발표와 동등한 출처가 아닙니다.
- Crossref 메타데이터의 학술지 분류는 완전한 논문 검색을 보장하지 않습니다.
- AI 번역/해설은 **검토 전**입니다. 공정 조건·실험값·회사 실적·제품 성능 수치를 외부 자료 없이 창작하지 않습니다.
- 제품 스펙 및 재무 분석은 아직 구현되지 않았습니다. 원문 링크는 계속 제공됩니다.
- OpenAI API로 보내는 내용은 **공개 뉴스 제목과 공개 학술 초록/메타데이터**에 한정됩니다. 사내 기밀과 고객 데이터를 입력하지 마세요.
- GitHub Pages는 공개 링크이며 URL을 모르는 사람도 접근할 수 있습니다.

## 소스
- `site/index.html` 한국어 대시보드
- `site/data.json` 최신 수집 데이터
- `scripts/collect.py` 데이터 수집 + 캐시 복원
- `scripts/ai_enrich.py` 사용량 통제·AI 번역·초록 요약
- `tests/` 자동 테스트
- `.github/workflows/weekly.yml` 주간 스케줄·테스트·배포

## 주간 업데이트 및 운영 기간 (2026-11-11 기준)
- 일정: `cron: 0 21 * * 0` — 한국시간 **매주 월요일 06:00**, UTC 일요일 21:00. 실행이 늦어지거나 건너뛰어질 수 있습니다.
- 다음 정기 예정일: **2026년 11월 16일(월) 06:00 KST**. 자동 종료일은 설정되어 있지 않습니다.
- GitHub 공개 저장소에서 **60일 동안 저장소 활동이 없으면** GitHub가 scheduled workflow를 비활성화할 수 있습니다. 자동 수집이 계속 성공하면서 커밋되는지 정기 확인하고, 중단 시 Actions에서 다시 활성화하세요.
- GitHub Pages는 마지막 배포를 보여 주므로 자동 수집이 끊겨도 사이트가 정상처럼 보일 수 있습니다. 항상 데이터 갱신 일자를 확인하세요.
- **현재는 site/data.json을 최신 수집 결과로 덮어써서 표시**하며, 과거 주차별 누적 보고서를 별도로 보관하지 않습니다. 장기 누적 히스토리 기능은 후속 단계입니다.
- API 키, 결제 크레딧, GitHub 계정과 Actions, GitHub Pages, 외부 출처 서비스 상태에 따라 실제 업데이트가 중단될 수 있습니다.

### API 비용 산정
2026-11-11 #19 실측 `3,356 input / 1,322 output tokens`, 12회 API 호출, 추정 `$0.003458`/회(주 1회). 같은 사용량 52회 = 약 `$0.18/년`; 매회 로컬 추정 상한 `$0.02`에 도달하면 52회 = `$1.04/년`. 이는 정기 52회 가정의 **추정치**이며 수동 재실행, 서비스 확장, 실제 API 청구 차이 등은 별도입니다. 50달러 충전액은 주간으로 정해진 기간만큼 소진되는 구독료가 아니며, 향후 모델 가격·사용량·선불 구매 크레딧은 구매일로부터 1년 후 만료됩니다(OpenAI 공식 도움말 기준). 자동 충전이 기본적으로 활성화될 수 있으므로 필요하지 않다면 끄고, 별도의 API 사용 한도와 경고를 설정하세요.

## IGBT 수집 품질 점검 (2026-11-11)
- IGBT는 뉴스 검색·Crossref 논문 검색·대시보드 카테고리에 추가됨.
- 기존 데이터에는 IGBT 0건이었음: 카테고리 추가와 실제 자료 확보는 별개.
- 뉴스 검색어를 IGBT Power Semiconductor, Power Module, Trench, RC-IGBT, Field-Stop로 확장함.
- 최근 7일간 IGBT 관련 뉴스가 없으면 최근 30일 검색을 추가로 수행하고, **최근 30일 참고**로 별도 표기함.
- GitHub Actions의 코드 변경(push) 실행은 비용 방지 및 경합 회피를 위해 데이터 JSON을 저장하지 않으므로, **최신 IGBT 건수 확인 시 Actions → Run workflow를 수동 1회 실행**해야 함. 주간 예약 실행도 저장함.
- Crossref 논문 45일 수집은 아직 커버리지가 제한되어 있으며 학술지 검색 고도화는 별도 과제.
