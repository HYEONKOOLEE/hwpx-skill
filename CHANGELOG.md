# 저장소 변경 이력

스킬 자체의 변경 이력은 `skills/hwpx/CHANGELOG.md`를 보세요.
이 파일은 **저장소 구조·배포 방식**의 변경만 기록합니다.

## v1.4.1 — 2026-09-05

스킬 v1.4.1(검사 6번 판정 정정)을 반영하고, **v1.4.0에서 빠져 있던 배포 파일을 실제로 빌드했다.**

### 배경

v1.4.0 커밋은 `README.md`·`install.sh`·`install.ps1`이 `dist/hwpx-v1.4.0.skill`을 안내하는데
**그 파일을 만들지 않았다.** `.skill` 업로드로 설치하려는 사용자는 없는 파일을 찾게 되고,
`dist/`에는 v1.2.0까지만 있어 마켓플레이스 설치자도 구버전을 받는 상태였다.

### 추가

- **`dist/hwpx-v1.4.1.skill` · `dist/hwpx-v1.4.1.zip`** — 코워크 업로드용 배포 파일.
  20개 항목, 기존 배포본과 동일한 `hwpx/` 최상위 구조. ZIP 무결성·BOM 부재 확인 완료.
  v1.0.0·v1.2.0 배포 파일은 이전 버전 참조용으로 남겨 둔다.
  (v1.4.0 배포 파일은 만들어진 적이 없으므로 건너뛴다.)

### 수정

- **`.claude-plugin/plugin.json` · `marketplace.json`** — `version` 1.4.0 → **1.4.1**.
  `description`에 "양식 없이 사내 규정·매뉴얼·지침서 작성" 추가(v1.4의 C 워크플로 반영),
  `keywords`에 `규정`·`매뉴얼` 추가.
- **`README.md`** — 버전 배지 v1.4.1, dist 파일명·폴더 구성표 갱신.
- **`install.sh` · `install.ps1`** — 안내하는 dist 파일명을 v1.4.1로.
- **`skills/hwpx/README.md`** — **v1.2에서 멈춰 있던 것을 v1.4.1로.** v1.1의 `.hwp` 직접 처리,
  v1.3의 표 병합 주의사항, v1.4의 C 워크플로가 모두 누락돼 있었다. `scripts/` 목록에
  `hwp_bridge.mjs` 보강, "꼭 알아둘 3가지" → 4가지(표 병합 항목 신설), 문제 해결표에
  R5 증상 2행 추가.
- **`skills/hwpx/`** — SKILL.md·CHANGELOG.md·scripts/verify_hwpx.py 교체
  (상세는 스킬 CHANGELOG v1.4.1).

## v1.4.0 — 2026-09-05

hwpx 스킬 v1.4를 반영했다. 핵심은 **새 문서 생성 워크플로(C)** 신설 — 양식 없이 처음부터
만드는 사내 규정·매뉴얼 작업에서 서식 속성이 조용히 전파되어 본문 전체가 가운데 정렬로
나오고, 단락 141개에 쪽나눔이 걸리는 사고가 있었다.

### 배경

`python-hwpx`의 `set_paragraph_format()`은 인자를 생략하면 그 속성을 가진 **기존 `paraPr`를
재사용한다.** `alignment`를 생략하니 앞선 CENTER 단락의 서식이 조·항·호 본문 전체에 붙었고,
`page_break_before`를 생략하니 37쪽 문서가 153쪽이 됐다.

`verify_hwpx.py`도 `@rhwp/core`도 전부 PASS를 줬다. 텍스트·구조 손실이 아니라 **서식 문제**라
무결성 검사의 사각지대다. 사용자가 화면을 보고 나서야 드러났다.

### 수정

- **`skills/hwpx/SKILL.md`** — 0단계 판별표에 **C. 새 문서 생성 워크플로** 신설. 빌더 클래스
  패턴, 표준 문서 구성, 5단계 저장 파이프라인을 문서화했다. 절대 규칙에 **R5~R9** 추가
  (서식 속성 명시 · id 중복 재부여 · 표 배색과 정렬 · A4 세로 지정 · 저장 파이프라인).
  "검사하지 않는 것" 표와 Quick Reference에 정렬·쪽나눔 분포 확인법을 넣었다.
  주의사항 23개 → **28개**. 상세는 스킬 CHANGELOG v1.4.
- **`.claude-plugin/plugin.json` · `marketplace.json`** — `version` 1.3.0 → **1.4.0**.
- **`README.md`** — 버전 배지 v1.4.0, v1.4 변경점 요약, dist 파일명 갱신.
- **`install.sh` · `install.ps1`** — 안내하는 dist 파일명을 v1.4.0으로.

### 추가

- **`dist/hwpx-v1.4.0.skill` · `dist/hwpx-v1.4.0.zip`** — 코워크 업로드용 v1.4 배포 파일.
  이전 버전 배포 파일은 기존 사용자 링크 보존을 위해 남겨 둔다.

### 손대지 않은 것

- `scripts/` 5종 — v1.3 그대로. R5·R7은 **생성 시점의 규칙**이라 저장된 파일을 사후
  검사해서는 잡아낼 수 없다. 규칙과 빌더 패턴으로 막는다.
- `references/` 4종, `assets/` 2종, `evals/` — 무변경.

## v1.3.0 — 2026-09-04

hwpx 스킬 v1.3을 반영했다. 핵심은 **표 구조 무결성 검사** — 서식 문서의 표에서 행을 지운 뒤
세로 병합 범위를 맞추지 않으면 한글이 파일을 열지 못하는데, 기존 검증 도구가 이를 전혀
걸러내지 못했다.

### 배경

실제 작업 중 발생한 사고다. 18행짜리 관공서 서식(전체가 표 하나, 왼쪽 라벨 칸이
`rowSpan=11`로 병합)에서 빈 행 3개를 지우면서 `rowSpan`을 그대로 뒀다. 표는 15행인데
셀은 18행까지 걸쳤다고 주장하는 상태가 되어 한글이 **"파일을 읽거나 저장하는데 오류가
있습니다"** 로 파일 자체를 거부했다.

`verify_hwpx.py`(v1.2)도, `@rhwp/core`의 `contentLoss`·`exportHwpVerify`도 전부 PASS를
줬다. 셋 다 텍스트·쪽수 보존만 검사하기 때문이다.

### 수정

- **`skills/hwpx/scripts/verify_hwpx.py`** — 검사 항목 6개 → **8개**. 5번(표 병합 정합성)과
  6번(단락 id 중복)을 신설했다. 표준 라이브러리 `xml.etree`만 쓰므로 추가 의존성이 없다.
  중첩 표를 오검출하지 않도록 직계 자식 `<hp:tr>`만 센다.
- **`skills/hwpx/SKILL.md`** — 절대 규칙을 3가지 → **4가지**로. R4(표 구조 무결성) 신설,
  트러블슈팅 절 신설, 주의사항 19개 → 23개. 상세는 스킬 CHANGELOG v1.3.
- **`.claude-plugin/plugin.json` · `marketplace.json`** — `version` 1.2.0 → **1.3.0**.
- **`README.md`** — 버전 배지 v1.3.0, v1.3 변경점 요약, dist 파일명 갱신.
- **`install.sh` · `install.ps1`** — 안내하는 dist 파일명을 v1.3.0으로.

### 추가

- **`dist/hwpx-v1.3.0.skill` · `dist/hwpx-v1.3.0.zip`** — 코워크 업로드용 v1.3 배포 파일.
  이전 버전 배포 파일은 기존 사용자 링크 보존을 위해 남겨 둔다.

### 손대지 않은 것

- `references/` 4종, `assets/` 2종, `evals/` — 문서 처리 로직 무변경.
- `scripts/`의 나머지 4종 — 변경 없음.

## v1.2.0 — 2026-09-01

hwpx 스킬 v1.2를 반영했다. 핵심은 **스킬 범위 한정** — 이 저장소 하나로 완결되며,
함께 설치해야 하는 다른 스킬이 없다는 점을 모든 진입점에서 일관되게 밝혔다.

### 배경

v1.1까지 `skills/hwpx/SKILL.md`가 두 곳(YAML frontmatter `description`, 0-A단계 판정표)에서
누름틀 채우기·메일머지 작업을 별도 스킬로 넘기라고 안내했다. frontmatter는 스킬 목록에
색인되는 문장이라 설치 직후 사용자 눈에 띄고, 여기에 의존 패키지 이름 `@rhwp/core`가
겹치면서 **"rhwp 관련 스킬도 추가로 설치해야 하나?"** 하는 오해를 낳았다.
설치 자체에는 영향이 없었으나(루트 README에는 해당 안내가 없었다) 진입 장벽으로 작용했다.

### 수정

- **`.claude-plugin/plugin.json` · `marketplace.json`** — `version` 1.1.0 → **1.2.0**.
  `description`을 "생성·읽기·편집·템플릿 치환 스킬"에서 **"읽고·편집하고·생성해 저장하는
  단독 스킬. 다른 스킬을 함께 설치할 필요가 없다"**로 교체. 마켓플레이스 목록에 그대로
  노출되는 문장이므로 스킬 본체와 문구를 맞췄다.
- **`README.md`** — 제목 문단에 `.hwp` 명시, 버전 배지 v1.2.0, "이 저장소 하나로 완결됩니다"
  한 줄 추가. 의존 패키지 절에 `npm i @rhwp/core`와 **구분 박스**(npm 라이브러리 ↔ 동명의
  별도 CLI·스킬 대조) 삽입. `scripts/` 설명을 4종 → **5종**으로 정정(`hwp_bridge.mjs` 누락분).
- **`install.sh` · `install.ps1`** — 안내하는 dist 파일명을 v1.2.0으로.
- **`skills/hwpx/`** — SKILL.md·README.md·CHANGELOG.md 3종 교체(상세는 스킬 CHANGELOG v1.2).

### 추가

- **`dist/hwpx-v1.2.0.skill` · `dist/hwpx-v1.2.0.zip`** — 코워크 업로드용 v1.2 배포 파일.
  v1.0.0·v1.1.0 배포 파일은 이전 버전 참조용으로 남겨 둔다.

### 손대지 않은 것

- `@rhwp/core` 의존성과 `scripts/hwp_bridge.mjs` — `.hwp` 직접 읽기·저장 기능의 핵심이다.
- `references/` 4종, `scripts/` 5종, `assets/` 2종, `evals/` — 문서 처리 로직 무변경.

## v1.1.0 — 2026-08-29

hwpx 스킬 v1.1을 반영했다. 핵심은 **HWP 입력 게이트** — `.hwp`(HWP5 바이너리)를 그대로
업로드해도 스킬이 자동으로 `.hwpx`로 변환해 처리하고, 작업이 끝나면 올린 형식 그대로
되돌려준다. 한컴오피스가 필요 없다(`@rhwp/core` Rust+WASM 변환기 사용).

### 추가

- **`skills/hwpx/scripts/hwp_bridge.mjs`** — HWP5 ↔ HWPX 양방향 변환기.
  변환 손실 보고(`contentLoss`)와 역변환 쪽수 보존 검증(`exportHwpVerify`)을 함께 낸다.
- **`dist/hwpx-v1.1.0.skill` · `dist/hwpx-v1.1.0.zip`** — 코워크 업로드용 v1.1 배포 파일.

### 수정

- `skills/hwpx/SKILL.md` — 0-A단계(입력 형식 게이트)·산출 형식 규약 추가, v1.1.
  상세 변경은 `skills/hwpx/CHANGELOG.md` 참조.
- `.claude-plugin/marketplace.json` · `plugin.json` — 버전 1.1.0, 설명에 `.hwp` 지원 명시.
- `README.md` · `install.sh` · `install.ps1` — 배포 파일명·버전 표기 갱신.
- v1.0.0 배포 파일(`dist/hwpx-v1.0.0.*`)은 기존 사용자 링크 보존을 위해 유지.

### 새 의존성 (스킬 실행 시)

- Node.js + `npm i @rhwp/core` — `.hwp` 입력을 만났을 때(0-A단계)만 필요.
  `.hwpx`만 다루는 작업은 기존과 동일하게 파이썬만으로 동작한다.

---

## v1.0.0 — 2026-08-16

첫 공개판. hwpx 스킬을 **클로드 코드 · 코워크 · 코덱스** 세 환경에 모두 설치할 수 있도록
저장소를 구성했다.

### 추가

- **`skills/hwpx/`** — 스킬 정본. 모든 설치 경로가 이 한 폴더를 원본으로 삼는다.
- **`.claude-plugin/marketplace.json` · `plugin.json`** — 클로드 코드 플러그인 마켓플레이스.
  `/plugin marketplace add HYEONKOOLEE/hwpx-skill` 로 등록하면
  이후 `/plugin marketplace update` 만으로 최신본을 받을 수 있다.
- **`install.ps1` (Windows) · `install.sh` (macOS·Linux)** — 클로드 코드와 코덱스에
  한 번에 설치하는 스크립트. 대상 선택 인자(`all` / `claude` / `codex`)를 받는다.
  복사만 하고 기존 폴더를 삭제하지 않는다.
- **`dist/hwpx-v1.0.0.skill` · `dist/hwpx-v1.0.0.zip`** — 코워크 업로드용 배포 파일.
  두 파일은 확장자만 다르고 내용은 동일하다.
- **`README.md`** — 설치 방법 4가지(스크립트·플러그인·수동 복사·코워크 업로드),
  설치 확인법, 문제 해결표.

### 설치 경로 근거

| 환경 | 개인 스킬 경로 | 프로젝트 경로 |
|---|---|---|
| 클로드 코드 | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| 코덱스 CLI | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |
| 코워크 | (폴더 없음 — `.skill` 파일 업로드) | 해당 없음 |

세 환경 모두 `SKILL.md` 앞머리에 `name`·`description` 두 필드를 요구하는 동일한 형식을
쓰기 때문에, **폴더 하나를 그대로 복사해 세 곳에서 쓸 수 있다.**

### 확인 사항

- 개인정보(이름·이메일·연락처)·소속 기관명·고객사명 **없음**.
- 모든 텍스트 파일 **UTF-8 BOM 없음**. BOM이 붙으면 YAML 앞머리가 파싱되지 않아
  스킬이 검색되지 않는다.

---

작성일: 2026-08-29 | 버전: v1.1.0 | 작성: 프랭크 × 에이미 협업
