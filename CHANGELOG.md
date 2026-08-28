# 저장소 변경 이력

스킬 자체의 변경 이력은 `skills/hwpx/CHANGELOG.md`를 보세요.
이 파일은 **저장소 구조·배포 방식**의 변경만 기록합니다.

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

작성일: 2026-08-16 | 버전: v1.0.0 | 작성: 프랭크 × 에이미 협업
