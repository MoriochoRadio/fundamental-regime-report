# `data/external/kospi200_quarterly/`

분기말 시점의 KOSPI200 구성 종목을 KRX 정보데이터시스템에서 *수동
다운로드* 한 정적 CSV 모음.

- **출처**: <http://data.krx.co.kr> > 통계 > 기본통계 > 지수 >
  주가지수 > [11005] 지수구성종목 (코스피 200)
- **대상 분기**: 2015 Q1 ~ 2024 Q4 (40개)
- **상세 절차·파일명 규칙·해시 계산**: 프로젝트 루트
  [`docs/data_sources.md`](../../../docs/data_sources.md) §3 참조
- **매니페스트**: [`MANIFEST.yaml`](MANIFEST.yaml) — 다운로드한 모든
  파일의 *single source of truth*. 다운로드 후 각 항목을 채운다.

> CSV 본체는 사용자가 단계 1 작업으로 직접 다운로드한 뒤 이 디렉터리에
> 추가한다. 매니페스트의 모든 필드가 채워진 분기만 후속 코드(로더)가
> 사용한다.
