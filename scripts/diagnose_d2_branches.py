"""D2 최종 결정 — 두 갈래 사전 진단.

배경: 두 차례 B1 폐기 후 *KOSPI200 모집단 부적합* 근본 원인 식별.
다음 결정은 *D1 핵심 스코프 경계 영향* 때문에 양성 확보만으로 불가.

갈래 1 (B3 — KOSDAQ 스코프 확장):
- (1a) FDR delisting KOSDAQ 부실 사유 + walk-forward 분포 (즉시 가능)
- (1b) KOSDAQ150 시점별 분기 구성 자동/수동 확보 가능성 검증
- (1c) 단계 2~4 파급 + 1인 일정 추정

갈래 2 (D2 타깃 재정의 — KOSPI200 유지):
- (2a) 대안 타깃 후보 정성 평가 + 가능한 정량 추정
- (2b) 장점·단점·자기참조 위험

데이터 비용: 추가 DART 호출 0 (FDR 캐시 + 기존 corrections.parquet 활용).
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

from frr.data.fdr import FDRDataSource  # noqa: E402


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


fdr_src = FDRDataSource(project_root=PROJECT_ROOT)
delisting = fdr_src.delisting()


# ============================================================
# 갈래 1: B3 (KOSDAQ 스코프 확장)
# ============================================================

section("갈래 1 (B3) — (1a) FDR KOSDAQ 상폐 부실 사유 + walk-forward 분포")

mask_kosdaq_window = (
    (delisting["DelistingDate"] >= pd.Timestamp("2015-01-01"))
    & (delisting["DelistingDate"] <= pd.Timestamp("2024-12-31"))
    & (delisting["Market"] == "KOSDAQ")
    & (delisting["Symbol"].str.len() == 6)  # 6자리 일반 종목만
)
kosdaq_delisted = delisting[mask_kosdaq_window]
print(f"  KOSDAQ 일반(6자리) 상폐 (2015-2024): {len(kosdaq_delisted)} 건")

# 부실 사유 필터 (KOSPI 와 동일 키워드)
distress_kw = ["잠식", "해산", "감사", "부도", "회생", "관리", "감리"]
mask_distress = kosdaq_delisted["Reason"].astype(str).apply(
    lambda r: any(kw in r for kw in distress_kw)
)
kosdaq_distress = kosdaq_delisted[mask_distress]
print(f"  그 중 부실 사유 키워드 매칭: {len(kosdaq_distress)} 건")

# 비부실 사유 분포 (배제 검증)
print("\n  *비부실* 사유 분포 (top 10):")
non_distress = kosdaq_delisted[~mask_distress]
for reason, n in non_distress["Reason"].value_counts().head(10).items():
    print(f"    {n:4d}  {reason}")

# 부실 사유 분포
print("\n  *부실* 사유 분포:")
for reason, n in kosdaq_distress["Reason"].value_counts().items():
    print(f"    {n:4d}  {reason}")

# walk-forward 연도별
print("\n  KOSDAQ 부실 상폐 연도별 분포:")
years_kosdaq = kosdaq_distress["DelistingDate"].dt.year
zero_years = []
for year in range(2015, 2025):
    n = (years_kosdaq == year).sum()
    flag = " <- ZERO" if n == 0 else ""
    print(f"    {year}: {n:3d}{flag}")
    if n == 0:
        zero_years.append(year)
print(f"  → KOSDAQ walk-forward 0 연도: {zero_years if zero_years else '없음'}")


# ---- (1b) KOSDAQ150 시점별 구성 확보 가능성 ------------------------------

section("갈래 1 (B3) — (1b) KOSDAQ150 시점별 분기 구성 확보 가능성")

import FinanceDataReader as fdr  # noqa: E402

print("  ## FDR StockListing 시도:")
for key in ["KOSDAQ150", "KOSDAQ-150", "KS200", "KQ150"]:
    try:
        df = fdr.StockListing(key)
        if df is not None and len(df) > 0:
            print(f"    OK  '{key}': shape={df.shape}")
        else:
            print(f"    EMPTY '{key}'")
    except NotImplementedError:
        print(f"    N/A  '{key}': NotImplementedError")
    except Exception as e:
        print(f"    FAIL '{key}': {type(e).__name__}: {str(e)[:60]}")

print("\n  ## pykrx 인덱스 시점별 구성:")
try:
    from pykrx import stock

    # KOSDAQ150 = 2203 (KRX 표준 인덱스 코드)
    members = stock.get_index_portfolio_deposit_file("20200101", "2203")
    if members is not None and len(members) > 0:
        print(f"    OK  KOSDAQ150(2203) 2020-01-01: {len(members)} 종목")
    else:
        print("    EMPTY KOSDAQ150(2203) 2020-01-01")
except Exception as e:
    print(f"    FAIL KOSDAQ150 시점별: {type(e).__name__}: {str(e)[:80]}")

print("\n  ## KRX 정보데이터시스템 [12006] 결론 (이전 Cowork 확정):")
print("    페이지 DOM 에 일자 입력 요소 부재. 모든 인덱스에 동일 적용.")
print("    → KOSDAQ150 시점별 조회 *수동 다운로드 불가능* (KOSPI200 과 동일 벽).")


# ---- (1c) 단계 2~4 파급 + 1인 일정 (정성) -------------------------------

section("갈래 1 (B3) — (1c) 단계 2~4 파급 + 1인 일정 정직 추정")

print("""  데이터 수집 재작업:
    - KOSDAQ 분기 인덱스 시점별 union 확보 → *현재 시점 구성*만 가능 가정
      (FDR/pykrx/KRX 모두 *과거 시점* 조회 막힘) → KOSPI200 만큼의 정밀한
      point-in-time 보장 *불가능*. 데이터 정합성 저하.
    - DART 호출: 신규 종목 ~수천 (KOSDAQ 전체 1,822) → +호출 시간 ~2시간
    - KRX OHLCV 추가 페치 → +시간

  단계 2 (펀더멘털):
    - KOSPI ↔ KOSDAQ 결제·유동성·규제 상이 → 통합 학습 vs 분리 학습 ablation
    - 추가 일정: +3~5일

  단계 3 (국면):
    - KOSDAQ 지수 통합 또는 별도 국면 — 분리 권장 시 +1~2일

  단계 4 (대시보드):
    - 양 시장 표시·필터·시장별 메타 — +2~3일

  검증·테스트 추가: +2~3일

  ── 합계 (낙관): +1.5~2주
  ── 합계 (분리 ablation 상한): +2.5~3주
  ── 추가 데이터 정합성 위험: KOSDAQ150 시점별 정밀도 KOSPI200 만큼 보장 X.
       (KRX 일자 입력 부재 → point-in-time 정의 *완화* 필요)""")


# ============================================================
# 갈래 2: D2 타깃 재정의 (KOSPI200 유지)
# ============================================================

section("갈래 2 — (2a) 대안 타깃 후보 평가")

print("""  ── 후보 A: 신용등급 N단계 하향 ──────────────────────────
    데이터 자동 확보:
      - DART 공시: '주요사항보고서(채권 신용평가)' 또는 '회사채 신용평가' 류
      - 또는 DART API 자유 검색으로 'NICE신용평가', 'KIS', '한기평' 키워드
      - 평가사 사이트 무료 공개도 일부 있음 (NICE 격주 발표 등)
      - **완전 자동은 어려움** — 텍스트 파싱 + 매칭 필요. 1인 +2~3일
    추정 양성 (KOSPI200 대형주):
      - 연 5~15건 추정 (한국 시장 전체 부정 등급 변동 연 ~50-100건)
      - walk-forward 0 연도 가능성 *낮음*
    자기참조 위험:
      - 신용등급은 *외부 평가* → 우리 입력(재무비율)과 *직접* 같지 않음
      - 신용등급 자체를 입력 피처로 쓰지 않으면 정직
      - 격리: 단계 2 isolation 테스트로 강제
    CLAUDE.md 수정:
      - "부실 위험 스코어링" → "신용 위험 스코어링" 경미 변경
      - 라벨 정의 명확화 ↑

  ── 후보 B: 재무 악화 동반 대형 drawdown ─────────────────
    데이터 자동 확보:
      - pykrx OHLCV (이미 확보) + DART finstate (이미 확보) → **0 추가 호출**
      - 정의: 1년 drawdown > X% AND 영업이익 음수 전환
    추정 양성 (KOSPI200):
      - 대형주에서 빈번 (LG생활건강 2022, 아모레퍼시픽 2020 등)
      - 연 10~30건 추정. 0 연도 없음
    자기참조 위험:
      - drawdown = 주가, 영업이익 = 재무. 모델 입력이 *재무비율*이므로
      - 라벨에 *영업이익*이 들어가면 *약한 자기참조* — 라벨 정의에서
        영업이익을 *추세 변환*으로 처리 시 완화
      - drawdown만으로 라벨 정의하면 자기참조 0 (재무→주가 예측 = 정직)
    CLAUDE.md 수정:
      - "부실" → "재무 동반 가격 충격" 으로 *재정의* (변경 큼)
      - 또는 "재무비율로 예측 가능한 위험"
    한계: "부실"의 본래 의미 — *상폐·관리종목* — 와 멀어짐.

  ── 후보 C: 중대 어닝 쇼크 ────────────────────────────
    데이터 자동 확보:
      - 컨센서스 데이터 (FnGuide, Wisefn) — 유료
      - 무료 출처 거의 없음 → 1인 부담 큼
    → 채택 X (데이터 비용 문제)

  ── 후보 D: 영업이익 음수 전환 ─────────────────────────
    B2 와 동일 — *자기참조*. 폐기 유지.

  ── 후보 E: 자본잠식·부채비율 임계 ────────────────────
    B4 와 동일 — *임의 임계*. 폐기 유지.

  ── 정량 추정 가능한 후보: A (신용등급), B (drawdown 동반)""")


# ---- (2b) 갈래 2 장단점 -------------------------------------------------

section("갈래 2 — (2b) 장점·단점·위험")

print("""  장점:
    - D1 핵심 스코프 경계(KOSPI200 한정) *유지* → 1인 일정 안전
    - 단계 1 데이터 자산 *전부 재사용* (321 종목·40 분기·10,114 보고서)
    - 추가 데이터 수집 부담 *작거나 없음*

  단점:
    - "부실 위험 스코어링" 원래 의미 *변형* (CLAUDE.md 수정 필요)
    - 후보 A: 신용등급 데이터 자동 확보가 *완전하지 않음* (텍스트 파싱 필요)
    - 후보 B: drawdown 라벨 = "부실"이라기보다 *주가 위험*

  자기참조 위험 — 별 검토:
    - 후보 A: 신용등급은 외부 평가 → 우리 입력과 직접 같지 X → 위험 *낮음*
    - 후보 B: 라벨에 *영업이익*이 들어가면 *약한 자기참조* → 정의 정밀화 필요

  포트폴리오 평가 시 영향:
    - "직접 학습 ML이 주연" 원칙 유지 가능 (CLAUDE.md §3.4)
    - 단 *D2 라벨 정의의 변천 과정* 자체를 *포트폴리오 가치*로 활용 가능
      (두 번의 라벨 오염 실패 → 모집단 통찰 → 타깃 재정의)""")


# ============================================================
# 비교표
# ============================================================

section("비교표 — 최종 결정 자료")

print(f"""
  {'항목':<25} {'갈래 1 (B3 KOSDAQ)':<25} {'갈래 2 (타깃 재정의)':<25}
  {'-' * 25} {'-' * 25} {'-' * 25}
  {'양성 확보 (KOSDAQ부실)':<25} {len(kosdaq_distress):<25} {'A: 연 5-15 추정':<25}
  {'walk-forward 0 연도':<25} {str(zero_years if zero_years else 'X')[:24]:<25} {'후보별 차이':<25}
  {'데이터 자동 확보':<25} {'부분 (point-in-time X)':<25} {'A 부분 / B 완전':<25}
  {'1인 추가 일정':<25} {'+1.5-2주 (상한 +3주)':<25} {'A +2-3일 / B +1-2일':<25}
  {'스코프 경계 변경':<25} {'CLAUDE.md §4.1 변경':<25} {'경미~중간':<25}
  {'데이터 정합성':<25} {'KOSDAQ150 시점별 X':<25} {'기존 KOSPI200 유지':<25}
  {'자기참조 위험':<25} {'X':<25} {'A 낮음 / B 약함':<25}
""")
