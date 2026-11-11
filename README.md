# PSI Radar — Power Semiconductor Intelligence Radar

한국어 중심의 전력반도체 주간 기술·논문·경쟁사 모니터링 플랫폼. GaN (40%) > SiC (30%) > UD/UG SGT (15%) = SJ MOSFET (15%).

## 구현된 V0.1
- 반응형 정적 대시보드: Overview, Technology, Research, Competitors, Benchmark 및 Market 준비 화면, Data Quality
- Google News RSS 공개 색인에서 주간 뉴스 메타데이터 수집
- Crossref에서 학술지 DOI 및 공개 초록 메타데이터 수집
- 기술 분류/검색/중복 제거/중요도 기초 점수/소스 링크 및 수집 오류 표시
- 매주 월요일 06:00 KST GitHub Actions 수집·테스트·Pages 배포 설계
- 선택적으로 GitHub Actions secret `OPENAI_API_KEY`를 설정하면 **공개 초록이 있는 학술지에만** 제한된 한국어 요약 수행 (API 사용료 발생 가능)

## 웹 배포 설정 (최초 1회)
1. Repository **Settings → Pages → Build and deployment → Source = GitHub Actions**로 설정합니다.
2. Repository **Actions → PSI Radar - Weekly Collect and Deploy → Run workflow**를 실행합니다.
3. 성공 시 **https://minijoaa85-cpu.github.io/psi-radar/** 로 접속합니다. 페이지가 활성화되기 전에는 404가 나올 수 있습니다.
4. **Actions** 탭의 실행 로그로 수집 건수·실패·Pages 배포 상태를 확인합니다.
5. 옵션: **Settings → Secrets and variables → Actions → New repository secret**에서 `OPENAI_API_KEY`를 등록합니다. 키를 파일에 넣거나 대화에 붙여 넣지 마세요.

## 로컬 실행
```bash
python -m pip install -r requirements.txt
pytest -q
python scripts/collect.py
python -m http.server 8000 --directory site
```
http://localhost:8000 접속.

## 데이터 정책과 한계
- 뉴스는 검색 색인과 원문 링크를 제공하며 첫 번째 당사자 공식 발표로 간주하지 않습니다.
- 논문은 제목·DOI·공개 초록으로 검색하므로 연구 결론은 자동 확정하지 않습니다.
- 기업 재무, 기술 비교 벤치마크, 미래 전망은 **아직 수집하지 않습니다.** 관련 메뉴는 데이터가 없음을 명확히 표시합니다.
- 첫 실행 전 `site/data.json`에는 가상 자료 없이 0건이 표시됩니다.
- 출처별 권리·접근 조건을 준수하며 미공개 사내 데이터를 업로드하지 않습니다.
- 공개 GitHub Pages는 URL을 모르는 사람도 접근할 수 있습니다.
- 정기 GitHub Actions 실행은 예약 시간에서 지연될 수 있으며 GitHub 정책에 따라 중단될 수 있습니다.

## 파일
- `site/index.html`: 정적 한국어 웹 UI
- `site/data.json`: 최신 자료
- `scripts/collect.py`: 주간 수집기
- `tests/test_collect.py`: 규칙 검증
- `.github/workflows/weekly.yml`: 예약 및 수동 실행, 테스트, 데이터 저장, GitHub Pages 배포
