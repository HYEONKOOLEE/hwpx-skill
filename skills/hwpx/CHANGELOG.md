# 변경 이력

## v1.1 — 2026-08-29 (HWP 입력 게이트)

`.hwp`(HWP5 바이너리)를 그대로 업로드해도 이 스킬이 동작하도록 앞뒤에 변환 게이트를 붙였다.
사용자가 한글에서 "hwpx로 다시 저장"하는 수작업이 없어진다.

### 추가

- **0-A단계: 입력 형식 게이트** — 업로드가 `.hwp`면 `@rhwp/core`(Rust+WASM, 한컴오피스 불필요)로
  `.hwpx`로 변환한 뒤 기존 A/B 절차를 그대로 탄다. `.hml`도 같은 경로.
- **`scripts/hwp_bridge.mjs`** — `to-hwpx` / `to-hwp` 양방향 변환기.
  `contentLoss` 손실 보고(항목 있으면 종료코드 3)와 `exportHwpVerify` 쪽수 보존 검증을 함께 낸다.
- **산출 형식 규약** — 사용자가 올린 확장자로 되돌린다. `.hwp` 입력이면 마지막에 `to-hwp`로
  역변환하고 `pageCountBefore == pageCountAfter` · `recovered: true`를 확인한 뒤 전달.
- 누름틀 서식에 값만 채우는 작업은 변환하지 말고 `rhwp-form-fill` 스킬로 넘기라는 분기 규칙.

### 수정

- frontmatter `description`에 `.hwp` 트리거·rhwp-form-fill 분기 명시.
- 주의사항 15번(“레거시 .hwp는 별도 도구 필요”)을 0-A단계 참조로 교체, 16·17번 신설.
- Quick Reference에 변환·역변환 2행 추가.

### 검증 (2026-08-29 실측)

`assets/form2.hwp`(3쪽, 이미지 참조 17건) 기준 전체 파이프라인 통과 —
변환 무손실(`count: 0`) → ZIP 치환 → `clear_layout_cache` → `verify_hwpx.py` PASS(글자 수 295→295)
→ 역변환 `recovered: true`(3쪽 유지). 렌더 비교에서 레이아웃 동일.

## v1.0 — 2026-08-16 (배포판)

원본 스킬(최종 수정 2026-07-29)을 **제3자 배포용으로 정리**한 첫 공개판.
문서 처리 로직·서식 규격·스크립트는 **원본과 동일**하며, 아래 항목만 손봤다.

### 수정

- **작업 파일 경로 일반화** — `SKILL.md` 1건, `references/report-style.md` 6건의
  `/home/claude/...` 하드코딩 경로를 현재 작업 폴더 기준 `./...` 로 변경.
  기존에는 예시 코드를 그대로 실행하면 특정 환경 밖에서 경로 오류가 났다.

- **템플릿 경로를 변수 방식으로** — `report-style.md`의
  `TEMPLATE = "/mnt/skills/user/hwpx/assets/report-template.hwpx"` 를
  `SKILL_DIR` 변수 + f-string 조합으로 변경. 스킬 설치 위치가 환경마다 다르므로
  (`~/.claude/skills/hwpx`, `/mnt/skills/user/hwpx` 등) 한 곳만 고치면 되도록 했다.
  `SKILL.md`는 이미 이 방식이라 표기를 맞춘 것이다.

### 추가

- **`README.md`** — 설치법(.skill / 폴더 복사), 의존 패키지, 트리거 문구,
  폴더 구성, 자주 겪는 문제 4가지, 동봉 양식 안내.
- **`CHANGELOG.md`** — 이 파일. 이전에는 버전·수정일을 확인할 방법이 없었다.
- **`SKILL.md` 버전 배지** — 본문 상단에 버전·최종 수정일·참고 파일 안내 3줄 추가.
  YAML frontmatter는 손대지 않았다(스킬 인식에 영향을 주지 않도록).

### 확인 사항

- 개인정보(이름·이메일·연락처)·소속 기관명·고객사명 **없음**. 배포 전 전수 스캔 완료.
- `assets/`의 두 양식은 자리표시자로만 채워진 일반 공공기관 서식 샘플.
  `form2.hwp` 차례에 남은 `유네스코 한국위원회 사업지원` 예시 문구는 README에 명시.
- `SKILL.md` 선두 **UTF-8 BOM 없음**. BOM이 붙으면 YAML frontmatter가 통째로
  파싱되지 않아 스킬 설명과 트리거 문구가 색인되지 않는다.
  Windows PowerShell의 `Out-File` / `>` 는 BOM을 붙이므로 편집 시 주의.

### 손대지 않은 것

- 문서 생성·편집 절차, 서식 규격(보고서·공문서), XML 내부 구조 문서
- `scripts/` 4종 전체
- `evals/evals.json`

---

## v0 — 2026-07-29 (원본)

- HWPX 생성·읽기·편집·템플릿 치환. 작업 유형 A(생성/템플릿 치환)와
  B(기존 문서 편집) 분기, 유형 무관 절대 규칙 3가지(레이아웃 캐시·재압축·검증),
  참고 문서 4종, 스크립트 4종, 양식 2종.

---

작성일: 2026-08-16 | 버전: v1.0 | 작성: 프랭크 × 에이미 협업
