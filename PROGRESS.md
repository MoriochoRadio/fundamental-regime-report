# PROGRESS.md

이 문서는 본 프로젝트의 **변하는 상태**를 추적한다.
변하지 않는 사실·규칙·방향은 `CLAUDE.md` 에 있다.

**마지막 갱신**: 2026-05-17 (디렉터리 구조 합의 완료)

---

## 1. 현재 상태 (Current Status)

- **단계**: 0 — 프로젝트 셋업 / 방향 합의 (디렉터리 구조 합의 완료)
- **요약**: 협업 문서·스캐폴딩·GitHub·기술 스택·**디렉터리 구조까지
  합의 완료**. 다음은 *단계별 진행 계획(DoD·예상 소요)* 제안 단계.
  그 후 단계 1(데이터 셋업) 실제 작업 진입.
- **원격**: https://github.com/MoriochoRadio/fundamental-regime-report (Public, MIT)

---

## 2. 완료한 작업 (Done)

- [x] 프로젝트 목적·스코프·작업 방식을 사용자와 합의
- [x] `CLAUDE.md` 초안 작성 (목표·포함/제외·방법론·산출물·협업 규칙)
- [x] `PROGRESS.md` 초안 작성 (본 문서)
- [x] 스캐폴딩: `README.md`, `LICENSE` (MIT), `.gitignore` (Python + data/model + .claude)
- [x] `git init` + 초기 커밋 (`c7c1852`)
- [x] GitHub 레포 생성·원격 연결·초기 푸시 (`origin/main`)
- [x] 기술 스택 1차 합의 (CLAUDE.md §8) — uv, OpenDartReader+pykrx, sklearn+LightGBM+hmmlearn, Gemini Free Tier, Streamlit+plotly
- [x] AI/ML 역할 분리 원칙 명문화 (CLAUDE.md §3.4) — 직접 학습 ML이 주연, LLM은 빌드타임 배치 1회만
- [x] 디렉터리 구조 합의 (CLAUDE.md §8.6) — src layout, 패키지명 `frr`, LLM 단일 출구, app/는 정적 읽기 전용, 점진 생성

---

## 3. 다음 할 일 (Next)

> 모두 사용자 확인을 받은 뒤 진행한다.

1. ~~권장 기술 스택 제안~~ ✅ 완료 (CLAUDE.md §8)
2. ~~디렉터리 구조 제안~~ ✅ 완료 (CLAUDE.md §8.6)
3. **단계별 진행 계획** — 5단계(데이터 → 펀더멘털 → 국면 → 통합 → 마무리)
   각 단계의 산출물·완료 기준(DoD)·예상 소요를 제출. ← **다음**
4. 위 확정 후 → **단계 1 (데이터 셋업)** 착수.

---

## 4. 미해결 이슈 / 결정 대기 (Open Decisions)

각 항목은 결정 즉시 CLAUDE.md의 해당 섹션에 반영된다.

| # | 결정 사항 | 후보 / 비고 | 상태 |
|---|---|---|---|
| D1 | 분석 대상 유니버스 | KOSPI200 / 핵심 수십 개 / 시총 상위 N | 미정 |
| D2 | 부실(라벨) 정의 | 관리종목 지정, 상장폐지, 신용등급 다운그레이드, Altman Z 임계 등 | 미정 |
| D3 | 국면 모델 | HMM(상태 수 K=?), GMM, K-Means, 변경점 탐지 | 미정 |
| D4 | 국면 입력 피처 | 지수 수익률, 변동성, 거래량, 금리/환율 등 매크로 | 미정 |
| D5 | 대시보드 프레임워크 | ~~Streamlit / Dash / Next.js + FastAPI~~ | ✅ **Streamlit + plotly** |
| D6 | LLM 공급자·정책 | ~~Anthropic / OpenAI / 로컬~~ | ✅ **Gemini Free Tier + LLMProvider 추상화 / 빌드타임 배치 1회 / 런타임 0호출** |
| D7 | 재무 데이터 시점 처리 | 공시일 + lag(예: T+1, T+2) — 정확한 lag 값 합의 필요 | 미정 |
| D8 | 평가 지표 | 부실 분류: AUC/PR-AUC/Brier? 국면: 안정성/지속성/사후해석성? | 미정 |
| D9 | 모델 카드/리포트 양식 | 출력 스키마(JSON) → LLM 서술화 파이프라인 | 미정 |

---

## 5. 학습된 규칙·결정 로그 (Decision Log)

> 확정되면 시간 역순으로 누적. 동시에 CLAUDE.md에도 반영한다.

- **2026-05-17** — 디렉터리 구조 합의 (CLAUDE.md §8.6 참조):
  - **src layout** + 패키지명 `frr` (짧고 임포트 깔끔)
  - `src/frr/llm/` 단일 출구 — 다른 모듈은 `LLMProvider` 인터페이스만 본다
  - `app/`(Streamlit)는 LLM SDK import 금지, 정적 JSON만 읽음 — CI 검사 가능
  - 데이터 흐름 단방향 (`raw → interim → processed → reports`)
  - **점진 생성** 정책 채택 — placeholder 미생성, 단계 진입 시 필요 파일만 추가
- **2026-05-17** — 기술 스택 1차 확정 (D5/D6 포함):
  - Python 3.11 + uv (재현성·속도)
  - 데이터: OpenDartReader + pykrx, parquet 저장
  - ML: scikit-learn + LightGBM, 국면: hmmlearn (GMM 비교)
  - **LLM: Gemini Free Tier** + `LLMProvider` 추상화
    - *근거*: 사용자 제약 — Max 유지 보장 없음·서비스 지속 비용 부담 어려움·*완전 무료* 우선
    - *정책*: LLM 호출은 **빌드 타임 배치 1회**만, 결과 JSON 고정.
      **서비스 런타임(대시보드) LLM 호출 0회**. 따라서 배포 시 비용 0원.
    - *원칙*: 직접 학습/개발하는 AI(부실 스코어링 + 국면 분류)가
      포트폴리오의 *주연*, LLM은 *조연* (CLAUDE.md §3.4)
  - 대시보드: Streamlit + plotly (직전 Flask와 다른 색·1인 6~12주에 안전)
  - 산출물 추적: 파일시스템 + git (MLflow 미도입)
  - 품질: pytest + ruff + GitHub Actions (lint+test)
- **2026-05-17** — 저장소 `MoriochoRadio/fundamental-regime-report`,
  Public, MIT 라이선스로 생성. GitHub 형상관리를 진행 기준으로 채택.

---

## 6. 다음 갱신 트리거 (Update Triggers)

다음 중 하나라도 발생하면 본 문서를 갱신한다:

- 한 작업 단위(기능·단계) 완료
- 새로운 결정 확정 (D1~D9 등)
- 미해결 이슈 추가/해소
- 단계 전환 (1→2, 2→3 …)
